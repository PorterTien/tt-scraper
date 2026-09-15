"""
LinkedIn Finder AI Agent
Uses AI and web search to find LinkedIn profiles for alumni
Respects LinkedIn's Terms of Service by using web search instead of scraping
"""

import os
import csv
import sys
import time
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, skip
    pass

# Try to import DuckDuckGo Search (try new package name first)
DDGS_AVAILABLE = False
try:
    # Try new package name first (ddgs)
    try:
        from ddgs import DDGS
        DDGS_AVAILABLE = True
    except ImportError:
        # Fallback to old package name
        try:
            from duckduckgo_search import DDGS
            DDGS_AVAILABLE = True
        except ImportError:
            DDGS_AVAILABLE = False
            print("DuckDuckGo Search not available. Install with: pip install ddgs")
except Exception:
    DDGS_AVAILABLE = False

# Try to import LangChain (optional)
LANGCHAIN_AVAILABLE = False
try:
    from langchain_community.tools import DuckDuckGoSearchRun
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain.tools import DuckDuckGoSearchRun
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        pass

# Import requests and BeautifulSoup for fallback search
try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Try to import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Gemini not installed. Install with: pip install google-generativeai")

# Try to import OpenAI (optional, for comparison)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class AlumniRecord:
    """Alumni record with search capabilities."""
    name: str
    major: str
    grad_year: str
    profile_url: str
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    confidence: Optional[str] = None  # HIGH, MEDIUM, LOW, or None
    company: Optional[str] = None  # Current company
    job_title: Optional[str] = None  # Job title
    location: Optional[str] = None  # Location
    bio: Optional[str] = None  # Bio text


