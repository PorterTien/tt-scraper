# Contributing

Thank you for your interest in contributing to this project!

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a virtual environment and install dependencies
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Setup

```bash
# Clone your fork
git clone <your-fork-url>
cd tt-scraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Set up environment variables
cp .env.example .env
# Add your API keys to .env
```

## Code Style

- Follow PEP 8 style guide
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and single-purpose

## Testing

Before submitting a pull request:
- Test your changes with sample data
- Verify error handling works correctly
- Check that output files are correct
- Ensure no new dependencies are required (unless necessary)

## Pull Request Process

1. Update README.md if you add new features
2. Update requirements.txt if you add new dependencies
3. Test your changes thoroughly
4. Submit a pull request with a clear description

## Reporting Issues

When reporting issues, please include:
- Description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Python version
- Operating system

## Feature Requests

Feature requests are welcome! Please describe:
- The feature you'd like to see
- Why it would be useful
- How it might work

## Questions?

Feel free to open an issue for questions or discussions.

