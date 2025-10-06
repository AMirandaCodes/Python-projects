# Web Scraper with Login Automation

## Project Overview

This Python script automates the extraction of **contact information (emails and phone numbers)** from a list of company pages on a filtered exhibitor website that requires **user authentication**.
It was built to efficiently gather contact data from hundreds of exhibitors listed behind a login wall, where each company page needed to be accessed individually to retrieve the contact email.
The scraper uses **Playwright** for browser automation and **BeautifulSoup** for HTML parsing.

This is a one-off solution for a particular application.

## Features

- Automated login using environment variables.
- Option for manual login (useful for CAPTCHA or MFA-protected sessions).
- Automatic navigation through exhibitor links parsed from a local HTML file.
- Extraction of emails and phone numbers from each exhibitor’s page.
- Exports results to a clean CSV file.

## Tech Stack

- Python 3
- [Playwright](https://playwright.dev/python/) – for automated browser control  
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) – for HTML parsing  
- [python-dotenv](https://pypi.org/project/python-dotenv/) – for environment variable management  

## Installation

1. Install dependencies
  ```bash
  pip install playwright beautifulsoup4 python-dotenv
```
2. Install Playwright browsers
```bash
python -m playwright install
```

## Usage
**Option 1: Manual login**
1. Set your credentials as environment variables:
  ```bash
  export KOELNMESSE_EMAIL="you@example.com"
  export KOELNMESSE_PASS="yourpassword"
  ```
2. Run:
```bash
python scrape_with_login.py
```

**Option 2: Manual login (for MFA or CAPTCHA)**
1. Run:
```bash
python scrape_with_login.py --manual
```

### Output
The script generates a CSV file (default: exhibitors_with_contact.csv) with the columns: Name | Link | Phone | Email

#### Notes
- The script expects a local HTML file (demo.html) containing links to exhibitor pages.
- Exhibitor links are automatically extracted based on their URL pattern (e.g. /exhibitor/).
- For stable scraping, use manual login mode when CAPTCHA or 2FA is enabled.
- You can adjust regex patterns and link filters as needed.
