# Quick Start Guide

## Complete Workflow

This guide walks you through the complete workflow from scraping to networking.

### Step 1: Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd tt-scraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Set up API keys (optional, for AI features)
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Step 2: Scrape Alumni Data

```bash
python scrape_alumni.py
```

This creates `alumni_data.csv` with basic information.

### Step 3: Enrich Profiles

```bash
python enrich_profiles.py \
  --input alumni_data.csv \
  --output alumni_data_enriched.csv
```

This may take 30-60 minutes. You can resume if interrupted:
```bash
python enrich_profiles.py \
  --input alumni_data.csv \
  --output alumni_data_enriched.csv \
  --start 100  # Resume from index 100
```

### Step 4: Find Missing LinkedIn Profiles

```bash
python find_missing_linkedin.py \
  --input alumni_data_enriched.csv \
  --output alumni_missing_linkedin.csv
```

### Step 5: Use AI to Find LinkedIn Profiles (Optional)

```bash
# Make sure GEMINI_API_KEY is in .env file
python linkedin_finder_agent.py \
  --input alumni_missing_linkedin.csv \
  --output alumni_ai_enriched.csv \
  --limit 50  # Process 50 profiles at a time
```

### Step 6: Verify LinkedIn Profiles (Interactive)

```bash
python verify_linkedin_profiles.py \
  --input alumni_data_enriched.csv
```

**Controls:**
- `y` = Yes, keep this LinkedIn URL
- `n` = No, remove this LinkedIn URL
- `s` = Skip, leave unchanged
- `q` = Quit and save progress

**Resume after rate limiting:**
```bash
python verify_linkedin_profiles.py \
  --input alumni_data_enriched.csv \
  --start-from 90  # Resume from position 90
```

### Step 7: Split by Major

```bash
python split_by_major.py \
  --input alumni_data_enriched.csv
```

This creates separate CSV files for each major group.

### Step 8: Analyze Data

```bash
python analyze_alumni.py \
  --input alumni_data_enriched.csv \
  --analyze
```

## Common Use Cases

### Find CS/DS/EECS Alumni for Networking

```bash
# After splitting by major
python verify_linkedin_profiles.py \
  --input alumni_cs_ds_eecs.csv \
  --min-confidence HIGH
```

### Filter by Graduation Year

```bash
python analyze_alumni.py \
  --input alumni_data_enriched.csv \
  --grad-year-min 2020 \
  --grad-year-max 2024 \
  --output recent_alumni.csv
```

### Find Alumni by Major and Experience

```bash
python analyze_alumni.py \
  --input alumni_data_enriched.csv \
  --major "Computer Science" \
  --years-exp-min 3 \
  --years-exp-max 10 \
  --output cs_experienced.csv
```

## Tips

1. **Rate Limiting**: LinkedIn may rate limit you. Use `verify_linkedin_profiles.py` with `--start-from` to resume.

2. **API Keys**: Gemini API has a free tier. Get your key from https://makersuite.google.com/app/apikey

3. **Progress Saving**: All tools save progress automatically. You can interrupt and resume.

4. **Data Backup**: Keep backups of your CSV files before running tools that modify them.

5. **Verification**: Always verify LinkedIn profiles before reaching out to ensure accuracy.

## Troubleshooting

### "Playwright browser not found"
```bash
playwright install chromium
```

### "Gemini API error"
- Check that `GEMINI_API_KEY` is in `.env` file
- Verify API key is correct
- Check API quota

### "LinkedIn rate limiting"
- Wait 30-60 minutes before resuming
- Use `--start-from` to resume where you left off
- Verify in smaller batches

### "CSV file locked"
- Close Excel or other programs that have the CSV open
- Check file permissions

