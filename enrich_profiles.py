"""
Profile Enrichment Tool for Alumni Data
Scrapes individual alumni profile pages to extract LinkedIn URLs, email, company, job title, and other information
"""

import csv
import time
import sys
import re
from typing import Dict, Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Page

# Configuration constants
INPUT_CSV = 'alumni_data.csv'
OUTPUT_CSV = 'alumni_data_enriched.csv'
DELAY_BETWEEN_PROFILES = 1  # Delay between profile requests in seconds
PAGE_LOAD_TIMEOUT = 20000  # 20 seconds timeout for page loads
MAX_RETRIES = 2  # Maximum number of retries for failed requests
RETRY_DELAY = 3  # Initial delay for retries in seconds


def extract_profile_data(page: Page, profile_url: str) -> Dict[str, Optional[str]]:
    """
    Extract additional data from an alumni profile page.
    
    Args:
        page: Playwright page object
        profile_url: URL of the alumni profile page
        
    Returns:
        Dictionary containing extracted profile information
    """
    profile_data = {
        'LinkedIn_URL': None,
        'Email': None,
        'Current_Company': None,
        'Job_Title': None,
        'Location': None,
        'Bio': None
    }
    
    try:
        # Navigate to profile page
        page.goto(profile_url, wait_until='networkidle', timeout=PAGE_LOAD_TIMEOUT)
        time.sleep(0.5)  # Brief wait for JavaScript rendering
        
        # Extract LinkedIn URL
        try:
            # Look for LinkedIn links - they might be in various formats
            linkedin_links = page.query_selector_all('a[href*="linkedin.com"]')
            for link in linkedin_links:
                href = link.get_attribute('href')
                if href:
                    # Normalize LinkedIn URL
                    if href.startswith('www.linkedin.com'):
                        href = f"https://{href}"
                    elif href.startswith('linkedin.com'):
                        href = f"https://{href}"
                    elif not href.startswith('http'):
                        href = f"https://{href}"
                    profile_data['LinkedIn_URL'] = href
                    break
        except Exception as e:
            pass
        
        # Extract email (if publicly visible)
        try:
            # Look for email patterns in the page text (not HTML to avoid reversed emails in HTML)
            page_text = page.inner_text('body')
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, page_text)
            
            # Filter out common non-email patterns and reversed emails
            filtered_emails = []
            for e in emails:
                e_lower = e.lower().strip()
                
                # Skip if empty
                if not e_lower:
                    continue
                
                # Skip common non-email patterns (check both local and domain parts)
                skip_patterns = ['example.com', 'test.com', 'image', 'sprite', 'icon', 'gravatar', 
                                'facebook', 'instagram', 'linkedin.com', 'moc.liamg', 'uat.ateht',
                                'cal.thetatau', 'thetatau', 'moc.liamg@uat.ateht.lac']
                
                # Check if email contains any skip patterns (exact match or substring)
                if any(pattern in e_lower for pattern in skip_patterns):
                    continue
                
                # Also check for the exact reversed email pattern
                if 'moc.liamg@uat.ateht' in e_lower or 'uat.ateht.lac' in e_lower:
                    continue
                
                # Parse email parts
                if '@' not in e_lower:
                    continue
                    
                local_part, domain_part = e_lower.split('@', 1)
                
                # Skip reversed emails - check for known reversed patterns
                # Pattern: moc.liamg@uat.ateht.lac (cal.thetatau@gmail.com reversed)
                reversed_indicators = [
                    'moc.',  # .com reversed
                    'ude.',  # .edu reversed  
                    'gro.',  # .org reversed
                    'tac.',  # .cat reversed (sometimes used)
                    'uat.ateht',  # thetatau reversed
                    'lac.',  # cal reversed
                ]
                
                # Check if domain or local part contains reversed indicators
                if any(indicator in domain_part or indicator in local_part for indicator in reversed_indicators):
                    continue
                
                # Valid email domains should end with common TLDs
                valid_tlds = ['.com', '.edu', '.org', '.net', '.io', '.co', '.gov']
                has_valid_tld = any(domain_part.endswith(tld) for tld in valid_tlds)
                
                # Skip if domain doesn't have a valid TLD
                if not has_valid_tld:
                    continue
                
                # Skip if domain has unusual structure (too many dots, likely reversed)
                # Normal domains: example.com, user@berkeley.edu (1-2 dots typically)
                # Reversed domains: uat.ateht.lac (3+ dots in unusual pattern)
                dot_count = domain_part.count('.')
                if dot_count > 3:
                    continue
                if dot_count == 3 and not any(x in domain_part for x in ['gmail', 'yahoo', 'hotmail', 'outlook', 'berkeley', 'stanford', 'mit']):
                    # 3 dots is suspicious unless it's a known university/company domain
                    continue
                
                # Skip if local part looks reversed (contains dots in unusual pattern)
                if local_part.count('.') > 2:
                    continue
                
                filtered_emails.append(e)
            
            if filtered_emails:
                # Prefer berkeley.edu emails over others
                berkeley_emails = [e for e in filtered_emails if 'berkeley.edu' in e.lower()]
                if berkeley_emails:
                    profile_data['Email'] = berkeley_emails[0]
                else:
                    # Use the first valid email found
                    profile_data['Email'] = filtered_emails[0]
        except Exception as e:
            pass
        
        # Extract company and job title (if available in bio or profile)
        # Note: Company extraction is difficult without structured data
        # This is a placeholder - actual company info would need to be scraped from LinkedIn
        # or found in a structured format on the profile page
        try:
            # Look for company in specific sections only (not in footer/navigation)
            # Skip company extraction for now as it's prone to false positives
            # Users should manually verify company information from LinkedIn profiles
            pass
        except Exception as e:
            pass
        
        # Extract bio/text content
        try:
            # Look for biography heading first
            bio_heading = page.query_selector('h3.mb1.mt4')
            
            if bio_heading:
                heading_text = bio_heading.inner_text().strip()
                # Check if this is actually a biography heading
                if 'Biography' in heading_text or 'Bio' in heading_text:
                    # Find the next sibling element (should be the bio paragraph)
                    try:
                        # Get the parent container
                        parent = bio_heading.evaluate('el => el.parentElement')
                        if parent:
                            # Find the next p tag after the heading
                            bio_para = page.query_selector('h3.mb1.mt4 + p')
                            if bio_para:
                                bio_text = bio_para.inner_text().strip()
                            else:
                                # Try to get text from the container after the heading
                                # Get all text, find the heading, get text after it
                                container = page.query_selector('.container')
                                if container:
                                    all_text = container.inner_text()
                                    # Split by the heading and get the next part
                                    if heading_text in all_text:
                                        parts = all_text.split(heading_text, 1)
                                        if len(parts) > 1:
                                            # Get the first paragraph after the heading
                                            next_part = parts[1].strip()
                                            # Take first line or first 500 chars
                                            bio_text = next_part.split('\n')[0].strip()
                                        else:
                                            bio_text = None
                                    else:
                                        bio_text = None
                                else:
                                    bio_text = None
                        else:
                            bio_text = None
                    except:
                        bio_text = None
                    
                    # Clean and validate bio text
                    if bio_text:
                        bio_text = bio_text.strip()
                        
                        # Filter out footer/navigation text
                        footer_keywords = ['©', 'Theta Tau', 'ASUC', 'sponsored', 'student organization',
                                          'University of California', 'Berkeley', 'Facebook', 'Instagram',
                                          'Home', 'About', 'Brothers', 'Rush', 'Sign In', 'General',
                                          'Recruitment', 'Contact', 'National Theta Tau']
                        
                        # Check if bio contains footer keywords
                        if any(keyword in bio_text for keyword in footer_keywords):
                            bio_text = None
                        # Check if it's too short (likely not a real bio)
                        elif len(bio_text) < 15:
                            bio_text = None
                        # Check if it's just a single word or looks like navigation
                        elif len(bio_text.split()) < 3:
                            bio_text = None
                        # Limit length
                        elif len(bio_text) > 500:
                            bio_text = bio_text[:500] + "..."
                        
                        if bio_text:
                            profile_data['Bio'] = bio_text
        except Exception as e:
            pass
        
    except PlaywrightTimeoutError:
        print(f"  Warning: Timeout loading profile {profile_url}")
    except Exception as e:
        print(f"  Warning: Error extracting data from {profile_url}: {e}")
    
    return profile_data


