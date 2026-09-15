# Cal Theta Tau Alumni Scraper & Networking Tools

A comprehensive Python toolkit for scraping, enriching, and networking with Cal Theta Tau alumni data.

## Features

- **Web Scraping**: Automatically scrape alumni data from the Cal Theta Tau alumni directory
- **Profile Enrichment**: Extract LinkedIn URLs, emails, company information, and bios
- **AI-Powered LinkedIn Finding**: Use Gemini AI to automatically find LinkedIn profiles
- **Interactive Verification**: Verify LinkedIn profiles with an interactive browser tool
- **Data Analysis**: Analyze alumni data by major, graduation year, experience level
- **Major Grouping**: Split alumni data by major into organized CSV files
- **Networking Tools**: Generate LinkedIn search URLs and filter alumni for networking

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd tt-scraper
   ```

2. **Set up virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

4. **Set up API keys (optional, for AI features):**
   ```bash
   cp .env.example .env
   # Edit .env and add your Gemini API key
   ```

5. **Run the scraper:**
   ```bash
   python scrape_alumni.py
   ```

## Tools Overview

| Tool | Purpose | Output |
|------|---------|--------|
| `scrape_alumni.py` | Scrape alumni data from website | `alumni_data.csv` |
| `enrich_profiles.py` | Enrich profiles with LinkedIn, email, company info | `alumni_data_enriched.csv` |
| `linkedin_finder_agent.py` | AI agent to find LinkedIn profiles automatically | CSV with found LinkedIn URLs |
| `verify_linkedin_profiles.py` | Interactive tool to verify LinkedIn profiles | Updated CSV with verified URLs |
| `split_by_major.py` | Split alumni data by major into separate CSV files | Multiple CSV files by major |
| `analyze_alumni.py` | Analyze and filter alumni data | Analysis report + filtered CSV |
| `generate_linkedin_searches.py` | Generate LinkedIn search URLs | CSV with search URLs |
| `find_missing_linkedin.py` | Find alumni missing LinkedIn profiles | `alumni_missing_linkedin.csv` |

## Workflow

### 1. Scrape Alumni Data

```bash
python scrape_alumni.py
```

This creates `alumni_data.csv` with basic alumni information (Name, Major, Grad Year, Profile URL).

### 2. Enrich Profiles

```bash
python enrich_profiles.py --input alumni_data.csv --output alumni_data_enriched.csv
```

This scrapes individual profile pages to extract:
- LinkedIn URLs
- Email addresses
- Company information
- Job titles
- Locations
- Bios

**Note**: This may take a while. You can resume using `--start` and `--limit` options.

### 3. Find Missing LinkedIn Profiles (Optional)

```bash
python find_missing_linkedin.py --input alumni_data_enriched.csv --output alumni_missing_linkedin.csv
```

### 4. Use AI to Find LinkedIn Profiles (Optional)

```bash
# Make sure you have GEMINI_API_KEY in .env file
python linkedin_finder_agent.py \
  --input alumni_missing_linkedin.csv \
  --output alumni_ai_enriched.csv \
  --limit 50
```

**Features:**
- Uses Gemini API (free tier available)
- Automatically searches for LinkedIn profiles using web search
- Name-based matching and context verification
- Confidence scores for each match
- Handles LinkedIn blocking gracefully

### 5. Verify LinkedIn Profiles (Interactive)

```bash
python verify_linkedin_profiles.py --input alumni_data_enriched.csv
```

**Features:**
- Opens each LinkedIn profile in your browser
- Interactive prompts (y/n/s/q) to verify profiles
- Automatically removes incorrect LinkedIn URLs
- Can resume from a specific position with `--start-from`
- Real-time CSV updates

**Example:**
```bash
# Verify profiles starting from position 90
python verify_linkedin_profiles.py --input alumni_data_enriched.csv --start-from 90

