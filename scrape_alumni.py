"""
Alumni Data Scraper for Cal Theta Tau
Scrapes alumni profiles from https://www.calthetatau.com/users/alumni
"""

import time
import csv
import sys
import re
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Page

# Configuration constants
BASE_URL = 'https://www.calthetatau.com/users/alumni'
OUTPUT_FILE = 'alumni_data.csv'
DELAY_BETWEEN_PAGES = 2  # Delay between page requests in seconds
PAGE_LOAD_TIMEOUT = 30000  # 30 seconds timeout for page loads
MAX_RETRIES = 3  # Maximum number of retries for failed requests
RETRY_DELAY = 5  # Initial delay for retries (exponential backoff)


def extract_alumni_data(page: Page) -> List[Dict[str, Optional[str]]]:
    """
    Extract alumni data from the current page.
    
    Args:
        page: Playwright page object
        
    Returns:
        List of dictionaries containing alumni information
    """
    alumni_list = []
    
    try:
        # Wait for the page content to load
        page.wait_for_load_state('networkidle', timeout=PAGE_LOAD_TIMEOUT)
        time.sleep(1)  # Additional wait for JavaScript rendering
        
        # Find all alumni profile items using the correct selector
        # Each alumni is in a div with class "user-index-item"
        profiles = page.query_selector_all('.user-index-item')
        
        if not profiles or len(profiles) == 0:
            return alumni_list
        
        # Extract data from each profile
        for profile in profiles:
            try:
                alumni_data = {
                    'Name': None,
                    'Major': None,
                    'Grad_Year': None,
                    'Profile_URL': None
                }
                
                # Extract name from h3 tag
                try:
                    name_elem = profile.query_selector('h3')
                    if name_elem:
                        alumni_data['Name'] = name_elem.inner_text().strip()
                except Exception as e:
                    print(f"  Warning: Could not extract name: {e}")
                
                # Extract major and graduation year from p tag
                # Format is typically: "Major <br> Class of Year"
                try:
                    info_elem = profile.query_selector('p')
                    if info_elem:
                        info_text = info_elem.inner_text().strip()
                        # Split by newline or "Class of"
                        if 'Class of' in info_text:
                            parts = info_text.split('Class of')
                            if len(parts) == 2:
                                alumni_data['Major'] = parts[0].strip()
                                alumni_data['Grad_Year'] = parts[1].strip()
                            else:
                                # Fallback: try to extract year
                                alumni_data['Major'] = info_text
                                # Try to find year pattern
                                year_match = re.search(r'\b(19|20)\d{2}\b', info_text)
                                if year_match:
                                    alumni_data['Grad_Year'] = year_match.group()
                        else:
                            # If no "Class of" found, treat entire text as major
                            alumni_data['Major'] = info_text
                except Exception as e:
                    print(f"  Warning: Could not extract major/year: {e}")
                
                # Extract profile URL from the first link (a tag)
                try:
                    link_elem = profile.query_selector('a')
                    if link_elem:
                        href = link_elem.get_attribute('href')
                        if href:
                            # Convert relative URLs to absolute
                            if href.startswith('http'):
                                alumni_data['Profile_URL'] = href
                            else:
                                alumni_data['Profile_URL'] = f"https://www.calthetatau.com{href}"
                except Exception as e:
                    print(f"  Warning: Could not extract profile URL: {e}")
                
                # Only add if we have at least a name
                if alumni_data['Name']:
                    alumni_list.append(alumni_data)
                else:
                    print("  Warning: Skipped profile with no name")
                    
            except Exception as e:
                print(f"  Error extracting data from profile: {e}")
                continue
                
    except PlaywrightTimeoutError:
        print("Error: Page load timeout")
    except Exception as e:
        print(f"Error extracting alumni data: {e}")
    
    return alumni_list


