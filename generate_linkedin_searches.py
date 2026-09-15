"""
LinkedIn Search URL Generator for Alumni Data
Generates LinkedIn search URLs for each alumni based on name, school, major, and graduation year
"""

import csv
import sys
import urllib.parse
from typing import List, Dict, Optional


def normalize_name(name: str) -> tuple:
    """
    Normalize name for LinkedIn search.
    Returns first name and last name.
    """
    name = name.strip().upper()
    parts = name.split()
    
    if len(parts) == 0:
        return ("", "")
    elif len(parts) == 1:
        return (parts[0], "")
    else:
        # First name is first part, last name is last part
        first_name = parts[0]
        last_name = parts[-1]
        return (first_name, last_name)


def generate_linkedin_search_url(name: str, major: Optional[str] = None, 
                                  grad_year: Optional[str] = None, 
                                  school: str = "UC Berkeley") -> str:
    """
    Generate a LinkedIn search URL for an alumni.
    
    Args:
        name: Alumni name
        major: Major/field of study
        grad_year: Graduation year
        school: School name (default: UC Berkeley)
        
    Returns:
        LinkedIn search URL
    """
    first_name, last_name = normalize_name(name)
    
    # Build search query components
    query_parts = []
    
    if first_name and last_name:
        query_parts.append(f"{first_name} {last_name}")
    elif first_name:
        query_parts.append(first_name)
    
    # Add school
    query_parts.append(school)
    
    # Add major if available
    if major:
        query_parts.append(major)
    
    # Build LinkedIn search URL
    # LinkedIn search format: https://www.linkedin.com/search/results/people/?keywords=...
    query = " ".join(query_parts)
    encoded_query = urllib.parse.quote(query)
    
    # Create search URL with filters
    base_url = "https://www.linkedin.com/search/results/people/"
    params = {
        'keywords': query,
        'origin': 'FACETED_SEARCH'
    }
    
    # Add school filter if possible (this is a simplified version)
    # Note: LinkedIn's actual search uses complex filters that require login
    param_string = "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
    search_url = f"{base_url}?{param_string}"
    
    return search_url


def generate_linkedin_search_string(name: str, major: Optional[str] = None, 
                                    grad_year: Optional[str] = None, 
                                    school: str = "UC Berkeley") -> str:
    """
    Generate a LinkedIn search string (for manual copying into LinkedIn search).
    
    Args:
        name: Alumni name
        major: Major/field of study
        grad_year: Graduation year
        school: School name (default: UC Berkeley)
        
    Returns:
        LinkedIn search string
    """
    first_name, last_name = normalize_name(name)
    
    query_parts = []
    
    if first_name and last_name:
        query_parts.append(f'"{first_name} {last_name}"')
    elif first_name:
        query_parts.append(first_name)
    
    query_parts.append(school)
    
    if major:
        query_parts.append(major)
    
    if grad_year:
        query_parts.append(grad_year)
    
    return " ".join(query_parts)


def generate_linkedin_profile_url(linkedin_username: Optional[str]) -> Optional[str]:
    """
    Generate a full LinkedIn profile URL from a username or partial URL.
    
    Args:
        linkedin_username: LinkedIn username or partial URL
        
    Returns:
        Full LinkedIn profile URL or None
    """
    if not linkedin_username:
        return None
    
    # If it's already a full URL, return it
    if linkedin_username.startswith('http'):
        return linkedin_username
    
    # If it starts with linkedin.com or www.linkedin.com
    if linkedin_username.startswith('linkedin.com/in/') or linkedin_username.startswith('www.linkedin.com/in/'):
        return f"https://{linkedin_username.lstrip('www.')}"
    
    # If it's just a username
    if '/' not in linkedin_username:
        return f"https://www.linkedin.com/in/{linkedin_username}"
    
    # If it starts with /in/
    if linkedin_username.startswith('/in/'):
        return f"https://www.linkedin.com{linkedin_username}"
    
    return f"https://www.linkedin.com/in/{linkedin_username}"


def process_alumni_csv(input_file: str, output_file: str) -> None:
    """
    Process alumni CSV and generate LinkedIn search URLs.
    
    Args:
        input_file: Input CSV file with alumni data
        output_file: Output CSV file with LinkedIn search URLs
    """
    print("Generating LinkedIn search URLs...")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print("-" * 50)
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            alumni_data = list(reader)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    
    print(f"Processing {len(alumni_data)} alumni records...")
    
    # Process each alumni record
    for alumni in alumni_data:
        name = alumni.get('Name', '')
        major = alumni.get('Major', '')
        grad_year = alumni.get('Grad_Year', '')
        linkedin_url = alumni.get('LinkedIn_URL', '')
        
        # Generate LinkedIn search URL
        search_url = generate_linkedin_search_url(name, major, grad_year)
        alumni['LinkedIn_Search_URL'] = search_url
        
        # Generate LinkedIn search string (for manual use)
        search_string = generate_linkedin_search_string(name, major, grad_year)
        alumni['LinkedIn_Search_String'] = search_string
        
        # Normalize existing LinkedIn URL if present
        if linkedin_url:
            normalized_linkedin = generate_linkedin_profile_url(linkedin_url)
            if normalized_linkedin:
                alumni['LinkedIn_URL'] = normalized_linkedin
    
    # Write enriched data to CSV
    fieldnames = ['Name', 'Major', 'Grad_Year', 'Profile_URL', 
                 'LinkedIn_URL', 'LinkedIn_Search_URL', 'LinkedIn_Search_String',
                 'Email', 'Current_Company', 'Job_Title', 'Location', 'Bio']
    
    # Only include fields that exist in the data
    existing_fieldnames = [f for f in fieldnames if any(f in row for row in alumni_data)]
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=existing_fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(alumni_data)
        
        print(f"\n{'=' * 50}")
        print(f"LinkedIn search URLs generated!")
        print(f"Processed: {len(alumni_data)} alumni records")
        print(f"Data saved to: {output_file}")
        print("\nUsage:")
        print("1. Open LinkedIn and log in")
        print("2. Copy a LinkedIn_Search_String and paste it into LinkedIn's search bar")
        print("3. Or click on LinkedIn_Search_URL to open LinkedIn search in your browser")
        print("4. Manually verify and connect with the correct profile")
    except Exception as e:
        print(f"Error saving data: {e}")
        sys.exit(1)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate LinkedIn search URLs for alumni')
    parser.add_argument('--input', default='alumni_data.csv', help='Input CSV file (default: alumni_data.csv)')
    parser.add_argument('--output', default='alumni_data_with_linkedin_searches.csv', 
                       help='Output CSV file (default: alumni_data_with_linkedin_searches.csv)')
    
    args = parser.parse_args()
    
    process_alumni_csv(args.input, args.output)