# Verify only high-confidence profiles
python verify_linkedin_profiles.py --input alumni_data_enriched.csv --min-confidence HIGH
```

### 6. Split by Major

```bash
python split_by_major.py --input alumni_data_enriched.csv
```

This creates separate CSV files for each major:
- `alumni_cs_ds_eecs.csv` - Computer Science, Data Science, EECS (grouped together)
- `alumni_mechanical_engineering.csv`
- `alumni_bioengineering.csv`
- `alumni_ieor.csv`
- `alumni_chemical_engineering.csv`
- `alumni_civil_engineering.csv`
- `alumni_cognitive_science.csv`
- `alumni_other.csv` - Small majors (< 5 alumni)

**Features:**
- Automatically consolidates major variations (e.g., "BioE" = "Bioengineering")
- Groups small majors into "Other" file
- Preserves original major names in CSV

### 7. Analyze Alumni Data

```bash
python analyze_alumni.py --input alumni_data_enriched.csv --analyze
```

Provides:
- Major distribution
- Graduation year trends
- Experience level breakdown
- Contact information availability

## Environment Variables

Create a `.env` file in the root directory:

```bash
# Gemini API Key (Required for AI agent)
# Get your API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Google Custom Search API (Optional, for better LinkedIn search results)
# Get API key from: https://console.cloud.google.com/apis/credentials
# Get Search Engine ID from: https://programmablesearchengine.google.com/controlpanel/all
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_search_engine_id_here

# OpenAI API Key (Optional, alternative to Gemini)
# Get your API key from: https://platform.openai.com/api-keys
# OPENAI_API_KEY=your_openai_api_key_here
```

## Requirements

- Python 3.7 or higher
- Playwright browser automation library
- Internet connection
- Gemini API key (for AI features, free tier available)

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## Configuration

### Scraper Settings

You can modify constants in `scrape_alumni.py`:
- `BASE_URL`: Base URL for alumni directory
- `OUTPUT_FILE`: Output CSV filename
- `DELAY_BETWEEN_PAGES`: Delay between page requests (default: 2 seconds)
- `PAGE_LOAD_TIMEOUT`: Page load timeout (default: 30000ms)
- `MAX_RETRIES`: Maximum retry attempts (default: 3)

### LinkedIn Finder Agent Settings

You can modify settings in `linkedin_finder_agent.py`:
- `delay`: Delay between searches (default: 1.0 seconds)
- `max_results`: Maximum search results to check (default: 15)
- `min_confidence`: Minimum confidence threshold (default: 30)

## Error Handling

All tools include comprehensive error handling:
- **Network issues**: Automatic retry with exponential backoff
- **Missing data fields**: Skips missing fields and continues
- **Page load timeouts**: Retries with increasing delays
- **Rate limiting**: Configurable delays between requests
- **LinkedIn blocking**: Graceful fallback to name-based matching
- **Keyboard interrupts**: Gracefully handles Ctrl+C

## Troubleshooting

### Playwright browser not found
```bash
playwright install chromium
```

### Gemini API errors
- Make sure your API key is set in `.env` file
- Check that you have API quota available
- Verify the API key is correct

### LinkedIn rate limiting
- The `verify_linkedin_profiles.py` tool helps you verify profiles manually
- Use `--start-from` to resume after rate limits
- Take breaks between verification sessions

### CSV file issues
- Make sure CSV files are not open in Excel or other programs
- Check file permissions
- Verify CSV encoding (should be UTF-8)

## File Structure

```
tt-scraper/
├── scrape_alumni.py              # Main scraper
├── enrich_profiles.py            # Profile enrichment
├── linkedin_finder_agent.py      # AI LinkedIn finder
├── verify_linkedin_profiles.py   # Interactive verification
├── split_by_major.py             # Split by major
├── analyze_alumni.py             # Data analysis
├── generate_linkedin_searches.py # Generate search URLs
├── find_missing_linkedin.py      # Find missing LinkedIn
├── networking_helper.py          # Interactive menu
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variable template
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## Output Files

- `alumni_data.csv` - Basic alumni data (scraped)
- `alumni_data_enriched.csv` - Enriched with LinkedIn, email, etc.
- `alumni_ai_enriched.csv` - AI-found LinkedIn profiles
- `alumni_missing_linkedin.csv` - Alumni without LinkedIn
- `alumni_*.csv` - Split files by major (e.g., `alumni_cs_ds_eecs.csv`)

## Notes

- The scraper uses a headless browser, so no browser window opens
- Default delays help avoid overwhelming servers
- All tools can be interrupted with Ctrl+C and will save progress
- CSV files are excluded from Git by default (see `.gitignore`)
- Original major names are preserved in CSV files for reference

## License

This project is provided as-is for educational and personal use. Please be respectful of website terms of service and rate limits when scraping.

## Contributing

Feel free to submit issues or pull requests for improvements!
