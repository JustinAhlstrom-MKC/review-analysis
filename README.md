# Review Analysis Automation

Automated system to sync Google My Business reviews to Google Sheets with 7shifts employee integration for Margie's Kitchen & Cocktails and Grackle.

## Features

- 🔄 Automated review syncing from Google My Business API
- 📊 Google Sheets integration with organized tabs per restaurant
- 👥 Employee list integration from 7shifts API
- 🏷️ Employee dropdown validation in Google Sheets
- 🎨 Conditional formatting for ratings
- 🤖 Automated employee name matching in reviews (AI-powered)
- 📈 Review analytics and summaries

## Project Structure

```
review-analysis/
├── .github/workflows/     # GitHub Actions automation (planned)
├── src/
│   ├── api/              # API clients
│   │   ├── google_business.py    # Google My Business API client
│   │   ├── google_sheets.py      # Google Sheets API client
│   │   └── sevenshift.py         # 7shifts API client
│   ├── core/             # Configuration and authentication
│   │   ├── auth.py               # Google OAuth authentication
│   │   └── config.py             # Configuration management
│   └── services/         # Business logic
│       └── review_sync.py        # Main sync service
├── scripts/              # User-facing scripts (see below)
├── config/               # Configuration files
│   ├── credentials/      # API credentials (git-ignored)
│   │   ├── google_oauth.json     # OAuth client credentials
│   │   └── google_token.pickle   # OAuth access token
│   └── settings.yaml     # App settings
├── data/                 # Data directory for exports (git-ignored)
└── logs/                 # Execution logs (git-ignored)
```

## Available Scripts

### Setup & Configuration Scripts

#### `setup_wizard.py`
Interactive setup wizard for first-time configuration.
```bash
python scripts/setup_wizard.py
```
**What it does:**
- Guides you through Google OAuth authentication
- Helps discover your Google My Business location IDs
- Creates the `.env` configuration file with your settings
- Validates credentials and API access

**When to use:** First time setup or when reconfiguring the project.

#### `create_sheet.py`
Creates a new Google Sheet for storing reviews.
```bash
python scripts/create_sheet.py
python scripts/create_sheet.py --title "My Custom Title"
```
**What it does:**
- Creates a new Google Sheet via Google Drive API
- Returns the Sheet ID and URL
- Provides the Sheet ID to add to your `.env` file

**When to use:** Initial setup to create your destination sheet.

#### `list_accounts.py`
Lists all Google My Business accounts you have access to.
```bash
python scripts/list_accounts.py
```
**What it does:**
- Queries Google My Business Account Management API
- Lists all business accounts with their IDs
- Shows account names, types, and your role
- Helps identify which account contains your locations

**When to use:** Finding your account ID for use with `list_locations.py`.

#### `list_locations.py`
Lists all Google My Business locations across all your accounts.
```bash
python scripts/list_locations.py
```
**What it does:**
- Iterates through all your Google My Business accounts
- Lists all locations with their full resource names
- Shows location titles and addresses
- Provides the exact location IDs needed for `.env`

**When to use:** Finding location IDs for Margie's and Grackle.

#### `test_7shifts.py`
Tests and debugs 7shifts API connection.
```bash
python scripts/test_7shifts.py
```
**What it does:**
- Tests authentication with 7shifts API
- Tries multiple endpoint variations
- Lists available users and their roles
- Validates API key and company ID
- Helps identify role/department endpoints

**When to use:** Troubleshooting 7shifts API issues or validating credentials.

### Review Processing Scripts

#### `sync_reviews.py` (Primary Script)
Main script to sync reviews from Google My Business to Google Sheets.
```bash
python scripts/sync_reviews.py
```
**What it does:**
- Fetches reviews from Google My Business API for both locations
- Retrieves employee list from 7shifts API
- Creates/updates Google Sheet with:
  - Separate tabs for each restaurant
  - Employee list tab with dropdown validation
  - Conditional formatting for ratings
- Handles pagination and rate limiting
- Updates existing reviews and adds new ones

**When to use:** Regular review synchronization (daily, weekly, or as needed).

### Legacy/Alternative Scripts

#### `setup_auth.py` (Legacy)
Early authentication script, now superseded by `setup_wizard.py`.
```bash
python scripts/setup_auth.py
```
**What it does:**
- Basic Google OAuth flow
- Lists accounts
- Saves authentication token

**Note:** Use `setup_wizard.py` instead for full setup.

#### `fetch_reviews.py` (Legacy)
Early review fetching script, now superseded by `sync_reviews.py`.
```bash
python scripts/fetch_reviews.py
```
**Note:** Use `sync_reviews.py` for current workflow.