class LinkedInFinderAgent:
    """AI agent to find and verify LinkedIn profiles."""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "gemini", 
                 use_web_search: bool = True, google_api_key: Optional[str] = None,
                 google_cse_id: Optional[str] = None):
        """
        Initialize the LinkedIn finder agent.
        
        Args:
            api_key: API key for the AI provider (Gemini or OpenAI)
            provider: AI provider to use ("gemini" or "openai")
            use_web_search: Whether to use web search (requires DuckDuckGo)
            google_api_key: Google Custom Search API key (optional, for better results)
            google_cse_id: Google Custom Search Engine ID (optional)
        """
        self.provider = provider.lower()
        self.use_web_search = use_web_search
        self.api_key = api_key
        self.google_api_key = google_api_key or os.getenv('GOOGLE_API_KEY')
        self.google_cse_id = google_cse_id or os.getenv('GOOGLE_CSE_ID')
        self.agent_available = False
        self.model = None
        
        # Initialize based on provider
        if self.provider == "gemini":
            if not self.api_key:
                self.api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            
            if not self.api_key:
                print("Warning: Gemini API key not found. Set GEMINI_API_KEY environment variable.")
                print("You can get an API key from: https://makersuite.google.com/app/apikey")
            elif GEMINI_AVAILABLE:
                try:
                    genai.configure(api_key=self.api_key)
                    # Try available Gemini models in order of preference
                    # Note: Model names may vary by API version
                    model_names = [
                        'gemini-2.5-flash',
                        'gemini-pro',  # Most widely available
                        'gemini-1.5-pro',
                        'gemini-1.5-flash',
                        'models/gemini-pro',
                        'models/gemini-1.5-pro',
                    ]
                    
                    model_initialized = False
                    for model_name in model_names:
                        try:
                            self.model = genai.GenerativeModel(model_name)
                            # Test if model works by checking if it's available
                            self.agent_available = True
                            model_initialized = True
                            print(f"✓ Gemini API initialized successfully (using {model_name})")
                            break
                        except Exception as e:
                            continue
                    
                    if not model_initialized:
                        # Last resort: try to list available models
                        try:
                            models = genai.list_models()
                            available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
                            gemini_models = [m for m in available_models if 'gemini' in m.lower()]
                            if gemini_models:
                                model_name = gemini_models[0]
                                self.model = genai.GenerativeModel(model_name)
                                self.agent_available = True
                                print(f"✓ Gemini API initialized successfully (using {model_name})")
                            else:
                                raise Exception("No Gemini models available")
                        except Exception as e:
                            print(f"Error initializing Gemini: {e}")
                            print("  Tried models: " + ", ".join(model_names))
                            self.agent_available = False
                except Exception as e:
                    print(f"Error initializing Gemini: {e}")
                    self.agent_available = False
            else:
                print("Gemini not available. Install with: pip install google-generativeai")
        
        elif self.provider == "openai":
            if not self.api_key:
                self.api_key = os.getenv('OPENAI_API_KEY')
            
            if not self.api_key:
                print("Warning: OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
                print("You can get an API key from: https://platform.openai.com/api-keys")
            elif OPENAI_AVAILABLE:
                try:
                    openai.api_key = self.api_key
                    self.agent_available = True
                    print("✓ OpenAI API initialized successfully")
                except Exception as e:
                    print(f"Error initializing OpenAI: {e}")
                    self.agent_available = False
            else:
                print("OpenAI not available. Install with: pip install openai")
        
        else:
            print(f"Unknown provider: {provider}. Use 'gemini' or 'openai'")
            self.agent_available = False
    
    def normalize_name_variations(self, name: str) -> List[str]:
        """
        Generate multiple name variations for more dynamic searching.
        
        Args:
            name: Full name
            
        Returns:
            List of name variations
        """
        variations = [name]  # Original name
        
        name_parts = name.upper().split()
        if len(name_parts) < 2:
            return variations
        
        # Remove common suffixes (Jr., Sr., III, etc.)
        suffixes = ['JR', 'SR', 'II', 'III', 'IV', 'V']
        base_parts = [p for p in name_parts if p not in suffixes]
        if len(base_parts) >= 2:
            first_name = base_parts[0]
            last_name = base_parts[-1]
            middle_names = base_parts[1:-1] if len(base_parts) > 2 else []
            
            # Full name
            variations.append(f"{first_name} {last_name}")
            
            # First + Last (no middle)
            if middle_names:
                variations.append(f"{first_name} {last_name}")
            
            # First Initial + Last
            if len(first_name) > 1:
                variations.append(f"{first_name[0]} {last_name}")
                variations.append(f"{first_name[0]}{last_name}")
            
            # First + Middle Initial + Last
            if middle_names and len(middle_names) > 0:
                middle_initial = middle_names[0][0] if middle_names[0] else ""
                variations.append(f"{first_name} {middle_initial} {last_name}")
                variations.append(f"{first_name}{middle_initial}{last_name}")
            
            # Handle hyphenated names
            if '-' in first_name:
                parts = first_name.split('-')
                variations.append(f"{' '.join(parts)} {last_name}")
                variations.append(f"{''.join(parts)}{last_name}")
                variations.append(f"{parts[0][0]}{parts[1][0]}{last_name}")  # Both initials
            
            # Handle apostrophes (O'Brien -> OBrien)
            if "'" in last_name:
                variations.append(last_name.replace("'", ""))
                variations.append(f"{first_name} {last_name.replace("'", "")}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for v in variations:
            if v not in seen:
                seen.add(v)
                unique_variations.append(v)
        
        return unique_variations
    
    def generate_search_query(self, alumni: AlumniRecord, search_type: str = "default") -> str:
        """
        Generate an optimized search query for finding LinkedIn profile.
        
        Args:
            alumni: Alumni record
            search_type: Type of search query ("default", "simple", "google", "linkedin", "company", "location")
            
        Returns:
            Search query string
        """
        # Normalize name - use first and last name
        name_parts = alumni.name.upper().split()
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = name_parts[-1]
            full_name = f"{first_name} {last_name}"
        else:
            full_name = alumni.name
        
        if search_type == "simple":
            # Simple query: name + LinkedIn + school
            return f'"{full_name}" LinkedIn UC Berkeley'
        
        elif search_type == "google":
            # Google-friendly query with site filter
            query = f'"{full_name}" site:linkedin.com/in UC Berkeley'
            if alumni.major:
                query += f" {alumni.major}"
            return query
        
        elif search_type == "linkedin":
            # Query optimized for LinkedIn search
            query = f'"{full_name}"'
            if alumni.grad_year:
                year = alumni.grad_year.split('/')[0].strip()
                query += f" {year}"
            query += " UC Berkeley"
            if alumni.major:
                query += f" {alumni.major}"
            return query
        
        elif search_type == "company":
            # Search by name + company
            if alumni.company:
                return f'"{full_name}" "{alumni.company}" LinkedIn'
            return None
        
        elif search_type == "location":
            # Search by name + location
            if alumni.location:
                return f'"{full_name}" "{alumni.location}" LinkedIn UC Berkeley'
            return None
        
        elif search_type == "email_domain":
            # Search by name + email domain (if available)
            if alumni.email and '@' in alumni.email:
                domain = alumni.email.split('@')[1]
                if domain != 'berkeley.edu':  # Skip if it's just berkeley.edu
                    return f'"{full_name}" "{domain}" LinkedIn'
            return None
        
        elif search_type == "job_title":
            # Search by name + job title
            if alumni.job_title:
                return f'"{full_name}" "{alumni.job_title}" LinkedIn UC Berkeley'
            return None
        
        else:  # default
            # Balanced query for general search
            query_parts = [f'"{full_name}"']
            query_parts.append("LinkedIn")
            query_parts.append("UC Berkeley")
            query_parts.append("University of California Berkeley")
            
            if alumni.major:
                query_parts.append(alumni.major)
            
            if alumni.grad_year and alumni.grad_year.strip():
                year = alumni.grad_year.split('/')[0].strip()
                query_parts.append(year)
            
            # Add company if available (can help narrow down)
            if alumni.company:
                query_parts.append(alumni.company)
            
            # Add location if available
            if alumni.location:
                query_parts.append(alumni.location)
            
            return " ".join(query_parts)
    
    def search_with_google_api(self, query: str, api_key: str, search_engine_id: str) -> Optional[str]:
        """
        Search using Google Custom Search API (requires API key).
        
        Args:
            query: Search query
            api_key: Google API key
            search_engine_id: Google Custom Search Engine ID
            
        Returns:
            Search results as string or None
        """
        try:
            import requests
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': search_engine_id,
                'q': query,
                'num': 10
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get('items', []):
                    title = item.get('title', '')
                    link = item.get('link', '')
                    snippet = item.get('snippet', '')
                    results.append(f"{title} | {link} | {snippet}")
                return "\n".join(results)
        except Exception as e:
            print(f"  Google API error: {e}")
        return None
    
    def verify_linkedin_profile_has_berkeley(self, linkedin_url: str, timeout: int = 10) -> Optional[bool]:
        """
        Verify if a LinkedIn profile mentions UC Berkeley by checking the profile page.
        Uses HTTP requests to check public profile information.
        
        Args:
            linkedin_url: LinkedIn profile URL to check
            timeout: Request timeout in seconds
            
        Returns:
            True if profile mentions UC Berkeley
            False if profile does NOT mention UC Berkeley
            None if verification is not possible (LinkedIn blocked request, timeout, etc.)
        """
        if not REQUESTS_AVAILABLE:
            return None  # Can't verify without requests library
        
        try:
            import re
            from urllib.parse import urlparse
            
            # Clean up URL
            if not linkedin_url.startswith('http'):
                linkedin_url = f"https://{linkedin_url}"
            
            # LinkedIn profile URLs should be in format: linkedin.com/in/username
            if 'linkedin.com/in/' not in linkedin_url:
                return None
            
            # Use requests to fetch the profile page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(linkedin_url, headers=headers, timeout=timeout, allow_redirects=True)
            
            # LinkedIn often returns 999 for bot detection or blocks requests
            # Status 999 means we can't verify (LinkedIn is blocking us)
            if response.status_code == 999:
                # Can't verify - LinkedIn is blocking the request
                # Return None to indicate "unknown" (not False, which means "definitely not Berkeley")
                return None
            
            if response.status_code != 200:
                return False
            
            # Get page content
            page_content = response.text
            
            # Check if page is too short (likely a bot detection page or redirect)
            if len(page_content) < 5000:
                # Very short page, likely blocked or redirected
                # But still check if there's any Berkeley mention in what we got
                pass
            
            # Collect all text sources to check
            text_sources = []
            import re
            
            # 1. Check page title
            title_match = re.search(r'<title[^>]*>(.*?)</title>', page_content, re.IGNORECASE | re.DOTALL)
            if title_match:
                text_sources.append(title_match.group(1))
            
            # 2. Check ALL meta tags (not just ones with berkeley in them)
            # LinkedIn puts profile info in og:tags and other meta tags
            all_meta_pattern = r'<meta[^>]*content=["\']([^"\']+)["\']'
            all_meta_matches = re.findall(all_meta_pattern, page_content, re.IGNORECASE)
            text_sources.extend(all_meta_matches)
            
            # 3. Check page content (but remove scripts/styles first)
            content_no_scripts = re.sub(r'<script[^>]*>.*?</script>', '', page_content, flags=re.IGNORECASE | re.DOTALL)
            content_no_scripts = re.sub(r'<style[^>]*>.*?</style>', '', content_no_scripts, flags=re.IGNORECASE | re.DOTALL)
            # Extract visible text (between tags)
            visible_text = re.sub(r'<[^>]+>', ' ', content_no_scripts)
            text_sources.append(visible_text)
            
            # 4. Check JSON-LD structured data
            json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
            json_ld_matches = re.findall(json_ld_pattern, page_content, re.IGNORECASE | re.DOTALL)
            text_sources.extend(json_ld_matches)
            
            # 5. Check data attributes (LinkedIn stores data in data-* attributes)
            data_attr_pattern = r'data-[^=]*=["\']([^"\']+)["\']'
            data_matches = re.findall(data_attr_pattern, page_content, re.IGNORECASE)
            text_sources.extend(data_matches)
            
            # Combine all text sources
            all_text = ' '.join(text_sources).lower()
            page_content_lower = all_text
            
            # Search for UC Berkeley mentions (prioritize stronger matches)
            # Strong patterns (very likely UC Berkeley)
            strong_patterns = [
                r'\buc\s+berkeley\b',
                r'\buniversity\s+of\s+california[,\s]*berkeley\b',
                r'\bucb\b',
                r'\bcal\s+berkeley\b',
                r'\bberkeley\s+university\b',  # Sometimes written backwards
            ]
            
            for pattern in strong_patterns:
                if re.search(pattern, page_content_lower, re.IGNORECASE):
                    return True
            
            # Moderate patterns (need context validation)
            # Look for "berkeley" with education/university context
            berkeley_matches = list(re.finditer(r'\bberkeley\b', page_content_lower, re.IGNORECASE))
            
            if berkeley_matches:
                for match in berkeley_matches:
                    match_start = match.start()
                    match_end = match.end()
                    
                    # Get wider context (500 chars before/after)
                    context_start = max(0, match_start - 500)
                    context_end = min(len(page_content_lower), match_end + 500)
                    context = page_content_lower[context_start:context_end]
                    
                    # Education-related keywords
                    education_keywords = [
                        'education', 'university', 'college', 'school', 
                        'degree', 'bachelor', 'master', 'phd', 'graduated',
                        'student', 'alumni', 'alumnus', 'graduate', 'studied',
                        'attended', 'bs', 'ba', 'ms', 'ma', 'masters', 'bachelors'
                    ]
                    
                    # University/California keywords
                    university_keywords = ['university', 'california', 'uc', 'cal']
                    
                    # Check for education context (use word boundaries to avoid partial matches)
                    has_education = any(re.search(r'\b' + re.escape(keyword) + r'\b', context, re.IGNORECASE) 
                                       for keyword in education_keywords)
                    has_university = any(re.search(r'\b' + re.escape(keyword) + r'\b', context, re.IGNORECASE) 
                                        for keyword in university_keywords)
                    
                    # If we have education context with university/california, it's likely UC Berkeley
                    if has_education and has_university:
                        # Exclude if it's clearly about Berkeley, CA (city)
                        location_indicators = ['city', 'lives in', 'located in', 'area', 'address', 'resides']
                        is_location = any(re.search(r'\b' + re.escape(indicator) + r'\b', context[:300], re.IGNORECASE) 
                                         for indicator in location_indicators)
                        
                        if not is_location:
                            return True
                    
                    # If "berkeley" appears with "university" or "california", it's likely UC Berkeley
                    if has_university:
                        # Make sure it's not just "Berkeley, CA" (city reference)
                        # Check the first part of context (before the match) for location indicators
                        before_context = context[:match_start - context_start]
                        if 'city' not in before_context[:200] and 'location' not in before_context[:200]:
                            return True
            
            return False
            
        except requests.exceptions.Timeout:
            return None  # Unknown - can't verify due to timeout
        except requests.exceptions.RequestException:
            return None  # Unknown - request failed
        except Exception as e:
            # Silently fail - return None to indicate "unknown"
            return None
    
    def extract_name_from_url(self, url: str) -> Optional[str]:
        """Extract name from LinkedIn URL (e.g., linkedin.com/in/john-doe -> john doe)."""
        import re
        match = re.search(r'linkedin\.com/in/([^/?]+)', url)
        if match:
            username = match.group(1)
            # Replace hyphens with spaces and clean up
            name = username.replace('-', ' ').replace('_', ' ')
            return name.lower()
        return None
    
    def name_match_score(self, url: str, target_name: str) -> int:
        """
        Calculate how well a LinkedIn URL matches the target name.
        Returns a score from 0-100, higher is better.
        
        Improved logic:
        - Handles hyphenated names (e.g., "CYRUS-JAN" -> "cyrusjan")
        - Handles combined names (e.g., "cyrusjan" for "CYRUS-JAN BATINO")
        - Requires at least first name match
        - Prefers exact name matches
        """
        if not url or not target_name:
            return 0
        
        # Extract name from URL
        url_name = self.extract_name_from_url(url)
        if not url_name:
            return 0
        
        url_lower = url.lower()
        target_lower = target_name.lower()
        
        # Split target name into parts
        target_parts = target_lower.split()
        url_parts = url_name.split()
        
        # Remove common words
        common_words = {'in', 'the', 'a', 'an', 'and', 'or', 'of', 'to', 'for'}
        target_parts = [p for p in target_parts if p not in common_words]
        url_parts = [p for p in url_parts if p not in common_words]
        
        if not target_parts:
            return 0
        
        # Get first and last name from target
        first_name = target_parts[0] if target_parts else ""
        last_name = target_parts[-1] if len(target_parts) > 1 else ""
        
        # Handle hyphenated first names (e.g., "cyrus-jan" -> try "cyrusjan", "cyrus", "jan")
        first_name_variants = [first_name]
        if '-' in first_name:
            # Add variants: "cyrus-jan" -> ["cyrus-jan", "cyrusjan", "cyrus", "jan"]
            parts = first_name.split('-')
            first_name_variants.extend(parts)
            first_name_variants.append(''.join(parts))  # "cyrusjan"
            first_name_variants.append(''.join([p[0] for p in parts]))  # "cj" (initials)
        
        # Add initial variants (first letter of first name)
        # "nik" -> "n", "cyrus-jan" -> "c"
        if first_name:
            first_initial = first_name[0].lower()
            first_name_variants.append(first_initial)
        
        # If last name is too short (single letter), it's unreliable
        if last_name and len(last_name) == 1:
            last_name = ""  # Don't use single-letter last names
        
        # Extract URL name for pattern matching
        url_name_lower = url_name.lower()
        
        # Check if any first name variant matches
        first_name_match = any(variant in url_lower for variant in first_name_variants if variant)
        
        # Check if last name matches (if we have one)
        last_name_match = last_name in url_lower if last_name and len(last_name) > 1 else False
        
        # Special case: Check for initial + last name pattern (e.g., "nbisht" for "NIK BISHT")
        # Pattern: first_initial + last_name (no separator or with hyphen/underscore)
        initial_last_match = False
        if first_name and last_name and len(last_name) > 1:
            first_initial = first_name[0].lower()
            # Try patterns: "n" + "bisht" = "nbisht", "n-bisht", "n_bisht"
            patterns_to_check = [
                first_initial + last_name,  # "nbisht"
                first_initial + '-' + last_name,  # "n-bisht"
                first_initial + '_' + last_name,  # "n_bisht"
            ]
            for pattern in patterns_to_check:
                if pattern in url_lower:
                    initial_last_match = True
                    break
        
        # Calculate score
        score = 0
        
        # Base score: first name match OR initial + last name match
        if first_name_match:
            score += 40
            # Bonus if it's the full first name (not just a part)
            if first_name in url_lower or ''.join(first_name.split('-')) in url_lower:
                score += 10  # Extra bonus for full first name
        elif initial_last_match:
            # Initial + last name pattern (e.g., "nbisht" for "NIK BISHT")
            # This is a valid pattern, give it a base score
            score += 35
            first_name_match = True  # Treat as match for later logic
        else:
            # No first name match and no initial pattern = very low score
            # But if last name matches strongly, might still be valid
            if last_name_match and last_name in url_name_lower:
                # Last name matches and URL is short (might be abbreviated)
                if len(url_name_lower.replace('-', '').replace('_', '')) <= len(last_name) + 3:
                    # URL is roughly last name + a few chars (could be initial)
                    score = 30  # Give it a chance
                    first_name_match = True  # Treat as potential match
                else:
                    return 5
            else:
                return 5
        
        # Last name match (important)
        if last_name:
            if last_name_match:
                if initial_last_match:
                    # Initial + last name pattern (e.g., "nbisht") - this is a strong indicator
                    score += 45  # Strong match for initial + last name
                else:
                    score += 50  # Strong match with both names
            else:
                # First name matches but last name doesn't - might be wrong person
                # But for hyphenated names combined (e.g., "cyrusjan"), this might be OK
                if '-' in first_name and ''.join(first_name.split('-')) in url_lower:
                    # Hyphenated name combined in URL (e.g., "cyrus-jan" -> "cyrusjan")
                    # This is common, so give it a moderate score
                    score = 50  # Moderate score for combined hyphenated names
                elif initial_last_match:
                    # Initial pattern detected but last name check failed (shouldn't happen, but just in case)
                    score = 40  # Moderate score
                else:
                    score = 25  # Lower score if no last name match
        else:
            # No last name to match - give moderate score
            score = 30
        
        # Bonus: exact name pattern match (e.g., "justin-borja" for "JUSTIN BORJA")
        if first_name and last_name:
            # Try various patterns
            patterns = [
                f"{first_name}-{last_name}",  # "cyrus-jan-batino"
                f"{''.join(first_name.split('-'))}-{last_name}",  # "cyrusjan-batino"
                f"{''.join(first_name.split('-'))}{last_name}",  # "cyrusjanbatino"
                f"{first_name}{last_name}",  # "cyrus-janbatino" (unlikely but possible)
            ]
            for pattern in patterns:
                if pattern in url_lower:
                    score = 100  # Perfect match
                    return score
        
        # Special case: hyphenated first name combined (e.g., "cyrus-jan" -> "cyrusjan")
        if '-' in first_name:
            combined_first = ''.join(first_name.split('-'))
            if combined_first in url_lower:
                # This is a good match (e.g., "cyrusjan" for "CYRUS-JAN")
                if last_name_match:
                    score = 90  # Very good match
                else:
                    score = 60  # Good match even without last name (common pattern)
        
        # Special case: initial + last name (e.g., "nbisht" for "NIK BISHT")
        if initial_last_match and last_name_match:
            # This is a valid and common LinkedIn pattern
            score = max(score, 75)  # Good confidence for initial + last name pattern
        
        # Bonus: all name parts match
        target_parts_set = set(target_parts)
        url_parts_set = set(url_parts)
        matching_parts = target_parts_set.intersection(url_parts_set)
        
        if len(matching_parts) == len(target_parts_set) and len(target_parts_set) > 1:
            score = min(score + 10, 100)  # Bonus for all parts matching
        
        # Check if URL contains all characters from the name (for combined names)
        if first_name and last_name:
            # Remove hyphens and spaces, check if URL contains the combined name
            name_chars = ''.join(target_parts).replace('-', '')
            url_chars = url_name.replace('-', '').replace('_', '')
            
            # Check if all significant characters from name are in URL
            if len(name_chars) > 0 and name_chars[:5] in url_chars:  # First 5 chars match
                if last_name_match or len(url_chars) <= len(name_chars) + 3:
                    score = max(score, 70)  # Good match for combined names
        
        # Penalty: URL has many extra parts (might be wrong person)
        if len(url_parts) > len(target_parts) * 3:
            score *= 0.6  # Significant penalty
        
        return min(int(score), 100)
    
    def filter_linkedin_profiles_by_berkeley(self, linkedin_urls: List[str], max_check: int = 5, skip_verification: bool = False) -> List[str]:
        """
        Filter LinkedIn profile URLs. Since LinkedIn blocks verification, we skip it
        and rely on name matching instead.
        
        Args:
            linkedin_urls: List of LinkedIn profile URLs to check
            max_check: Maximum number of profiles to check (for performance)
            skip_verification: If True, skip LinkedIn verification (faster)
            
        Returns:
            List of LinkedIn URLs (since we can't verify, return all for name matching)
        """
        if not linkedin_urls:
            return []
        
        # LinkedIn blocks all verification attempts, so skip it for speed
        if skip_verification:
            return linkedin_urls[:max_check]
        
        # Legacy verification code (usually skipped)
        berkeley_profiles = []
        unverifiable_profiles = []
        
        for url in linkedin_urls[:max_check]:
            result = self.verify_linkedin_profile_has_berkeley(url)
            
            if result is True:
                berkeley_profiles.append(url)
                print(f"      ✓ Verified UC Berkeley: {url}")
            elif result is False:
                print(f"      ✗ No UC Berkeley mention: {url}")
            else:
                unverifiable_profiles.append(url)
                print(f"      ⚠️  Can't verify (LinkedIn blocked/private): {url}")
            
            time.sleep(0.3)  # Reduced delay
        
        if berkeley_profiles:
            return berkeley_profiles
        
        # Return unverified profiles for name matching
        return unverifiable_profiles if unverifiable_profiles else linkedin_urls[:max_check]
    
    def verify_match_with_context(self, url: str, alumni: AlumniRecord, search_results: List[Dict]) -> Tuple[int, str]:
        """
        Verify if a LinkedIn URL matches the alumni by analyzing search result context.
        Checks for UC Berkeley mentions, major, graduation year, and name in context.
        
        Returns:
            Tuple of (confidence_score, reason)
            confidence_score: 0-100 (higher = more confident)
            reason: Explanation of the confidence level
        """
        import re
        
        # Start with name match score
        name_score = self.name_match_score(url, alumni.name)
        
        if name_score < 30:
            return (name_score, "Poor name match")
        
        # Look for this URL in search results and analyze context
        context_score = 0
        context_reasons = []
        url_username = url.split('/')[-1].lower() if '/' in url else ""
        
        for result in search_results:
            title = result.get('title', '').lower()
            body = result.get('body', '').lower()
            href = result.get('href', '').lower()
            
            # Check if this result is about our URL
            # Match by URL or by LinkedIn username
            if url.lower() not in href and url_username not in href:
                # Also check if the username appears in title/body
                if url_username not in title and url_username not in body:
                    continue
            
            # Check for UC Berkeley mentions (strong signal)
            berkeley_keywords = ['uc berkeley', 'university of california berkeley', 'cal berkeley', 'berkeley']
            if any(keyword in title or keyword in body for keyword in berkeley_keywords):
                context_score += 30
                context_reasons.append("UC Berkeley mentioned")
            
            # Check for major match
            if alumni.major:
                major_words = alumni.major.lower().split()
                # Remove common words
                major_words = [w for w in major_words if w not in ['and', 'of', 'the', 'engineering', 'science', 'mechanical', 'electrical', 'computer', 'civil', 'chemical']]
                # Keep meaningful words (3+ chars)
                major_words = [w for w in major_words if len(w) > 3]
                if major_words and any(word in title or word in body for word in major_words):
                    context_score += 20
                    context_reasons.append(f"Major mentioned")
            
            # Check for graduation year (strong signal)
            if alumni.grad_year:
                # Extract year from grad_year (handle formats like "2015" or "2015 / 2016")
                year_match = re.search(r'\b(19|20)\d{2}\b', str(alumni.grad_year))
                if year_match:
                    year = year_match.group(0)
                    if year in title or year in body:
                        context_score += 15
                        context_reasons.append(f"Year {year} mentioned")
            
            # Check if Theta Tau is mentioned (strong signal for correct person)
            theta_tau_keywords = ['theta tau', 'thetatau', 'theta tau professional', 'engineering fraternity']
            for keyword in theta_tau_keywords:
                if keyword in title or keyword in body:
                    context_score += 20  # Strong signal - this is a Theta Tau member
                    context_reasons.append("Theta Tau mentioned")
                    break  # Only count once
            
            # Check if name appears in context
            name_parts = alumni.name.lower().split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = name_parts[-1]
                # Both names in context is a strong signal
                if first_name in title or first_name in body:
                    if last_name in title or last_name in body:
                        context_score += 10
                        context_reasons.append("Name in context")
        
        # Combine name score and context score
        # Name score is base (max 100), context adds verification (max +30)
        # But we cap total at 100
        total_score = min(name_score + min(context_score, 30), 100)
        
        # Boost score if we have multiple context signals
        if len(context_reasons) >= 3:
            total_score = min(total_score + 10, 100)
            context_reasons.append("Multiple signals")
        
        # Determine confidence level
        if total_score >= 80:
            confidence = "HIGH"
        elif total_score >= 60:
            confidence = "MEDIUM"
        elif total_score >= 40:
            confidence = "LOW"
        else:
            confidence = "VERY_LOW"
        
        reason = f"{confidence} confidence"
        if context_reasons:
            reason += f" ({', '.join(set(context_reasons))})"  # Remove duplicates
        else:
            reason += " (name match only)"
        
        return (total_score, reason)
    
    def search_linkedin_profile(self, alumni: AlumniRecord) -> Optional[Union[str, Tuple[str, int, str]]]:
        """
        Search for LinkedIn profile using web search with context-aware verification.
        Analyzes search result snippets to verify matches.
        
        Args:
            alumni: Alumni record
            
        Returns:
            Tuple of (url, confidence_score, reason) if found, None otherwise
        """
        if not self.agent_available:
            return None
        
        # Generate multiple search query variations - try different strategies
        queries = []
        
        # Core queries
        core_queries = [
            self.generate_search_query(alumni, "default"),  # Most specific first
            self.generate_search_query(alumni, "linkedin"),
            self.generate_search_query(alumni, "simple"),
            # Additional variations
            f'"{alumni.name}" LinkedIn',  # Just name + LinkedIn
            f'"{alumni.name}" UC Berkeley LinkedIn',  # Name + school + LinkedIn
        ]
        queries.extend([q for q in core_queries if q])  # Filter out None values
        
        # Name variation queries (try different name formats)
        name_variations = self.normalize_name_variations(alumni.name)
        for name_var in name_variations[:3]:  # Limit to top 3 variations to avoid too many queries
            if name_var.upper() != alumni.name.upper():
                queries.append(f'"{name_var}" LinkedIn UC Berkeley')
        
        # Context-based queries (use additional data if available)
        context_queries = []
        
        # Company-based search
        company_query = self.generate_search_query(alumni, "company")
        if company_query:
            context_queries.append(company_query)
        
        # Location-based search
        location_query = self.generate_search_query(alumni, "location")
        if location_query:
            context_queries.append(location_query)
        
        # Job title-based search
        job_title_query = self.generate_search_query(alumni, "job_title")
        if job_title_query:
            context_queries.append(job_title_query)
        
        # Email domain-based search (if email is available and not berkeley.edu)
        email_domain_query = self.generate_search_query(alumni, "email_domain")
        if email_domain_query:
            context_queries.append(email_domain_query)
        
        queries.extend(context_queries)
        
        # Handle hyphenated names - try variants
        name_parts = alumni.name.upper().split()
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = name_parts[-1]
            
            # If first name has hyphen, try variations
            if '-' in first_name:
                # Try without hyphen: "CYRUS-JAN" -> "CYRUS JAN"
                first_name_no_hyphen = first_name.replace('-', ' ')
                queries.append(f'"{first_name_no_hyphen} {last_name}" LinkedIn UC Berkeley')
                # Try combined: "CYRUS-JAN" -> "CYRUSJAN"
                first_name_combined = first_name.replace('-', '')
                queries.append(f'"{first_name_combined} {last_name}" LinkedIn UC Berkeley')
                queries.append(f'"{first_name_combined}{last_name}" LinkedIn UC Berkeley')  # No space
            
            # Try initial + last name pattern (e.g., "N BISHT" or "N Bisht" for "NIK BISHT")
            # This is a common LinkedIn pattern where people use first initial + last name
            first_initial = first_name[0] if first_name else ""
            if first_initial and len(first_name) > 2:  # Only if first name is longer than 2 chars
                # Try patterns: "N BISHT LinkedIn", "N Bisht LinkedIn"
                queries.append(f'"{first_initial} {last_name}" LinkedIn UC Berkeley')
                queries.append(f'"{first_initial}{last_name}" LinkedIn UC Berkeley')  # No space
                queries.append(f'site:linkedin.com/in/ "{first_initial}{last_name}" UC Berkeley')  # Direct LinkedIn search
        
        # Add queries with major if available
        if alumni.major:
            queries.append(f'"{alumni.name}" {alumni.major} LinkedIn UC Berkeley')
            queries.append(f'"{alumni.name}" {alumni.major} UC Berkeley')
            
            # With name variants if hyphenated
            if len(name_parts) >= 2 and '-' in name_parts[0]:
                first_name = name_parts[0]
                last_name = name_parts[-1]
                first_name_combined = first_name.replace('-', '')
                queries.append(f'"{first_name_combined} {last_name}" {alumni.major} LinkedIn UC Berkeley')
        
        # Add queries with graduation year if available
        if alumni.grad_year:
            year = alumni.grad_year.split('/')[0].strip()
            if year and year.isdigit():
                queries.append(f'"{alumni.name}" {year} LinkedIn UC Berkeley')
                queries.append(f'"{alumni.name}" UC Berkeley {year}')
                
                # With name variants if hyphenated
                if len(name_parts) >= 2 and '-' in name_parts[0]:
                    first_name = name_parts[0]
                    last_name = name_parts[-1]
                    first_name_combined = first_name.replace('-', '')
                    queries.append(f'"{first_name_combined} {last_name}" {year} LinkedIn UC Berkeley')
        
        all_linkedin_urls = []  # Collect URLs from all queries
        all_search_results = []  # Collect all search results for context analysis
        
        # Try each query until we find good matches
        # Try more queries to increase chances of finding LinkedIn
        max_queries = 7  # Increased from 5
        for i, search_query in enumerate(queries[:max_queries], 1):
            print(f"  Search {i}/{min(len(queries), max_queries)}: {search_query[:70]}...")
            
            # Early exit if we already have a high-confidence match from previous queries
            if all_linkedin_urls and i > 1:
                # Check if we have any high-confidence matches already
                temp_verified = []
                for url in all_linkedin_urls[:3]:  # Check top 3
                    score, reason = self.verify_match_with_context(url, alumni, all_search_results)
                    if score >= 70:
                        print(f"  ✓ Found high-confidence match, stopping search")
                        return (url, score, reason)
            
            try:
                # Try DuckDuckGo Search
                if DDGS_AVAILABLE:
                    try:
                        import re
                        from ddgs import DDGS as DDGS_New
                        with DDGS_New() as ddgs:
                            results = list(ddgs.text(search_query, max_results=15))  # Increased from 10
                    except (ImportError, AttributeError):
                        from duckduckgo_search import DDGS as DDGS_Old
                        with DDGS_Old() as ddgs:
                            results = list(ddgs.text(search_query, max_results=15))  # Increased from 10
                    
                    if results:
                        print(f"    ✓ Found {len(results)} results")
                        all_search_results.extend(results)
                        
                        linkedin_urls_from_query = []
                        
                        for r in results:
                            href = r.get('href', '')
                            title = r.get('title', '')
                            body = r.get('body', '')
                            
                            # Extract LinkedIn URLs from href
                            if href and 'linkedin.com/in/' in href:
                                match = re.search(r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9\-_]+)', href)
                                if match:
                                    clean_url = f"https://www.linkedin.com/in/{match.group(1)}"
                                    if clean_url not in all_linkedin_urls:
                                        all_linkedin_urls.append(clean_url)
                                        linkedin_urls_from_query.append((clean_url, r))
                                        print(f"      → {clean_url}")
                            
                            # Also check text for LinkedIn URLs (more thorough)
                            text = f"{title} {body}"
                            text_lower = text.lower()
                            
                            # Look for LinkedIn URLs in various formats (more dynamic patterns)
                            linkedin_patterns = [
                                r'linkedin\.com/in/([a-zA-Z0-9\-_]+)',  # Standard format
                                r'linkedin\.com/in/([a-zA-Z0-9\-_]+)/?',  # With optional trailing slash
                                r'www\.linkedin\.com/in/([a-zA-Z0-9\-_]+)',  # With www
                                r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9\-_]+)',  # Full URL
                                r'linkedin\.com/in/([a-zA-Z0-9\-_]+)/[^/]*',  # With additional path
                                r'linkedin\.com/profile/view\?id=([a-zA-Z0-9\-_]+)',  # Old profile format
                                r'linkedin\.com/pub/([a-zA-Z0-9\-_/]+)',  # Old pub format
                                r'\/in\/([a-zA-Z0-9\-_]+)',  # Just /in/username
                            ]
                            
                            for pattern in linkedin_patterns:
                                url_matches = re.findall(pattern, text, re.IGNORECASE)
                                for username in url_matches:
                                    clean_url = f"https://www.linkedin.com/in/{username}"
                                    if clean_url not in all_linkedin_urls:
                                        all_linkedin_urls.append(clean_url)
                                        linkedin_urls_from_query.append((clean_url, r))
                                        print(f"      → Found in text: {clean_url}")
                            
                            # Also check if result mentions LinkedIn but URL not in standard format
                            # Sometimes LinkedIn URLs are mentioned in text without full URL
                            if 'linkedin' in text_lower and 'linkedin.com/in/' not in text_lower:
                                # Try to extract from context - look for "linkedin.com/in/username" patterns
                                # or "view profile" links
                                pass  # This is handled by AI extraction below
                        
                        # If we found LinkedIn URLs, verify them with context
                        if linkedin_urls_from_query:
                            verified_urls = []
                            
                            for url, result_data in linkedin_urls_from_query:
                                # Verify with context from search results
                                confidence_score, reason = self.verify_match_with_context(
                                    url, alumni, [result_data]
                                )
                                
                                # Lower threshold to catch more matches (we'll filter later)
                                if confidence_score >= 30:  # Lowered from 40
                                    verified_urls.append((confidence_score, url, reason))
                                    print(f"      ✓ {url} - {reason} (score: {confidence_score})")
                                else:
                                    print(f"      ✗ {url} - {reason} (score: {confidence_score}) - REJECTED")
                            
                            # Sort by confidence score
                            verified_urls.sort(reverse=True, key=lambda x: x[0])
                            
                            if verified_urls:
                                best_score, best_url, best_reason = verified_urls[0]
                                
                                # High confidence: return immediately with confidence info
                                if best_score >= 70:
                                    print(f"    ✓ HIGH confidence match: {best_url}")
                                    return (best_url, best_score, best_reason)
                                
                                # Medium confidence: return if it's the only good match
                                if best_score >= 50 and len([v for v in verified_urls if v[0] >= 50]) == 1:
                                    print(f"    ✓ MEDIUM confidence match: {best_url}")
                                    return (best_url, best_score, best_reason)
                                
                                # If we have a decent match and it's the only one, return it
                                if best_score >= 40 and len(verified_urls) == 1:
                                    print(f"    ✓ Single match found: {best_url}")
                                    return (best_url, best_score, best_reason)
                                
                                # Continue searching for better matches
                                print(f"    ℹ Best match: {best_url} (score: {best_score}) - continuing search...")
                            
                    else:
                        print(f"    ✗ No results")
                    
                    # If no LinkedIn URLs found directly, use AI to extract from search results
                    # This catches cases where LinkedIn is mentioned but URL isn't in standard format
                    if not linkedin_urls_from_query and results and self.agent_available:
                        # Only use AI if search results mention LinkedIn or the person's name
                        has_linkedin_mention = any(
                            'linkedin' in (r.get('title', '') + r.get('body', '')).lower() 
                            for r in results
                        )
                        has_name_mention = any(
                            alumni.name.lower() in (r.get('title', '') + r.get('body', '')).lower()
                            for r in results
                        )
                        
                        if has_linkedin_mention or has_name_mention:
                            print(f"    ℹ No direct URLs found, using AI to extract from {len(results)} results...")
                            linkedin_url = self.extract_linkedin_with_ai(alumni, results)
                            if linkedin_url:
                                if linkedin_url not in all_linkedin_urls:
                                    all_linkedin_urls.append(linkedin_url)
                                    # Create a mock result for context verification
                                    mock_result = {'title': 'AI extracted', 'body': 'Extracted from search results', 'href': linkedin_url}
                                    linkedin_urls_from_query.append((linkedin_url, mock_result))
                                    print(f"      ✓ AI found: {linkedin_url}")
                                    # Verify it immediately
                                    confidence_score, reason = self.verify_match_with_context(
                                        linkedin_url, alumni, results
                                    )
                                    if confidence_score >= 30:
                                        print(f"      ✓ Verified (score: {confidence_score}): {reason}")
                                        if confidence_score >= 50:
                                            return (linkedin_url, confidence_score, reason)
                
            except Exception as e:
                print(f"    Error: {e}")
                continue
        
        # After trying all queries, verify all URLs with full context
        if all_linkedin_urls and all_search_results:
            print(f"  ℹ Final verification of {len(all_linkedin_urls)} LinkedIn URL(s)...")
            
            verified_urls = []
            for url in all_linkedin_urls:
                confidence_score, reason = self.verify_match_with_context(
                    url, alumni, all_search_results
                )
                
                # Lower threshold to catch more matches
                if confidence_score >= 30:  # Lowered from 40
                    verified_urls.append((confidence_score, url, reason))
                    print(f"    {confidence_score:3d} - {url}")
                    print(f"        {reason}")
            
            if verified_urls:
                # Sort by confidence
                verified_urls.sort(reverse=True, key=lambda x: x[0])
                best_score, best_url, best_reason = verified_urls[0]
                
                # Return best match if it meets threshold (lowered to catch more)
                if best_score >= 30:  # Lowered from 40
                    confidence_level = "HIGH" if best_score >= 70 else "MEDIUM" if best_score >= 50 else "LOW"
                    print(f"  ✓ {confidence_level} confidence: {best_url}")
                    if best_score < 70:
                        print(f"  ⚠️  Manual verification recommended")
                    return (best_url, best_score, best_reason)
        
        # No good matches found - try AI extraction from all search results as last resort
        if all_search_results and self.agent_available and not all_linkedin_urls:
            print(f"  ℹ Last resort: Using AI to extract LinkedIn from all search results...")
            linkedin_url = self.extract_linkedin_with_ai(alumni, all_search_results)
            if linkedin_url:
                # Verify it
                confidence_score, reason = self.verify_match_with_context(
                    linkedin_url, alumni, all_search_results
                )
                if confidence_score >= 30:  # Lower threshold for AI-extracted URLs
                    print(f"  ✓ AI found LinkedIn: {linkedin_url} (score: {confidence_score})")
                    return (linkedin_url, confidence_score, reason)
        
        # No good matches found
        print(f"  ✗ No LinkedIn profiles found with sufficient confidence")
        return None
    
    def extract_linkedin_with_ai(self, alumni: AlumniRecord, search_results: List[Dict]) -> Optional[str]:
        """
        Use AI to extract LinkedIn URL from search results when direct extraction fails.
        
        Args:
            alumni: Alumni record
            search_results: List of search result dictionaries
            
        Returns:
            LinkedIn URL if found, None otherwise
        """
        if not self.agent_available or not self.model:
            return None
        
        try:
            import re
            
            # Format search results for AI
            results_text = []
            for i, result in enumerate(search_results[:15], 1):  # Limit to 15 results
                title = result.get('title', '')
                body = result.get('body', '')
                href = result.get('href', '')
                # Truncate long text to avoid token limits
                title = title[:200] if len(title) > 200 else title
                body = body[:300] if len(body) > 300 else body
                results_text.append(f"{i}. {title}\n   {body}\n   {href}")
            
            search_results_str = "\n\n".join(results_text)
            
            # Create prompt for AI
            prompt = f"""Find the LinkedIn profile URL for this person in the search results below.

PERSON TO FIND:
- Name: {alumni.name}
- Major: {alumni.major}
- Graduation Year: {alumni.grad_year}
- School: UC Berkeley (University of California, Berkeley)

SEARCH RESULTS:
{search_results_str}

TASK: Extract the LinkedIn profile URL (linkedin.com/in/username) for {alumni.name} from the search results.

INSTRUCTIONS:
1. Look for LinkedIn profile URLs in the search results
2. The URL should match the person's name: {alumni.name}
3. The profile should be from UC Berkeley
4. Return ONLY the LinkedIn URL (e.g., https://www.linkedin.com/in/username)
5. If no LinkedIn URL is found, return "NOT_FOUND"

IMPORTANT: Return ONLY the URL, nothing else."""

            # Use AI to extract
            if self.provider == "gemini" and self.model:
                response = self.model.generate_content(prompt)
                result = response.text.strip()
            elif self.provider == "openai" and OPENAI_AVAILABLE:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100,
                    temperature=0
                )
                result = response.choices[0].message.content.strip()
            else:
                return None
            
            # Extract LinkedIn URL from AI response
            if result and result.upper() != "NOT_FOUND":
                # Try to extract URL from response
                linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9\-_]+)'
                match = re.search(linkedin_pattern, result, re.IGNORECASE)
                if match:
                    return f"https://www.linkedin.com/in/{match.group(1)}"
                
                # Try without https
                match = re.search(r'linkedin\.com/in/([a-zA-Z0-9\-_]+)', result, re.IGNORECASE)
                if match:
                    return f"https://www.linkedin.com/in/{match.group(1)}"
            
            return None
            
        except Exception as e:
            print(f"    AI extraction error: {e}")
            return None
    
    def verify_linkedin_profile(self, linkedin_url: str, alumni: AlumniRecord) -> bool:
        """
        Use AI to verify if a LinkedIn profile matches the alumni record.
        
        Args:
            linkedin_url: LinkedIn profile URL
            alumni: Alumni record
            
        Returns:
            True if profile matches, False otherwise
        """
        if not self.agent_available:
            return False
        
        try:
            # Note: We can't actually access LinkedIn profile content due to ToS
            # This is a placeholder that would need the profile content
            # In practice, you'd need to manually verify or use LinkedIn's official API
            
            prompt = f"""Verify if this LinkedIn profile matches the alumni:
LinkedIn URL: {linkedin_url}
Alumni Name: {alumni.name}
Alumni Major: {alumni.major}
Alumni Graduation Year: {alumni.grad_year}
Alumni School: UC Berkeley

Based on the LinkedIn profile information, does this profile match?
Return "MATCH" or "NO_MATCH"."""
            
            # Use Gemini or OpenAI based on provider
            if self.provider == "gemini" and self.model:
                response = self.model.generate_content(prompt)
                result = response.text.strip()
                return "MATCH" in result.upper()
            elif self.provider == "openai" and OPENAI_AVAILABLE:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=50,
                    temperature=0
                )
                result = response.choices[0].message.content.strip()
                return "MATCH" in result.upper()
                
        except Exception as e:
            print(f"  Error verifying profile: {e}")
        
        return False
    
    def find_linkedin_profiles(self, alumni_list: List[AlumniRecord], 
                              limit: Optional[int] = None,
                              delay: float = 1.0) -> List[AlumniRecord]:
        """
        Find LinkedIn profiles for a list of alumni.
        
        Args:
            alumni_list: List of alumni records
            limit: Maximum number of alumni to process
            delay: Delay between searches (seconds)
            
        Returns:
            List of alumni records with LinkedIn URLs
        """
        if not self.agent_available:
            print("AI agent not available. Please install requirements and set API key.")
            return alumni_list
        
        processed = 0
        found_count = 0
        
        for alumni in alumni_list:
            # Skip if already has LinkedIn
            if alumni.linkedin_url:
                continue
            
            # Check if LinkedIn was found in enriched profiles (more reliable)
            # This happens if enrich_profiles.py already found it
            if not alumni.linkedin_url and hasattr(alumni, 'profile_url') and alumni.profile_url:
                # Could check enriched CSV here, but for now we'll just search
                pass
            
            if limit and processed >= limit:
                break
            
            print(f"\n[{processed + 1}/{len(alumni_list)}] Processing: {alumni.name}")
            
            # Search for LinkedIn profile
            result = self.search_linkedin_profile(alumni)
            
            if isinstance(result, tuple):
                # New format: (url, confidence_score, reason)
                linkedin_url, confidence_score, reason = result
                alumni.linkedin_url = linkedin_url
                
                # Set confidence level
                if confidence_score >= 80:
                    alumni.confidence = "HIGH"
                elif confidence_score >= 60:
                    alumni.confidence = "MEDIUM"
                elif confidence_score >= 40:
                    alumni.confidence = "LOW"
                else:
                    alumni.confidence = "VERY_LOW"
                
                print(f"  ✓ Found LinkedIn: {linkedin_url}")
                print(f"  Confidence: {alumni.confidence} (score: {confidence_score}) - {reason}")
                found_count += 1
            elif result:
                # Legacy format: just URL
                linkedin_url = result
                alumni.linkedin_url = linkedin_url
                alumni.confidence = "MEDIUM"  # Default if no confidence score
                print(f"  ✓ Found LinkedIn: {linkedin_url}")
                found_count += 1
            else:
                print(f"  ✗ LinkedIn not found")
            
            processed += 1
            
            # Rate limiting
            if delay > 0 and processed < len(alumni_list):
                time.sleep(delay)
        
        print(f"\n{'=' * 50}")
        print(f"Processed: {processed} alumni")
        print(f"Found LinkedIn: {found_count} profiles")
        if processed > 0:
            print(f"Success rate: {found_count/processed*100:.1f}%")
        
        # Print confidence summary
        confidence_counts = {}
        for alumni in alumni_list:
            if alumni.confidence:
                confidence_counts[alumni.confidence] = confidence_counts.get(alumni.confidence, 0) + 1
        
        if confidence_counts:
            print(f"\nConfidence Summary:")
            for level in ['HIGH', 'MEDIUM', 'LOW', 'VERY_LOW']:
                count = confidence_counts.get(level, 0)
                if count > 0:
                    print(f"  {level}: {count}")
        
        return alumni_list


