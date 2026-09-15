"""
Alumni Data Analyzer
Analyzes alumni data to identify networking opportunities, filter by criteria, and generate insights
"""

import csv
import sys
from collections import Counter
from typing import List, Dict, Optional
from datetime import datetime


def load_alumni_data(input_file: str) -> List[Dict]:
    """
    Load alumni data from CSV file.
    
    Args:
        input_file: Input CSV file path
        
    Returns:
        List of alumni records as dictionaries
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)


def calculate_years_of_experience(grad_year: Optional[str]) -> Optional[int]:
    """
    Calculate years of experience from graduation year.
    
    Args:
        grad_year: Graduation year as string
        
    Returns:
        Years of experience or None if grad_year is invalid
    """
    if not grad_year or not grad_year.strip():
        return None
    
    try:
        # Handle cases like "2011 / 2012"
        year_str = grad_year.split('/')[0].strip()
        year = int(year_str)
        current_year = datetime.now().year
        return current_year - year
    except (ValueError, AttributeError):
        return None


def categorize_experience_level(years_exp: Optional[int]) -> Optional[str]:
    """
    Categorize experience level based on years of experience.
    
    Args:
        years_exp: Years of experience
        
    Returns:
        Experience level category
    """
    if years_exp is None:
        return None
    elif years_exp <= 2:
        return "Recent Grad (0-2 years)"
    elif years_exp <= 5:
        return "Early Career (3-5 years)"
    elif years_exp <= 10:
        return "Mid-Career (6-10 years)"
    else:
        return "Senior (11+ years)"


def normalize_major(major: str) -> str:
    """
    Normalize major names for better grouping.
    
    Args:
        major: Major name
        
    Returns:
        Normalized major name
    """
    if not major:
        return "Unknown"
    
    major_lower = major.lower()
    
    # Computer Science variants
    if any(x in major_lower for x in ['computer science', 'cs', 'eecs', 'electrical engineering and computer science']):
        return "Computer Science / Software Engineering"
    
    # Mechanical Engineering
    if 'mechanical engineering' in major_lower or 'meche' in major_lower:
        return "Mechanical Engineering"
    
    # Bioengineering
    if 'bioengineering' in major_lower or 'bioe' in major_lower:
        return "Bioengineering"
    
    # Chemical Engineering
    if 'chemical engineering' in major_lower or 'cheme' in major_lower:
        return "Chemical Engineering"
    
    # IEOR
    if 'ieor' in major_lower or 'industrial engineering' in major_lower or 'operations research' in major_lower:
        return "IEOR / Operations Research"
    
    # Civil Engineering
    if 'civil engineering' in major_lower:
        return "Civil Engineering"
    
    # Data Science
    if 'data science' in major_lower:
        return "Data Science"
    
    # Cognitive Science
    if 'cognitive science' in major_lower:
        return "Cognitive Science"
    
    return major  # Return original if no normalization matches


def analyze_alumni_data(alumni_data: List[Dict]) -> Dict:
    """
    Analyze alumni data and generate statistics.
    
    Args:
        alumni_data: List of alumni records
        
    Returns:
        Dictionary containing analysis results
    """
    total_alumni = len(alumni_data)
    
    # Major analysis
    majors = [normalize_major(alumni.get('Major', '')) for alumni in alumni_data]
    major_counts = Counter(majors)
    
    # Graduation year analysis
    grad_years = [alumni.get('Grad_Year', '') for alumni in alumni_data if alumni.get('Grad_Year')]
    grad_year_counts = Counter(grad_years)
    
    # Experience level analysis
    experience_levels = []
    years_of_exp_list = []
    for alumni in alumni_data:
        years_exp = calculate_years_of_experience(alumni.get('Grad_Year'))
        if years_exp is not None:
            years_of_exp_list.append(years_exp)
            exp_level = categorize_experience_level(years_exp)
            if exp_level:
                experience_levels.append(exp_level)
    
    exp_level_counts = Counter(experience_levels)
    
    # LinkedIn presence
    linkedin_count = sum(1 for alumni in alumni_data if alumni.get('LinkedIn_URL'))
    
    # Email presence
    email_count = sum(1 for alumni in alumni_data if alumni.get('Email'))
    
    # Company presence
    company_count = sum(1 for alumni in alumni_data if alumni.get('Current_Company'))
    
    return {
        'total_alumni': total_alumni,
        'major_distribution': major_counts,
        'graduation_year_distribution': grad_year_counts,
        'experience_level_distribution': exp_level_counts,
        'years_of_experience_stats': {
            'min': min(years_of_exp_list) if years_of_exp_list else None,
            'max': max(years_of_exp_list) if years_of_exp_list else None,
            'avg': sum(years_of_exp_list) / len(years_of_exp_list) if years_of_exp_list else None
        },
        'linkedin_count': linkedin_count,
        'email_count': email_count,
        'company_count': company_count
    }


def filter_alumni(alumni_data: List[Dict], major: Optional[str] = None,
                  grad_year_min: Optional[int] = None, grad_year_max: Optional[int] = None,
                  years_exp_min: Optional[int] = None, years_exp_max: Optional[int] = None,
                  experience_level: Optional[str] = None, has_linkedin: Optional[bool] = None,
                  has_email: Optional[bool] = None) -> List[Dict]:
    """
    Filter alumni data based on various criteria.
    
    Args:
        alumni_data: List of alumni records
        major: Filter by major (supports partial matches)
        grad_year_min: Minimum graduation year
        grad_year_max: Maximum graduation year
        years_exp_min: Minimum years of experience
        years_exp_max: Maximum years of experience
        experience_level: Filter by experience level category
        has_linkedin: Filter by LinkedIn presence (True/False)
        has_email: Filter by email presence (True/False)
        
    Returns:
        Filtered list of alumni records
    """
    filtered = alumni_data.copy()
    
    # Filter by major
    if major:
        major_lower = major.lower()
        filtered = [a for a in filtered if major_lower in normalize_major(a.get('Major', '')).lower()]
    
    # Filter by graduation year range
    if grad_year_min is not None or grad_year_max is not None:
        def in_year_range(alumni):
            grad_year = alumni.get('Grad_Year', '')
            if not grad_year:
                return False
            try:
                year_str = grad_year.split('/')[0].strip()
                year = int(year_str)
                if grad_year_min is not None and year < grad_year_min:
                    return False
                if grad_year_max is not None and year > grad_year_max:
                    return False
                return True
            except (ValueError, AttributeError):
                return False
        filtered = [a for a in filtered if in_year_range(a)]
    
    # Filter by years of experience
    if years_exp_min is not None or years_exp_max is not None:
        def in_exp_range(alumni):
            years_exp = calculate_years_of_experience(alumni.get('Grad_Year'))
            if years_exp is None:
                return False
            if years_exp_min is not None and years_exp < years_exp_min:
                return False
            if years_exp_max is not None and years_exp > years_exp_max:
                return False
            return True
        filtered = [a for a in filtered if in_exp_range(a)]
    
    # Filter by experience level
    if experience_level:
        filtered = [a for a in filtered 
                   if categorize_experience_level(calculate_years_of_experience(a.get('Grad_Year'))) == experience_level]
    
    # Filter by LinkedIn presence
    if has_linkedin is not None:
        filtered = [a for a in filtered if (a.get('LinkedIn_URL') is not None) == has_linkedin]
    
    # Filter by email presence
    if has_email is not None:
        filtered = [a for a in filtered if (a.get('Email') is not None) == has_email]
    
    return filtered


def print_analysis_report(analysis: Dict) -> None:
    """
    Print analysis report to console.
    
    Args:
        analysis: Analysis results dictionary
    """
    print("=" * 70)
    print("ALUMNI DATA ANALYSIS REPORT")
    print("=" * 70)
    print(f"\nTotal Alumni: {analysis['total_alumni']}")
    
    print("\n" + "-" * 70)
    print("MAJOR DISTRIBUTION (Top 15)")
    print("-" * 70)
    for major, count in analysis['major_distribution'].most_common(15):
        percentage = (count / analysis['total_alumni']) * 100
        print(f"  {major:50s} {count:4d} ({percentage:5.1f}%)")
    
    print("\n" + "-" * 70)
    print("GRADUATION YEAR DISTRIBUTION")
    print("-" * 70)
    sorted_years = sorted(analysis['graduation_year_distribution'].items(), key=lambda x: x[0])
    for year, count in sorted_years:
        percentage = (count / analysis['total_alumni']) * 100
        print(f"  {year:10s} {count:4d} ({percentage:5.1f}%)")
    
    print("\n" + "-" * 70)
    print("EXPERIENCE LEVEL DISTRIBUTION")
    print("-" * 70)
    for level, count in analysis['experience_level_distribution'].most_common():
        percentage = (count / analysis['total_alumni']) * 100
        print(f"  {level:30s} {count:4d} ({percentage:5.1f}%)")
    
    if analysis['years_of_experience_stats']['min'] is not None:
        print("\n" + "-" * 70)
        print("YEARS OF EXPERIENCE STATISTICS")
        print("-" * 70)
        stats = analysis['years_of_experience_stats']
        print(f"  Minimum: {stats['min']} years")
        print(f"  Maximum: {stats['max']} years")
        print(f"  Average: {stats['avg']:.1f} years")
    
    print("\n" + "-" * 70)
    print("CONTACT INFORMATION AVAILABILITY")
    print("-" * 70)
    print(f"  LinkedIn URLs: {analysis['linkedin_count']} ({analysis['linkedin_count']/analysis['total_alumni']*100:.1f}%)")
    print(f"  Email Addresses: {analysis['email_count']} ({analysis['email_count']/analysis['total_alumni']*100:.1f}%)")
    print(f"  Company Information: {analysis['company_count']} ({analysis['company_count']/analysis['total_alumni']*100:.1f}%)")
    print("=" * 70)


def export_filtered_results(alumni_data: List[Dict], output_file: str) -> None:
    """
    Export filtered alumni data to CSV.
    
    Args:
        alumni_data: List of alumni records to export
        output_file: Output CSV file path
    """
    if not alumni_data:
        print("No alumni data to export.")
        return
    
    fieldnames = list(alumni_data[0].keys())
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(alumni_data)
        
        print(f"\nFiltered results exported to: {output_file}")
        print(f"Total records: {len(alumni_data)}")
    except Exception as e:
        print(f"Error exporting data: {e}")
        sys.exit(1)


def main():
    """
    Main function for command-line interface.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze and filter alumni data')
    parser.add_argument('--input', default='alumni_data.csv', help='Input CSV file')
    parser.add_argument('--output', default=None, help='Output CSV file for filtered results')
    parser.add_argument('--analyze', action='store_true', help='Run analysis and print report')
    parser.add_argument('--major', help='Filter by major (supports partial matches)')
    parser.add_argument('--grad-year-min', type=int, help='Minimum graduation year')
    parser.add_argument('--grad-year-max', type=int, help='Maximum graduation year')
    parser.add_argument('--years-exp-min', type=int, help='Minimum years of experience')
    parser.add_argument('--years-exp-max', type=int, help='Maximum years of experience')
    parser.add_argument('--experience-level', 
                       choices=['Recent Grad (0-2 years)', 'Early Career (3-5 years)', 
                               'Mid-Career (6-10 years)', 'Senior (11+ years)'],
                       help='Filter by experience level')
    parser.add_argument('--has-linkedin', action='store_true', help='Filter for alumni with LinkedIn URLs')
    parser.add_argument('--has-email', action='store_true', help='Filter for alumni with email addresses')
    
    args = parser.parse_args()
    
    # Load data
    alumni_data = load_alumni_data(args.input)
    print(f"Loaded {len(alumni_data)} alumni records from {args.input}")
    
    # Run analysis if requested
    if args.analyze or not any([args.major, args.grad_year_min, args.grad_year_max, 
                                args.years_exp_min, args.years_exp_max, args.experience_level,
                                args.has_linkedin, args.has_email, args.output]):
        analysis = analyze_alumni_data(alumni_data)
        print_analysis_report(analysis)
    
    # Filter data if filters are specified
    filtered_data = alumni_data
    if any([args.major, args.grad_year_min, args.grad_year_max, 
            args.years_exp_min, args.years_exp_max, args.experience_level,
            args.has_linkedin, args.has_email]):
        filtered_data = filter_alumni(
            alumni_data,
            major=args.major,
            grad_year_min=args.grad_year_min,
            grad_year_max=args.grad_year_max,
            years_exp_min=args.years_exp_min,
            years_exp_max=args.years_exp_max,
            experience_level=args.experience_level,
            has_linkedin=args.has_linkedin if args.has_linkedin else None,
            has_email=args.has_email if args.has_email else None
        )
        
        print(f"\nFiltered to {len(filtered_data)} alumni records")
        
        if args.output:
            export_filtered_results(filtered_data, args.output)
        elif len(filtered_data) < len(alumni_data):
            # Show sample of filtered results
            print("\nSample of filtered results (first 10):")
            for i, alumni in enumerate(filtered_data[:10], 1):
                print(f"  {i}. {alumni.get('Name', 'Unknown')} - {alumni.get('Major', 'Unknown')} ({alumni.get('Grad_Year', 'Unknown')})")


if __name__ == '__main__':
    main()



