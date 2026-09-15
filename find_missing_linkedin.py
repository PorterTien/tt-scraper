"""
Find Missing LinkedIn Profiles
Helps identify and prioritize alumni who need LinkedIn profile lookup
"""

import csv
import sys
from typing import List, Dict


def load_alumni_data(input_file: str) -> List[Dict]:
    """Load alumni data from CSV."""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)


def analyze_missing_linkedin(alumni_data: List[Dict]) -> Dict:
    """Analyze which alumni are missing LinkedIn profiles."""
    has_linkedin = []
    missing_linkedin = []
    
    for alumni in alumni_data:
        if alumni.get('LinkedIn_URL') and alumni.get('LinkedIn_URL').strip():
            has_linkedin.append(alumni)
        else:
            missing_linkedin.append(alumni)
    
    return {
        'has_linkedin': has_linkedin,
        'missing_linkedin': missing_linkedin,
        'total': len(alumni_data),
        'found_count': len(has_linkedin),
        'missing_count': len(missing_linkedin)
    }


def export_missing_linkedin(alumni_data: List[Dict], output_file: str):
    """Export alumni missing LinkedIn profiles to a separate CSV."""
    missing = [a for a in alumni_data if not a.get('LinkedIn_URL') or not a.get('LinkedIn_URL').strip()]
    
    if not missing:
        print("All alumni have LinkedIn profiles!")
        return
    
    # Get all fieldnames from the data
    fieldnames = list(alumni_data[0].keys())
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(missing)
        
        print(f"Exported {len(missing)} alumni missing LinkedIn to: {output_file}")
    except Exception as e:
        print(f"Error exporting data: {e}")
        sys.exit(1)


def print_prioritization_suggestions(missing: List[Dict]):
    """Print suggestions for prioritizing LinkedIn searches."""
    print("\n" + "=" * 70)
    print("PRIORITIZATION SUGGESTIONS")
    print("=" * 70)
    
    # Group by major
    from collections import Counter
    majors = Counter([a.get('Major', 'Unknown') for a in missing])
    
    print("\nMissing LinkedIn by Major (Top 10):")
    for major, count in majors.most_common(10):
        print(f"  {major:40s} {count:3d} alumni")
    
    # Group by graduation year (recent grads might be easier to find)
    from collections import Counter as Counter2
    years = Counter2([a.get('Grad_Year', 'Unknown') for a in missing if a.get('Grad_Year')])
    
    print("\nMissing LinkedIn by Graduation Year (Recent First):")
    sorted_years = sorted([(y, c) for y, c in years.items() if y and y != 'Unknown'], 
                         key=lambda x: int(x[0].split('/')[0]) if x[0] and x[0].split('/')[0].isdigit() else 9999,
                         reverse=True)
    for year, count in sorted_years[:10]:
        print(f"  {year:10s} {count:3d} alumni")
    
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    print("1. Start with recent graduates (2020-2026) - they're more likely to have LinkedIn")
    print("2. Focus on Computer Science/EECS majors - largest group, most active on LinkedIn")
    print("3. Use the LinkedIn_Search_URL column to quickly search for profiles")
    print("4. Verify profiles match before adding LinkedIn URLs")
    print("5. Consider reaching out to alumni who have LinkedIn to ask about others")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Find and analyze alumni missing LinkedIn profiles')
    parser.add_argument('--input', default='alumni_data_with_searches.csv',
                       help='Input CSV file with LinkedIn search URLs')
    parser.add_argument('--output', default='alumni_missing_linkedin.csv',
                       help='Output CSV file for alumni missing LinkedIn')
    parser.add_argument('--analyze', action='store_true',
                       help='Show analysis of missing LinkedIn profiles')
    parser.add_argument('--export', action='store_true',
                       help='Export alumni missing LinkedIn to separate CSV')
    
    args = parser.parse_args()
    
    # Load data
    alumni_data = load_alumni_data(args.input)
    print(f"Loaded {len(alumni_data)} alumni records")
    
    # Analyze
    analysis = analyze_missing_linkedin(alumni_data)
    
    print("\n" + "=" * 70)
    print("LINKEDIN PROFILE STATUS")
    print("=" * 70)
    print(f"Total alumni: {analysis['total']}")
    print(f"LinkedIn profiles found: {analysis['found_count']} ({analysis['found_count']/analysis['total']*100:.1f}%)")
    print(f"LinkedIn profiles missing: {analysis['missing_count']} ({analysis['missing_count']/analysis['total']*100:.1f}%)")
    
    if args.analyze or args.export:
        if analysis['missing_count'] > 0:
            if args.analyze:
                print_prioritization_suggestions(analysis['missing_linkedin'])
            
            if args.export:
                export_missing_linkedin(alumni_data, args.output)
                print(f"\nYou can now use '{args.output}' to focus on finding LinkedIn profiles")
                print("The file includes LinkedIn_Search_URL and LinkedIn_Search_String columns")
                print("to help you quickly search for each alumni on LinkedIn.")
        else:
            print("\nAll alumni have LinkedIn profiles! 🎉")


if __name__ == '__main__':
    main()



