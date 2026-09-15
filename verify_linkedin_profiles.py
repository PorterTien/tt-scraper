"""
LinkedIn Profile Verification Tool
Interactive tool to verify LinkedIn profiles and update CSV file
"""

import csv
import sys
import webbrowser
import argparse
from typing import List, Dict, Optional


def load_alumni_from_csv(filename: str) -> List[Dict[str, str]]:
    """Load alumni records from CSV file."""
    alumni_list = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                alumni_list.append(row)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading CSV: {e}")
        sys.exit(1)
    
    return alumni_list


def save_alumni_to_csv(alumni_list: List[Dict[str, str]], filename: str, fieldnames: List[str]):
    """Save alumni records to CSV file."""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(alumni_list)
    except Exception as e:
        print(f"Error saving CSV: {e}")
        sys.exit(1)


def filter_alumni_with_linkedin(alumni_list: List[Dict[str, str]], 
                                min_confidence: Optional[str] = None,
                                limit: Optional[int] = None) -> List[Dict[str, str]]:
    """Filter alumni to only those with LinkedIn URLs."""
    filtered = []
    
    for alumni in alumni_list:
        linkedin_url = alumni.get('LinkedIn_URL', '').strip()
        if not linkedin_url:
            continue
        
        # Filter by confidence if specified
        if min_confidence:
            confidence = alumni.get('Confidence', '').strip().upper()
            # If confidence column doesn't exist or is empty, skip this record when filtering by confidence
            if not confidence:
                continue
            
            confidence_levels = {'VERY_LOW': 0, 'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
            min_level = confidence_levels.get(min_confidence.upper(), 0)
            alumni_level = confidence_levels.get(confidence, 0)
            
            # Only include if alumni's confidence level meets or exceeds minimum
            if alumni_level < min_level:
                continue
        
        filtered.append(alumni)
        
        if limit and len(filtered) >= limit:
            break
    
    return filtered


def display_context(alumni: Dict[str, str], index: int, total: int):
    """Display alumni context information."""
    name = alumni.get('Name', 'Unknown')
    major = alumni.get('Major', 'N/A')
    grad_year = alumni.get('Grad_Year', 'N/A')
    company = alumni.get('Current_Company', '').strip()
    job_title = alumni.get('Job_Title', '').strip()
    location = alumni.get('Location', '').strip()
    linkedin_url = alumni.get('LinkedIn_URL', '').strip()
    confidence = alumni.get('Confidence', '').strip()
    
    print("\n" + "=" * 70)
    print(f"[{index}/{total}] Verifying: {name}")
    print("-" * 70)
    print(f"Major: {major} | Year: {grad_year}")
    
    if company:
        print(f"Company: {company}")
    if job_title:
        print(f"Job Title: {job_title}")
    if location:
        print(f"Location: {location}")
    if confidence:
        print(f"Confidence: {confidence}")
    
    print(f"LinkedIn: {linkedin_url}")
    print("=" * 70)


def verify_profiles(filtered_alumni: List[Dict[str, str]],
                   all_alumni: List[Dict[str, str]],
                   input_file: str,
                   fieldnames: List[str],
                   auto_save: bool = True,
                   start_from: int = 1):
    """Main verification loop."""
    original_total = len(filtered_alumni)
    verified_count = 0
    removed_count = 0
    skipped_count = 0
    
    # Adjust start_from to be 0-based for list indexing
    start_index = max(0, start_from - 1)
    
    # Skip profiles before start_from
    if start_index > 0:
        if start_index >= original_total:
            print(f"Error: start_from ({start_from}) is greater than total profiles ({original_total})")
            return
        print(f"\nResuming from position {start_from} (skipping first {start_index} profiles)...")
        filtered_alumni = filtered_alumni[start_index:]
        # Update total to reflect remaining profiles
        total = len(filtered_alumni)
    else:
        total = original_total
    
    # Create a mapping of Profile_URL to index in all_alumni for quick updates
    profile_url_to_index = {}
    for idx, alumni in enumerate(all_alumni):
        profile_url = alumni.get('Profile_URL', '').strip()
        if profile_url:
            profile_url_to_index[profile_url] = idx
    
    print(f"\nStarting verification of {total} LinkedIn profiles...")
    print("Instructions:")
    print("  y = Yes, keep this LinkedIn URL")
    print("  n = No, remove this LinkedIn URL")
    print("  s = Skip (leave unchanged)")
    print("  q = Quit and save progress")
    print("\nPress Enter after viewing the LinkedIn profile in your browser.")
    
    try:
        for i, alumni in enumerate(filtered_alumni, start_from):
            linkedin_url = alumni.get('LinkedIn_URL', '').strip()
            if not linkedin_url:
                # Skip if LinkedIn URL was already removed
                skipped_count += 1
                continue
            
            # Display context
            display_context(alumni, i, total)
            
            # Open LinkedIn URL in browser
            try:
                print("\nOpening LinkedIn profile in browser...")
                webbrowser.open(linkedin_url)
                print("(Browser opened. View the profile, then return here.)")
            except Exception as e:
                print(f"Warning: Could not open browser: {e}")
                print(f"LinkedIn URL: {linkedin_url}")
            
            # Get user input
            while True:
                try:
                    response = input("\nIs this the correct profile? [y/n/s/q]: ").strip().lower()
                    
                    if response == 'y':
                        # Keep the LinkedIn URL
                        verified_count += 1
                        print(f"✓ Kept LinkedIn URL for {alumni.get('Name', 'Unknown')}")
                        break
                    
                    elif response == 'n':
                        # Remove the LinkedIn URL from the full alumni list
                        profile_url = alumni.get('Profile_URL', '').strip()
                        if profile_url in profile_url_to_index:
                            idx = profile_url_to_index[profile_url]
                            all_alumni[idx]['LinkedIn_URL'] = ''
                            # Also update the filtered list
                            alumni['LinkedIn_URL'] = ''
                        
                        removed_count += 1
                        print(f"✗ Removed LinkedIn URL for {alumni.get('Name', 'Unknown')}")
                        
                        # Save CSV immediately if auto_save is enabled
                        if auto_save:
                            save_alumni_to_csv(all_alumni, input_file, fieldnames)
                            print("  ✓ CSV updated")
                        break
                    
                    elif response == 's':
                        # Skip
                        skipped_count += 1
                        print(f"⊘ Skipped {alumni.get('Name', 'Unknown')}")
                        break
                    
                    elif response == 'q':
                        # Quit
                        print("\nQuitting...")
                        # Save progress before quitting
                        if auto_save:
                            save_alumni_to_csv(all_alumni, input_file, fieldnames)
                            print("Progress saved.")
                        
                        print(f"\nSummary:")
                        print(f"  Verified: {verified_count}")
                        print(f"  Removed: {removed_count}")
                        print(f"  Skipped: {skipped_count}")
                        print(f"  Remaining: {total - i}")
                        return
                    
                    else:
                        print("Invalid input. Please enter y, n, s, or q.")
                        continue
                
                except KeyboardInterrupt:
                    print("\n\nInterrupted by user. Saving progress...")
                    if auto_save:
                        save_alumni_to_csv(all_alumni, input_file, fieldnames)
                        print("Progress saved.")
                    
                    print(f"\nSummary:")
                    print(f"  Verified: {verified_count}")
                    print(f"  Removed: {removed_count}")
                    print(f"  Skipped: {skipped_count}")
                    print(f"  Remaining: {total - i}")
                    return
        
        # All profiles processed
        print("\n" + "=" * 70)
        print("Verification complete!")
        print("=" * 70)
        print(f"\nSummary:")
        print(f"  Verified: {verified_count}")
        print(f"  Removed: {removed_count}")
        print(f"  Skipped: {skipped_count}")
        print(f"  Total processed: {total}")
        
        # Final save
        if auto_save:
            save_alumni_to_csv(all_alumni, input_file, fieldnames)
            print("\n✓ Final CSV saved")
    
    except Exception as e:
        print(f"\nError during verification: {e}")
        if auto_save:
            print("Attempting to save progress...")
            try:
                save_alumni_to_csv(all_alumni, input_file, fieldnames)
                print("Progress saved.")
            except Exception as save_error:
                print(f"Error saving progress: {save_error}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Verify LinkedIn profiles interactively')
    parser.add_argument('--input', default='alumni_data_enriched.csv',
                       help='Input CSV file with alumni data (default: alumni_data_enriched.csv)')
    parser.add_argument('--output', default=None,
                       help='Output CSV file (default: overwrites input file)')
    parser.add_argument('--min-confidence', type=str, default=None,
                       choices=['LOW', 'MEDIUM', 'HIGH', 'VERY_LOW'],
                       help='Minimum confidence level to verify (LOW, MEDIUM, HIGH, VERY_LOW)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Maximum number of profiles to verify')
    parser.add_argument('--start-from', type=int, default=1,
                       help='Start from this position (1-based index, useful for resuming)')
    parser.add_argument('--no-auto-save', action='store_true',
                       help='Disable automatic CSV saving after each decision')
    
    args = parser.parse_args()
    
    # Load alumni data
    print(f"Loading alumni data from {args.input}...")
    alumni_list = load_alumni_from_csv(args.input)
    print(f"Loaded {len(alumni_list)} alumni records")
    
    # Get fieldnames from CSV
    with open(args.input, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
    
    if not fieldnames:
        print("Error: Could not read CSV fieldnames")
        sys.exit(1)
    
    # Filter to only profiles with LinkedIn URLs
    filtered_alumni = filter_alumni_with_linkedin(
        alumni_list,
        min_confidence=args.min_confidence,
        limit=args.limit
    )
    
    if not filtered_alumni:
        print("No alumni with LinkedIn URLs found (after filtering).")
        if args.min_confidence:
            print(f"  (Filtered by confidence: {args.min_confidence})")
        sys.exit(0)
    
    # Apply limit before showing count (so count is accurate)
    if args.limit:
        filtered_alumni = filtered_alumni[:args.limit]
    
    print(f"Found {len(filtered_alumni)} alumni with LinkedIn URLs to verify")
    if args.min_confidence:
        print(f"  (Filtered by minimum confidence: {args.min_confidence})")
    if args.limit:
        print(f"  (Limited to: {args.limit})")
    if args.start_from > 1:
        print(f"  (Starting from position: {args.start_from})")
    
    # Determine output file
    output_file = args.output or args.input
    auto_save = not args.no_auto_save
    
    # Start verification (pass both filtered and full alumni lists)
    verify_profiles(
        filtered_alumni,
        alumni_list,  # Full alumni list for updates
        output_file,
        fieldnames,
        auto_save=auto_save,
        start_from=args.start_from
    )


if __name__ == '__main__':
    main()