def load_alumni_from_csv(filename: str) -> List[AlumniRecord]:
    """Load alumni records from CSV file."""
    alumni_list = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                alumni = AlumniRecord(
                    name=row.get('Name', ''),
                    major=row.get('Major', ''),
                    grad_year=row.get('Grad_Year', ''),
                    profile_url=row.get('Profile_URL', ''),
                    linkedin_url=row.get('LinkedIn_URL', '').strip() or None,
                    email=row.get('Email', '').strip() or None,
                    confidence=row.get('Confidence', '').strip() or None,
                    company=row.get('Current_Company', '').strip() or None,
                    job_title=row.get('Job_Title', '').strip() or None,
                    location=row.get('Location', '').strip() or None,
                    bio=row.get('Bio', '').strip() or None
                )
                alumni_list.append(alumni)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    
    return alumni_list


def save_alumni_to_csv(alumni_list: List[AlumniRecord], filename: str):
    """Save alumni records to CSV file."""
    fieldnames = ['Name', 'Major', 'Grad_Year', 'Profile_URL', 
                 'LinkedIn_URL', 'Email', 'Confidence']
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for alumni in alumni_list:
                writer.writerow({
                    'Name': alumni.name,
                    'Major': alumni.major,
                    'Grad_Year': alumni.grad_year,
                    'Profile_URL': alumni.profile_url,
                    'LinkedIn_URL': alumni.linkedin_url or '',
                    'Email': alumni.email or '',
                    'Confidence': alumni.confidence or ''
                })
        
        print(f"Saved {len(alumni_list)} records to {filename}")
        
        # Print confidence statistics
        confidence_counts = {}
        for alumni in alumni_list:
            if alumni.confidence:
                confidence_counts[alumni.confidence] = confidence_counts.get(alumni.confidence, 0) + 1
        
        if confidence_counts:
            print(f"\nConfidence breakdown:")
            for level in ['HIGH', 'MEDIUM', 'LOW', 'VERY_LOW']:
                if level in confidence_counts:
                    print(f"  {level}: {confidence_counts[level]}")
    except Exception as e:
        print(f"Error saving CSV: {e}")
        sys.exit(1)


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI agent to find LinkedIn profiles')
    parser.add_argument('--input', default='alumni_missing_linkedin.csv',
                       help='Input CSV file with alumni data')
    parser.add_argument('--output', default='alumni_data_ai_enriched.csv',
                       help='Output CSV file')
    parser.add_argument('--limit', type=int, default=None,
                       help='Maximum number of alumni to process')
    parser.add_argument('--delay', type=float, default=2.0,
                       help='Delay between searches (seconds)')
    parser.add_argument('--api-key', type=str, default=None,
                       help='API key for AI provider (or set GEMINI_API_KEY/OPENAI_API_KEY env var)')
    parser.add_argument('--provider', type=str, default='gemini', choices=['gemini', 'openai'],
                       help='AI provider to use: gemini (default) or openai')
    parser.add_argument('--no-web-search', action='store_true',
                       help='Disable web search (will only generate queries)')
    
    args = parser.parse_args()
    
    # Check if API key is available based on provider
    if args.provider == "gemini":
        api_key = args.api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("Error: Gemini API key required.")
            print("Set GEMINI_API_KEY environment variable or use --api-key option")
            print("Get your API key from: https://makersuite.google.com/app/apikey")
            sys.exit(1)
    else:
        api_key = args.api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("Error: OpenAI API key required.")
            print("Set OPENAI_API_KEY environment variable or use --api-key option")
            print("Get your API key from: https://platform.openai.com/api-keys")
            sys.exit(1)
    
    # Load alumni data
    print(f"Loading alumni data from {args.input}...")
    alumni_list = load_alumni_from_csv(args.input)
    
    # Filter to only those missing LinkedIn
    missing_linkedin = [a for a in alumni_list if not a.linkedin_url]
    print(f"Found {len(missing_linkedin)} alumni missing LinkedIn profiles")
    
    if not missing_linkedin:
        print("All alumni have LinkedIn profiles!")
        return
    
    # Initialize AI agent
    print(f"\nInitializing AI agent with {args.provider}...")
    agent = LinkedInFinderAgent(
        api_key=api_key,
        provider=args.provider,
        use_web_search=not args.no_web_search
    )
    
    if not agent.agent_available:
        print("AI agent not available. Please check your API key and install requirements.")
        sys.exit(1)
    
    # Find LinkedIn profiles
    print(f"\nStarting LinkedIn profile search...")
    print(f"Processing up to {args.limit or len(missing_linkedin)} alumni")
    print(f"Delay between searches: {args.delay} seconds")
    print("-" * 50)
    
    # Process alumni
    processed_alumni = agent.find_linkedin_profiles(
        missing_linkedin,
        limit=args.limit,
        delay=args.delay
    )
    
    # Update the full alumni list with found LinkedIn URLs
    linkedin_map = {a.name: a.linkedin_url for a in processed_alumni if a.linkedin_url}
    for alumni in alumni_list:
        if alumni.name in linkedin_map:
            alumni.linkedin_url = linkedin_map[alumni.name]
    
    # Save results
    print(f"\nSaving results to {args.output}...")
    save_alumni_to_csv(alumni_list, args.output)
    
    print("\nDone! Review the results and verify LinkedIn URLs manually.")


if __name__ == '__main__':
    main()

