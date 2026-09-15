#!/bin/bash
# Simple pipeline script to run the complete workflow
# Usage: ./run_pipeline.sh

set -e  # Exit on error

echo "=========================================="
echo "Cal Theta Tau Alumni Scraper Pipeline"
echo "=========================================="
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Warning: Virtual environment not activated."
    echo "Please run: source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Scrape alumni data
echo "Step 1: Scraping alumni data..."
python scrape_alumni.py
echo ""

# Step 2: Enrich profiles
echo "Step 2: Enriching profiles..."
read -p "This may take 30-60 minutes. Continue? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python enrich_profiles.py \
        --input alumni_data.csv \
        --output alumni_data_enriched.csv
    echo ""
fi

# Step 3: Find missing LinkedIn
echo "Step 3: Finding missing LinkedIn profiles..."
python find_missing_linkedin.py \
    --input alumni_data_enriched.csv \
    --output alumni_missing_linkedin.csv
echo ""

# Step 4: Use AI to find LinkedIn (optional)
echo "Step 4: Use AI to find LinkedIn profiles (optional)..."
read -p "Do you want to use AI to find LinkedIn profiles? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -z "$GEMINI_API_KEY" ]; then
        echo "Warning: GEMINI_API_KEY not set in environment."
        echo "Make sure it's in your .env file."
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    read -p "How many profiles to process? (default: 50) " limit
    limit=${limit:-50}
    
    python linkedin_finder_agent.py \
        --input alumni_missing_linkedin.csv \
        --output alumni_ai_enriched.csv \
        --limit $limit
    echo ""
fi

# Step 5: Split by major
echo "Step 5: Splitting by major..."
python split_by_major.py \
    --input alumni_data_enriched.csv
echo ""

# Step 6: Analyze data
echo "Step 6: Analyzing data..."
python analyze_alumni.py \
    --input alumni_data_enriched.csv \
    --analyze
echo ""

echo "=========================================="
echo "Pipeline complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Verify LinkedIn profiles: python verify_linkedin_profiles.py --input alumni_data_enriched.csv"
echo "2. Check the split CSV files in the current directory"
echo "3. Use the data for networking!"
echo ""