#### `import_reviews.py`
Imports reviews from Google Takeout data export.
```bash
python scripts/import_reviews.py
```
**What it does:**
- Extracts review data from Google Takeout ZIP files
- Parses JSON review files from Google Business Profile
- Consolidates reviews from multiple locations
- Saves to CSV format

**When to use:**
- Getting historical reviews not available via API
- Backup/archival purposes
- API quota issues

#### `process_takeout.py`
Advanced processing of Google Takeout data with employee matching.
```bash
python scripts/process_takeout.py [employee_file.csv]
```
**What it does:**
- Imports Google Takeout review data
- Performs AI-powered employee name extraction from reviews
- Matches mentioned names against employee roster
- Filters matching to last 6 months of reviews
- Generates employee mention analytics
- Saves processed data with employee columns

**When to use:** Analyzing historical reviews with employee attribution.

#### `create_dataset.py`
Creates analysis dataset from imported reviews.
```bash
python scripts/create_dataset.py [employee_file.csv] [input_file.csv]
```
**What it does:**
- Loads previously imported reviews
- Adds employee matching columns
- Processes employee mentions with location awareness
- Creates analysis-ready dataset

**When to use:** Preparing data for analysis after import.

#### `export_summary.py`
Exports summary analysis and reports from processed reviews.
```bash
python scripts/export_summary.py [input_file.csv]
```
**What it does:**
- Generates comprehensive review statistics
- Creates restaurant-by-restaurant breakdowns
- Analyzes rating distributions
- Produces employee mention summaries
- Exports to CSV and JSON formats

**When to use:** Creating reports and analytics from processed data.

## Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure Google Cloud

1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable these APIs:
   - Google My Business API
   - Google Sheets API
   - Google Drive API
3. Create OAuth 2.0 credentials (Desktop application)
4. Download credentials and save as `config/credentials/google_oauth.json`

### 3. Run Setup Wizard

```bash
python scripts/setup_wizard.py
```

This will:
- Authenticate with Google (one-time OAuth flow)
- Save your authentication token
- Guide you through finding location IDs
- Create your `.env` configuration file

### 4. Find Your Location IDs

```bash
# List all accounts
python scripts/list_accounts.py

# List all locations
python scripts/list_locations.py
```

Copy the full location resource names (e.g., `accounts/12345/locations/67890`)

### 5. Get 7shifts API Credentials

1. Log in to 7shifts
2. Go to Settings → API
3. Generate an API key
4. Note your Company ID

### 6. Create Google Sheet

```bash
python scripts/create_sheet.py
```

This creates a new Google Sheet and provides the Sheet ID.

### 7. Configure Environment Variables

Create/edit `.env` file with:

```bash
# Google Sheets Configuration
SHEET_ID=your_sheet_id_from_step_6

# 7shifts API Configuration
SEVENSHIFT_API_KEY=your_api_key
SEVENSHIFT_COMPANY_ID=your_company_id

# Restaurant Location IDs (from Google My Business)
MARGIES_LOCATION_ID=accounts/12345/locations/67890
GRACKLE_LOCATION_ID=accounts/12345/locations/67891

# Optional: Logging level
LOG_LEVEL=INFO
```

## Usage

### Primary Workflow: Sync Reviews

```bash
python scripts/sync_reviews.py
```

This will:
1. Fetch latest reviews from Google My Business
2. Get current employee list from 7shifts
3. Update Google Sheet with all data
4. Apply formatting and validation rules

### Alternative Workflow: Process Historical Reviews

```bash
# 1. Download Google Takeout (Google Business Profile only)
# 2. Place ZIP file in data/raw/

# 3. Import and process with employee matching
python scripts/process_takeout.py path/to/employees.csv

# 4. Generate summary report
python scripts/export_summary.py
```

## Configuration Files

### `.env` (git-ignored)
Your environment-specific settings:
```bash
# Google Sheets Configuration
SHEET_ID=your_sheet_id

# 7shifts API Configuration
SEVENSHIFT_API_KEY=your_api_key
SEVENSHIFT_COMPANY_ID=your_company_id

# Restaurant Location IDs (from Google My Business)
MARGIES_LOCATION_ID=accounts/12345/locations/67890
GRACKLE_LOCATION_ID=accounts/12345/locations/67891

# Optional: Logging level
LOG_LEVEL=INFO
```

### `config/credentials/` (git-ignored)
- `google_oauth.json` - OAuth 2.0 client credentials from Google Cloud Console
- `google_token.pickle` - Saved OAuth token (created automatically on first auth)

### `config/settings.yaml`
Application settings (version controlled):
- Restaurant names and configuration
- Google Sheet tab names
- Column headers and formatting
- API scopes and permissions

