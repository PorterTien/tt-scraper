"""
Networking Helper - Main Utility Script
Interactive tool to combine all networking and alumni data tools
"""

import sys
import subprocess
import os
from typing import Optional


def print_menu():
    """Print the main menu."""
    print("\n" + "=" * 70)
    print("ALUMNI NETWORKING HELPER")
    print("=" * 70)
    print("\n1. Analyze Alumni Data")
    print("2. Enrich Profiles (Scrape LinkedIn, Email, Company info)")
    print("3. Generate LinkedIn Search URLs")
    print("4. Filter Alumni by Criteria")
    print("5. Run Full Pipeline (Analyze -> Enrich -> Generate LinkedIn Searches)")
    print("6. Exit")
    print("-" * 70)


def run_analysis(input_file: str = 'alumni_data.csv'):
    """Run alumni data analysis."""
    print("\n" + "=" * 70)
    print("RUNNING ALUMNI DATA ANALYSIS")
    print("=" * 70)
    
    cmd = [sys.executable, 'analyze_alumni.py', '--input', input_file, '--analyze']
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running analysis: {e}")
    except FileNotFoundError:
        print("Error: analyze_alumni.py not found. Make sure you're in the correct directory.")


def run_enrichment(input_file: str = 'alumni_data.csv', 
                   output_file: str = 'alumni_data_enriched.csv',
                   start_index: int = 0,
                   limit: Optional[int] = None):
    """Run profile enrichment."""
    print("\n" + "=" * 70)
    print("RUNNING PROFILE ENRICHMENT")
    print("=" * 70)
    print("This will scrape individual profile pages to extract LinkedIn URLs,")
    print("email addresses, company information, and other details.")
    print("\nNote: This may take a while depending on the number of profiles.")
    print("You can resume by specifying --start and --limit options.")
    
    response = input("\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("Enrichment cancelled.")
        return
    
    cmd = [sys.executable, 'enrich_profiles.py', 
           '--input', input_file, 
           '--output', output_file]
    
    if start_index > 0:
        cmd.extend(['--start', str(start_index)])
    if limit:
        cmd.extend(['--limit', str(limit)])
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running enrichment: {e}")
    except FileNotFoundError:
        print("Error: enrich_profiles.py not found. Make sure you're in the correct directory.")
    except KeyboardInterrupt:
        print("\n\nEnrichment interrupted. You can resume later using --start option.")


def run_linkedin_search_generation(input_file: str = 'alumni_data.csv',
                                   output_file: str = 'alumni_data_with_linkedin_searches.csv'):
    """Generate LinkedIn search URLs."""
    print("\n" + "=" * 70)
    print("GENERATING LINKEDIN SEARCH URLS")
    print("=" * 70)
    
    cmd = [sys.executable, 'generate_linkedin_searches.py',
           '--input', input_file,
           '--output', output_file]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error generating LinkedIn searches: {e}")
    except FileNotFoundError:
        print("Error: generate_linkedin_searches.py not found. Make sure you're in the correct directory.")


def run_filtering(input_file: str = 'alumni_data.csv'):
    """Interactive filtering of alumni data."""
    print("\n" + "=" * 70)
    print("FILTER ALUMNI DATA")
    print("=" * 70)
    
    # Get filter criteria
    print("\nEnter filter criteria (press Enter to skip):")
    
    major = input("Major (partial match): ").strip() or None
    grad_year_min = input("Minimum graduation year: ").strip()
    grad_year_min = int(grad_year_min) if grad_year_min else None
    grad_year_max = input("Maximum graduation year: ").strip()
    grad_year_max = int(grad_year_max) if grad_year_max else None
    years_exp_min = input("Minimum years of experience: ").strip()
    years_exp_min = int(years_exp_min) if years_exp_min else None
    years_exp_max = input("Maximum years of experience: ").strip()
    years_exp_max = int(years_exp_max) if years_exp_max else None
    
    print("\nExperience level:")
    print("1. Recent Grad (0-2 years)")
    print("2. Early Career (3-5 years)")
    print("3. Mid-Career (6-10 years)")
    print("4. Senior (11+ years)")
    exp_level_choice = input("Select (1-4, or press Enter to skip): ").strip()
    experience_level = None
    if exp_level_choice == '1':
        experience_level = 'Recent Grad (0-2 years)'
    elif exp_level_choice == '2':
        experience_level = 'Early Career (3-5 years)'
    elif exp_level_choice == '3':
        experience_level = 'Mid-Career (6-10 years)'
    elif exp_level_choice == '4':
        experience_level = 'Senior (11+ years)'
    
    has_linkedin = input("Has LinkedIn URL? (y/n/skip): ").strip().lower()
    has_linkedin = True if has_linkedin == 'y' else (False if has_linkedin == 'n' else None)
    
    has_email = input("Has Email? (y/n/skip): ").strip().lower()
    has_email = True if has_email == 'y' else (False if has_email == 'n' else None)
    
    output_file = input("Output CSV file (default: filtered_alumni.csv): ").strip()
    output_file = output_file or 'filtered_alumni.csv'
    
    # Build command
    cmd = [sys.executable, 'analyze_alumni.py', '--input', input_file, '--output', output_file]
    
    if major:
        cmd.extend(['--major', major])
    if grad_year_min:
        cmd.extend(['--grad-year-min', str(grad_year_min)])
    if grad_year_max:
        cmd.extend(['--grad-year-max', str(grad_year_max)])
    if years_exp_min:
        cmd.extend(['--years-exp-min', str(years_exp_min)])
    if years_exp_max:
        cmd.extend(['--years-exp-max', str(years_exp_max)])
    if experience_level:
        cmd.extend(['--experience-level', experience_level])
    if has_linkedin:
        cmd.append('--has-linkedin')
    if has_email:
        cmd.append('--has-email')
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running filter: {e}")
    except FileNotFoundError:
        print("Error: analyze_alumni.py not found. Make sure you're in the correct directory.")


def run_full_pipeline():
    """Run the full pipeline: Analyze -> Enrich -> Generate LinkedIn Searches."""
    print("\n" + "=" * 70)
    print("RUNNING FULL PIPELINE")
    print("=" * 70)
    print("This will:")
    print("1. Analyze alumni data")
    print("2. Enrich profiles with LinkedIn, email, company info")
    print("3. Generate LinkedIn search URLs")
    print("\nNote: This may take a significant amount of time.")
    
    response = input("\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("Pipeline cancelled.")
        return
    
    # Step 1: Analyze
    print("\n" + "=" * 70)
    print("STEP 1: ANALYZING ALUMNI DATA")
    print("=" * 70)
    run_analysis()
    
    # Step 2: Enrich
    print("\n" + "=" * 70)
    print("STEP 2: ENRICHING PROFILES")
    print("=" * 70)
    run_enrichment(output_file='alumni_data_enriched.csv')
    
    # Step 3: Generate LinkedIn searches
    print("\n" + "=" * 70)
    print("STEP 3: GENERATING LINKEDIN SEARCH URLS")
    print("=" * 70)
    run_linkedin_search_generation(input_file='alumni_data_enriched.csv',
                                   output_file='alumni_data_final.csv')
    
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE!")
    print("=" * 70)
    print("Output files:")
    print("  - alumni_data_enriched.csv (enriched data)")
    print("  - alumni_data_final.csv (with LinkedIn search URLs)")


def check_files():
    """Check if required files exist."""
    required_files = ['alumni_data.csv']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print("Warning: The following required files are missing:")
        for f in missing_files:
            print(f"  - {f}")
        print("\nPlease make sure you have run the scraper first:")
        print("  python scrape_alumni.py")
        return False
    return True


def main():
    """Main function."""
    print("\nWelcome to the Alumni Networking Helper!")
    print("This tool helps you analyze, enrich, and network with alumni data.")
    
    if not check_files():
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    while True:
        print_menu()
        choice = input("\nSelect an option (1-6): ").strip()
        
        if choice == '1':
            run_analysis()
        elif choice == '2':
            input_file = input("Input CSV file (default: alumni_data.csv): ").strip() or 'alumni_data.csv'
            output_file = input("Output CSV file (default: alumni_data_enriched.csv): ").strip() or 'alumni_data_enriched.csv'
            start_index = input("Start index (default: 0): ").strip()
            start_index = int(start_index) if start_index else 0
            limit_input = input("Limit number of profiles (default: all): ").strip()
            limit = int(limit_input) if limit_input else None
            run_enrichment(input_file, output_file, start_index, limit)
        elif choice == '3':
            input_file = input("Input CSV file (default: alumni_data.csv): ").strip() or 'alumni_data.csv'
            output_file = input("Output CSV file (default: alumni_data_with_linkedin_searches.csv): ").strip() or 'alumni_data_with_linkedin_searches.csv'
            run_linkedin_search_generation(input_file, output_file)
        elif choice == '4':
            input_file = input("Input CSV file (default: alumni_data.csv): ").strip() or 'alumni_data.csv'
            run_filtering(input_file)
        elif choice == '5':
            run_full_pipeline()
        elif choice == '6':
            print("\nGoodbye! Happy networking!")
            break
        else:
            print("\nInvalid choice. Please select 1-6.")
        
        input("\nPress Enter to continue...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)



