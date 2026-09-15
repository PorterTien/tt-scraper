"""
Split alumni CSV by major into separate files
Groups CS/DS/EECS together, others separately
"""

import csv
import sys
import re
from collections import defaultdict
from typing import Dict, List


def normalize_major(major: str) -> str:
    """
    Normalize major names to handle variations.
    Groups CS, DS, EECS together, and consolidates similar major names.
    """
    if not major:
        return "Other"
    
    major_lower = major.lower().strip()
    
    # EECS variations (check BEFORE Computer Science to catch "Electrical Engineering and Computer Science")
    eecs_keywords = ['eecs', 'electrical engineering and computer science', 
                     'electrical engineer and computer science',
                     'electrical engineering & computer science']
    if any(keyword in major_lower for keyword in eecs_keywords):
        return "EECS"
    
    # BioEECS -> EECS (hybrid)
    if 'bioeecs' in major_lower:
        return "EECS"
    
    # Computer Science variations (must contain "computer science" or "cs" as standalone)
    if 'computer science' in major_lower:
        return "Computer Science"
    if major_lower in ['cs', 'cs & business'] or major_lower.startswith('cs,') or major_lower.startswith('cs '):
        return "Computer Science"
    
    # Data Science variations
    if 'data science' in major_lower or major_lower == 'ds':
        return "Data Science"
    
    # Mechanical Engineering variations (consolidate all variants)
    mech_keywords = ['mechanical engineering', 'mechanical engineer', 'meche', 'mech e']
    if any(keyword in major_lower for keyword in mech_keywords):
        return "Mechanical Engineering"
    
    # Bioengineering variations (consolidate bioe, bioengineering, bio e, etc.)
    if 'bioengineering' in major_lower or major_lower in ['bioe', 'bio e']:
        if 'eecs' not in major_lower:  # Exclude BioEECS which goes to EECS
            return "Bioengineering"
    
    # Chemical Engineering variations (consolidate all chemical engineering variants)
    if 'chemical engineering' in major_lower or 'chemical engineer' in major_lower:
        return "Chemical Engineering"
    if 'chemical and biomolecular engineering' in major_lower:
        return "Chemical Engineering"
    
    # IEOR variations (consolidate all operations research/industrial engineering variants)
    ieor_keywords = ['ieor', 'industrial engineering', 'operations research']
    if any(keyword in major_lower for keyword in ieor_keywords):
        return "IEOR"
    
    # Civil Engineering variations (consolidate civil & energy engineering)
    if 'civil engineering' in major_lower:
        return "Civil Engineering"
    if 'civil & energy engineering' in major_lower:
        return "Civil Engineering"  # Or could go to Energy Engineering, but Civil is more specific
    
    # Energy Engineering variations (consolidate energye, energy engineering)
    # But exclude "Civil & Energy Engineering" which goes to Civil Engineering
    if 'energy engineering' in major_lower and 'civil' not in major_lower:
        return "Energy Engineering"
    if major_lower == 'energye':
        return "Energy Engineering"
    
    # Applied Math/Mathematics variations (consolidate all math variants)
    # Check for math-related majors that aren't CS or EECS
    if 'mathematics' in major_lower and 'computer science' not in major_lower and 'electrical' not in major_lower:
        return "Applied Mathematics"
    if 'applied math' in major_lower or 'applied mathematics' in major_lower:
        return "Applied Mathematics"
    
    # Cognitive Science
    if 'cognitive science' in major_lower:
        return "Cognitive Science"
    
    # Nuclear Engineering
    if 'nuclear engineering' in major_lower:
        return "Nuclear Engineering"
    
    # Environmental Engineering variations (consolidate all env eng variants)
    if 'environmental engineering' in major_lower:
        return "Environmental Engineering"
    
    # Materials Science variations
    if 'materials science' in major_lower:
        return "Materials Science & Engineering"
    
    # Biology variations (consolidate biology, integrative biology)
    if 'biology' in major_lower and 'bioengineering' not in major_lower and 'bioe' not in major_lower:
        return "Biology"
    
    # Everything else goes to "Other"
    return "Other"