## Google Sheet Structure

The `sync_reviews.py` script creates/updates these tabs:

### 1. Margies Reviews
All reviews for Margie's Kitchen & Cocktails with columns:
- **Review ID** - Unique identifier from Google
- **Date Posted** - When review was created
- **Date Updated** - Last modification date
- **Reviewer Name** - Customer's name
- **Rating** - Star rating (1-5, color-coded)
- **Review Text** - Customer's comment
- **Response Text** - Your reply (if any)
- **Response Date** - When you responded
- **Employee Tagged** - Dropdown for manual selection
- **Notes** - Free text field for internal notes

### 2. Grackle Reviews
Same structure as Margies Reviews tab.

### 3. Employees
Current employee roster from 7shifts with columns:
- **Employee Name** - Full name
- **Role** - Position/title from 7shifts
- **Location** - Which restaurant(s) they work at
- **Active** - Employment status

This tab is used to populate the dropdown validation in the review tabs.

### Sheet Features
- ✅ Conditional formatting: ratings color-coded (red for low, green for high)
- ✅ Data validation: Employee dropdown restricted to active employees
- ✅ Frozen headers: First row stays visible when scrolling
- ✅ Auto-sizing: Columns sized to fit content
- ✅ Sorted: Reviews ordered by date (newest first)

## Troubleshooting

### Authentication Issues

**Problem:** "Token expired" or "Invalid credentials"

**Solution:**
```bash
# Delete saved token and re-authenticate
rm config/credentials/google_token.pickle
python scripts/setup_wizard.py
```

### API Access Errors

**Problem:** 403 Forbidden or "API not enabled"

**Solution:**
1. Verify APIs are enabled in Google Cloud Console:
   - My Business Account Management API
   - My Business Business Information API
   - Google Sheets API
   - Google Drive API
2. Check that OAuth credentials have correct scopes
3. Some Google My Business APIs require verification - apply at [Google My Business API setup](https://developers.google.com/my-business/content/basic-setup)

### Location IDs Not Found

**Problem:** Can't find your restaurant location IDs

**Solutions:**
1. Use `list_accounts.py` then `list_locations.py` to discover them
2. Check Google Business Profile Manager for location details
3. Ensure you're authenticated with the correct Google account
4. Verify you have permission to access the business locations

### 7shifts API Issues

**Problem:** Can't connect to 7shifts or no employees returned

**Solution:**
1. Run `test_7shifts.py` to diagnose the issue
2. Verify API key and Company ID in `.env`
3. Check that API key has correct permissions in 7shifts settings
4. Ensure you're using the correct company ID

### Sheet Not Updating

**Problem:** Reviews aren't syncing to Google Sheet

**Solution:**
1. Check logs in `logs/` directory for error messages
2. Verify Sheet ID is correct in `.env`
3. Ensure the Google account has edit permissions on the sheet
4. Try running with verbose logging: `LOG_LEVEL=DEBUG`

### Missing Dependencies

**Problem:** Import errors when running scripts

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

## Project Status

### Current Features
- ✅ Google My Business API integration
- ✅ 7shifts API integration
- ✅ Google Sheets sync with formatting
- ✅ Employee dropdown validation
- ✅ Historical data import via Google Takeout
- ✅ Employee name matching in reviews (AI-powered)
- ✅ Review analytics and summaries

### Planned Enhancements
- [ ] GitHub Actions automation for scheduled syncing
- [ ] Advanced dashboard with charts and visualizations
- [ ] Sentiment analysis on reviews
- [ ] Automated response suggestions
- [ ] Email/Slack notifications for new reviews
- [ ] Historical trend tracking and reporting
- [ ] Integration with other review platforms (Yelp, TripAdvisor)
- [ ] Automated employee performance reports

## Technical Details

### APIs Used
- **Google My Business API** - Fetch reviews and location data
- **Google Sheets API** - Create and update spreadsheets
- **Google Drive API** - Create new sheet files
- **7shifts API** - Retrieve employee roster and roles

### Data Flow
```
Google My Business API → Review Data
         +
7shifts API → Employee Data
         ↓
   Review Sync Service
         ↓
  Google Sheets API → Formatted Spreadsheet
```

### Authentication
- Google APIs use OAuth 2.0 with offline access
- Token stored in `google_token.pickle` (automatically refreshed)
- 7shifts uses Bearer token authentication

### Error Handling
- Automatic retry with exponential backoff for API failures
- Rate limiting detection and handling
- Graceful degradation if 7shifts unavailable
- Comprehensive logging for debugging

## Contributing

This is a personal project, but feel free to fork and adapt for your use case.

## License

MIT License - free to use and modify for your own purposes.