def scrape_page_with_retry(page: Page, url: str, retry_count: int = 0) -> bool:
    """
    Navigate to a page with retry logic.
    
    Args:
        page: Playwright page object
        url: URL to navigate to
        retry_count: Current retry attempt
        
    Returns:
        True if page loaded successfully, False otherwise
    """
    try:
        page.goto(url, wait_until='networkidle', timeout=PAGE_LOAD_TIMEOUT)
        return True
    except PlaywrightTimeoutError:
        if retry_count < MAX_RETRIES:
            wait_time = RETRY_DELAY * (2 ** retry_count)  # Exponential backoff
            print(f"Timeout loading {url}. Retrying in {wait_time} seconds... (Attempt {retry_count + 1}/{MAX_RETRIES})")
            time.sleep(wait_time)
            return scrape_page_with_retry(page, url, retry_count + 1)
        else:
            print(f"Error: Failed to load {url} after {MAX_RETRIES} retries")
            return False
    except Exception as e:
        if retry_count < MAX_RETRIES:
            wait_time = RETRY_DELAY * (2 ** retry_count)
            print(f"Error loading {url}: {e}. Retrying in {wait_time} seconds... (Attempt {retry_count + 1}/{MAX_RETRIES})")
            time.sleep(wait_time)
            return scrape_page_with_retry(page, url, retry_count + 1)
        else:
            print(f"Error: Failed to load {url} after {MAX_RETRIES} retries: {e}")
            return False


def save_to_csv(alumni_data: List[Dict[str, Optional[str]]], filename: str) -> None:
    """
    Save alumni data to a CSV file.
    
    Args:
        alumni_data: List of dictionaries containing alumni information
        filename: Output CSV filename
    """
    if not alumni_data:
        print("Warning: No data to save")
        return
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Name', 'Major', 'Grad_Year', 'Profile_URL']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(alumni_data)
        print(f"Successfully saved {len(alumni_data)} records to {filename}")
    except Exception as e:
        print(f"Error saving data to CSV: {e}")
        sys.exit(1)


def scrape_alumni() -> None:
    """
    Main function to scrape alumni data from all pages.
    """
    print("Starting alumni scraper...")
    print(f"Target URL: {BASE_URL}")
    print(f"Output file: {OUTPUT_FILE}")
    print("-" * 50)
    
    all_alumni_data = []
    page_number = 1
    
    with sync_playwright() as p:
        # Launch browser in headless mode
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            while True:
                # Construct URL for current page
                if page_number == 1:
                    url = BASE_URL
                else:
                    url = f"{BASE_URL}?page={page_number}"
                
                print(f"\nScraping page {page_number}...")
                print(f"URL: {url}")
                
                # Navigate to page with retry logic
                if not scrape_page_with_retry(page, url):
                    print(f"Failed to load page {page_number}. Stopping scraper.")
                    break
                
                # Extract alumni data from current page
                page_alumni = extract_alumni_data(page)
                
                if not page_alumni:
                    print(f"No alumni found on page {page_number}. Ending scrape.")
                    break
                
                # Add to total collection
                all_alumni_data.extend(page_alumni)
                print(f"Scraped page {page_number}: found {len(page_alumni)} alumni")
                print(f"Total alumni collected so far: {len(all_alumni_data)}")
                
                # Move to next page
                page_number += 1
                
                # Rate limiting: delay between requests
                if DELAY_BETWEEN_PAGES > 0:
                    time.sleep(DELAY_BETWEEN_PAGES)
                    
        except KeyboardInterrupt:
            print("\n\nScraping interrupted by user.")
        except Exception as e:
            print(f"\nError during scraping: {e}")
        finally:
            browser.close()
            print("\nBrowser closed.")
    
    # Save all collected data to CSV
    if all_alumni_data:
        print(f"\n{'=' * 50}")
        print(f"Scraping complete!")
        print(f"Total alumni records: {len(all_alumni_data)}")
        print(f"Saving to {OUTPUT_FILE}...")
        save_to_csv(all_alumni_data, OUTPUT_FILE)
    else:
        print("\nNo alumni data collected.")


if __name__ == '__main__':
    scrape_alumni()