def scrape_profile_with_retry(page: Page, url: str, retry_count: int = 0) -> Dict[str, Optional[str]]:
    """
    Scrape a profile page with retry logic.
    
    Args:
        page: Playwright page object
        url: Profile URL to scrape
        retry_count: Current retry attempt
        
    Returns:
        Dictionary containing extracted profile information
    """
    try:
        return extract_profile_data(page, url)
    except Exception as e:
        if retry_count < MAX_RETRIES:
            wait_time = RETRY_DELAY * (retry_count + 1)
            print(f"  Retrying {url} in {wait_time} seconds... (Attempt {retry_count + 1}/{MAX_RETRIES})")
            time.sleep(wait_time)
            return scrape_profile_with_retry(page, url, retry_count + 1)
        else:
            print(f"  Failed to scrape {url} after {MAX_RETRIES} retries")
            return {
                'LinkedIn_URL': None,
                'Email': None,
                'Current_Company': None,
                'Job_Title': None,
                'Location': None,
                'Bio': None
            }


def enrich_alumni_profiles(input_file: str, output_file: str, start_index: int = 0, limit: Optional[int] = None) -> None:
    """
    Enrich alumni profiles by scraping individual profile pages.
    
    Args:
        input_file: Input CSV file with alumni data
        output_file: Output CSV file with enriched data
        start_index: Index to start from (for resuming)
        limit: Maximum number of profiles to process (None for all)
    """
    print("Starting profile enrichment...")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Starting from index: {start_index}")
    if limit:
        print(f"Processing limit: {limit} profiles")
    print("-" * 50)
    
    # Read existing alumni data
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            alumni_data = list(reader)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    
    total_profiles = len(alumni_data)
    print(f"Total profiles to process: {total_profiles}")
    
    # Determine end index
    end_index = start_index + limit if limit else total_profiles
    end_index = min(end_index, total_profiles)
    
    # Process profiles
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            enriched_count = 0
            linkedin_found = 0
            email_found = 0
            
            for i in range(start_index, end_index):
                alumni = alumni_data[i]
                profile_url = alumni.get('Profile_URL', '')
                
                if not profile_url:
                    print(f"\n[{i+1}/{total_profiles}] Skipping {alumni.get('Name', 'Unknown')} - No profile URL")
                    continue
                
                print(f"\n[{i+1}/{total_profiles}] Processing: {alumni.get('Name', 'Unknown')}")
                print(f"  URL: {profile_url}")
                
                # Scrape profile page
                profile_data = scrape_profile_with_retry(page, profile_url)
                
                # Merge profile data with alumni data
                alumni.update(profile_data)
                
                # Track statistics
                if profile_data['LinkedIn_URL']:
                    linkedin_found += 1
                    print(f"  ✓ Found LinkedIn: {profile_data['LinkedIn_URL']}")
                if profile_data['Email']:
                    email_found += 1
                    print(f"  ✓ Found Email: {profile_data['Email']}")
                if profile_data['Current_Company']:
                    print(f"  ✓ Found Company: {profile_data['Current_Company']}")
                if profile_data['Bio']:
                    print(f"  ✓ Found Bio: {profile_data['Bio'][:50]}...")
                
                enriched_count += 1
                
                # Rate limiting
                if DELAY_BETWEEN_PROFILES > 0 and i < end_index - 1:
                    time.sleep(DELAY_BETWEEN_PROFILES)
                    
        except KeyboardInterrupt:
            print("\n\nEnrichment interrupted by user.")
            print(f"Processed {enriched_count} profiles. Saving progress...")
        except Exception as e:
            print(f"\nError during enrichment: {e}")
        finally:
            browser.close()
    
    # Write enriched data to CSV
    if alumni_data:
        fieldnames = ['Name', 'Major', 'Grad_Year', 'Profile_URL', 
                     'LinkedIn_URL', 'Email', 'Current_Company', 'Job_Title', 'Location', 'Bio']
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(alumni_data)
            
            print(f"\n{'=' * 50}")
            print(f"Enrichment complete!")
            print(f"Processed: {enriched_count} profiles")
            print(f"LinkedIn URLs found: {linkedin_found}")
            print(f"Emails found: {email_found}")
            print(f"Data saved to: {output_file}")
        except Exception as e:
            print(f"Error saving enriched data: {e}")
            sys.exit(1)
    else:
        print("No alumni data to save.")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich alumni profiles with additional information')
    parser.add_argument('--input', default=INPUT_CSV, help='Input CSV file (default: alumni_data.csv)')
    parser.add_argument('--output', default=OUTPUT_CSV, help='Output CSV file (default: alumni_data_enriched.csv)')
    parser.add_argument('--start', type=int, default=0, help='Start index (for resuming)')
    parser.add_argument('--limit', type=int, default=None, help='Maximum number of profiles to process')
    
    args = parser.parse_args()
    
    enrich_alumni_profiles(args.input, args.output, args.start, args.limit)