def group_majors(normalized_major: str) -> str:
    """
    Group majors into categories for file naming.
    CS/DS/EECS go together, others get their own files.
    """
    tech_majors = ["Computer Science", "Data Science", "EECS"]
    
    if normalized_major in tech_majors:
        return "CS_DS_EECS"
    
    # Return normalized major name (sanitized for filename)
    # Replace special characters and spaces
    filename = normalized_major.replace('/', '_').replace('&', 'and').replace(',', '')
    filename = re.sub(r'\s+', '_', filename)
    return filename


def split_alumni_by_major(input_file: str, output_dir: str = ".", min_alumni_per_file: int = 5):
    """
    Split alumni CSV by major into separate files.
    Small majors (fewer than min_alumni_per_file) are grouped into "Other".
    
    Args:
        input_file: Input CSV file
        output_dir: Output directory for split files
        min_alumni_per_file: Minimum number of alumni required for a separate file (default: 5)
    """
    import os
    
    # Create output directory if it doesn't exist
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Load all alumni data
    alumni_by_group = defaultdict(list)
    all_alumni = []
    fieldnames = None
    
    print(f"Loading alumni data from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        if not fieldnames:
            print("Error: Could not read CSV fieldnames")
            sys.exit(1)
        
        for row in reader:
            all_alumni.append(row)
            major = row.get('Major', '').strip()
            normalized_major = normalize_major(major)
            group = group_majors(normalized_major)
            
            # Store both normalized major and original for reference
            row['Normalized_Major'] = normalized_major
            alumni_by_group[group].append(row)
    
    print(f"Loaded {len(all_alumni)} alumni records")
    print(f"Found {len(alumni_by_group)} major groups (before consolidation)")
    
    # Consolidate small groups into "Other"
    consolidated_groups = {}
    other_alumni = []
    
    for group, alumni_list in alumni_by_group.items():
        # Always keep CS_DS_EECS as separate (even if small)
        if group == "CS_DS_EECS":
            consolidated_groups[group] = alumni_list
        # Keep groups with enough alumni as separate
        elif len(alumni_list) >= min_alumni_per_file:
            consolidated_groups[group] = alumni_list
        # Group small ones into "Other"
        else:
            other_alumni.extend(alumni_list)
    
    # Add "Other" group if there are any small majors
    if other_alumni:
        consolidated_groups["Other"] = other_alumni
    
    print(f"Consolidated to {len(consolidated_groups)} major groups (min {min_alumni_per_file} alumni per file)")
    
    # Print summary
    print("\nMajor groups:")
    print("=" * 70)
    for group, alumni_list in sorted(consolidated_groups.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"{group:30s} : {len(alumni_list):3d} alumni")
    
    # Save each group to separate CSV file
    print("\nSaving split files...")
    print("=" * 70)
    
    for group, alumni_list in sorted(consolidated_groups.items(), key=lambda x: len(x[1]), reverse=True):
        # Create filename
        if group == "CS_DS_EECS":
            filename = "alumni_cs_ds_eecs.csv"
        else:
            filename = f"alumni_{group.lower()}.csv"
        
        output_path = os.path.join(output_dir, filename) if output_dir else filename
        
        # Remove Normalized_Major column before saving (it was just for grouping)
        output_fieldnames = [f for f in fieldnames if f != 'Normalized_Major']
        for alumni in alumni_list:
            if 'Normalized_Major' in alumni:
                del alumni['Normalized_Major']
        
        # Save to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=output_fieldnames)
            writer.writeheader()
            writer.writerows(alumni_list)
        
        print(f"✓ Saved {len(alumni_list):3d} alumni to {filename}")
    
    print("\n" + "=" * 70)
    print("Split complete!")
    print(f"Created {len(consolidated_groups)} CSV files in {output_dir or 'current directory'}")
    
    if other_alumni:
        print(f"\nNote: {len(other_alumni)} alumni from small majors were grouped into 'Other'")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Split alumni CSV by major')
    parser.add_argument('--input', default='alumni_data_enriched.csv',
                       help='Input CSV file (default: alumni_data_enriched.csv)')
    parser.add_argument('--output-dir', default='.',
                       help='Output directory for split files (default: current directory)')
    parser.add_argument('--min-alumni', type=int, default=5,
                       help='Minimum number of alumni required for a separate file (default: 5, smaller majors go to "Other")')
    
    args = parser.parse_args()
    
    split_alumni_by_major(args.input, args.output_dir, args.min_alumni)


if __name__ == '__main__':
    main()

