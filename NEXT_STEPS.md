# 🚀 Next Steps - Getting Your Review Automation Running

## ✅ What's Been Completed

1. ✅ Google Cloud APIs enabled (My Business, Sheets, Drive)
2. ✅ OAuth credentials downloaded and configured
3. ✅ Project restructured with modern, reusable architecture
4. ✅ All Python code written and tested
5. ✅ GitHub Actions workflow created
6. ✅ Dependencies installed

## 📋 What You Need To Do Next

### Step 1: Run the Setup Wizard (5 minutes)

```bash
cd /home/justin/dev/automation-projects/review-analysis
source venv/bin/activate
python scripts/setup_wizard.py
```

This will:
- Authenticate you with Google (opens browser)
- Create your `.env` configuration file
- Guide you through finding location IDs

### Step 2: Get 7shifts API Credentials (5 minutes)

1. Log in to https://www.7shifts.com
2. Go to **Settings** → **API** (or **Company Settings** → **Integrations** → **API**)
3. Click **Generate API Key** or **Create Access Token**
4. Copy the API Key and Company ID

You'll need:
- **API Key**: Long string like `eyJhbGc...`
- **Company ID**: Usually a number

Add these to your `.env` file when the wizard creates it.

### Step 3: Find Your Google My Business Location IDs (10-15 minutes)

This is the trickiest part. Here are your options:

#### Option A: Use the Google My Business API Explorer

1. Go to: https://developers.google.com/my-business/reference/rest/v4/accounts.locations/list
2. Click **"Try this method"** on the right
3. Sign in with your business account
4. You'll see a JSON response with your locations
5. Find the `name` field - it looks like: `"accounts/12345/locations/67890"`
6. The location ID is the full path: `accounts/12345/locations/67890`

#### Option B: Contact Google Business Profile Support

They can provide your location IDs directly.

#### Option C: Check the URL

Sometimes location IDs are in the URL when viewing your business in Google Business Profile Manager.

### Step 4: Create Your Google Sheet (2 minutes)

```bash
source venv/bin/activate
python scripts/create_sheet.py --title "Restaurant Reviews - Production"
```

This will:
- Create a new Google Sheet
- Give you the Sheet ID
- Provide instructions to add it to `.env`

### Step 5: Test the Sync Locally (5 minutes)

```bash
source venv/bin/activate
python scripts/sync_reviews.py
```

This will:
- Fetch all reviews from Google My Business
- Fetch employee list from 7shifts
- Write everything to your Google Sheet
- Apply formatting and dropdowns

**Check your Google Sheet** - you should see:
- Tab 1: Margies Reviews (with all review data)
- Tab 2: Grackle Reviews (with all review data)
- Tab 3: Employees (with current employee list)
- Tab 4: Dashboard (placeholder for now)

### Step 6: Set Up GitHub Actions Automation (10 minutes)

1. **Make sure your code is pushed to GitHub:**
   ```bash
   git add .
   git commit -m "Set up automated review sync system"
   git push origin main
   ```

2. **Add secrets to GitHub repository:**
   - Go to your repo on GitHub.com
   - Click **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret** for each of these:

   | Secret Name | Value | Where to Find It |
   |------------|-------|------------------|
   | `GOOGLE_OAUTH_JSON` | Entire contents of `config/credentials/google_oauth.json` | Open the file, copy all text |
   | `SHEET_ID` | Your Google Sheet ID | From Step 4, or from the sheet URL |
   | `SEVENSHIFT_API_KEY` | Your 7shifts API key | From Step 2 |
   | `SEVENSHIFT_COMPANY_ID` | Your 7shifts company ID | From Step 2 |
   | `MARGIES_LOCATION_ID` | Margie's location ID | From Step 3 |
   | `GRACKLE_LOCATION_ID` | Grackle's location ID | From Step 3 |

3. **Enable GitHub Actions:**
   - Go to the **Actions** tab in your repo
   - If workflows are disabled, click to enable them

4. **Test the workflow manually:**
   - Go to **Actions** → **Weekly Review Sync**
   - Click **Run workflow** → **Run workflow**
   - Watch it execute (takes ~2-5 minutes)
   - Check your Google Sheet for updated data

5. **Verify the schedule:**
   - The workflow is set to run **every Monday at 9:00 AM EST**
   - You can change this in `.github/workflows/weekly-sync.yml`
   - Cron format: `'0 14 * * 1'` = 14:00 UTC = 9:00 AM EST

## 🎉 You're Done!

Once Step 6 is complete, your system will:
- ✅ Run automatically every Monday morning
- ✅ Fetch all reviews from Google My Business
- ✅ Fetch current employee list from 7shifts
- ✅ Update your Google Sheet with fresh data
- ✅ Apply formatting and dropdowns
- ✅ Send you an email if anything fails

## 📊 Using Your Google Sheet

### Manual Tagging

In the review tabs (Margies Reviews / Grackle Reviews):
- Column J (**Employee Tagged**) has a dropdown with all current employees
- Click any cell to select who was mentioned in that review
- Column K (**Notes**) is for any additional comments

### Reading Reviews

- **Green rows** = 5-star reviews
- **Yellow rows** = 3-star reviews
- **Red rows** = 1-2 star reviews
- Sort/filter as needed

### Dashboard (Future)

The dashboard tab is a placeholder - you can build custom charts and metrics there!

## 🛠️ Maintenance

### Weekly Check
Just check your Google Sheet on Mondays to see the fresh data!

### Monthly Check
- Review the GitHub Actions logs to ensure it's running
- Update 7shifts employee data (happens automatically weekly)

### As Needed
- Re-run locally: `python scripts/sync_reviews.py`
- Update configuration: Edit `.env` or `config/settings.yaml`

## ❓ Troubleshooting

### "Location ID not found"
- Double-check the format: `accounts/12345/locations/67890`
- Verify you have access to those locations in Google Business Profile

### "7shifts API error"
- Verify API key is correct
- Check if API access is enabled in 7shifts settings

### "Sheet not found"
- Verify the Sheet ID in `.env` matches your actual sheet
- Make sure you've shared the sheet with yourself

### GitHub Actions fails
- Check the logs in the Actions tab
- Verify all secrets are set correctly
- Try running locally first to isolate the issue

## 📞 Need Help?

If you get stuck:
1. Check the logs in `logs/` (local runs)
2. Check GitHub Actions output (automated runs)
3. Review the error messages carefully
4. Google the specific API error codes

## 🎯 Future Enhancements

Ideas for expanding this system:
- Build interactive dashboard with charts
- Add sentiment analysis
- Email notifications for low ratings
- Automated response templates
- Integration with Yelp, TripAdvisor, etc.
- Weekly summary emails to managers
- Employee performance tracking

---

**Good luck! You've got a professional-grade automation system ready to go! 🚀**
