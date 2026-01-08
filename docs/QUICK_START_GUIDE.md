# Quick Start Guide - Historical Data System
## Simple Instructions for Non-Technical Users

This guide will walk you through setting up and using the new historical data system in plain English.

---

## What Changed?

**Before:** Each weekly report had to contain all historical data, which meant maintaining large Excel files manually.

**Now:** The system automatically builds historical data from your weekly uploads and stores it in one central place. Your graphs always show complete history without manual work.

---

## How to Get Started

### Option 1: Quick Setup (Using Your Existing Weekly Reports)

This is the **easiest and fastest** way if you already have comprehensive weekly reports in S3.

#### Step 1: Access Your Server
Connect to your Elastic Beanstalk server where the dashboard runs.

#### Step 2: Run the Migration Script
```bash
# First, see what will be migrated (safe preview)
python scripts/migrate_from_weekly_reports.py --dry-run
```

This will show you:
- Which properties will be migrated
- How many weeks of data found for each property
- What date range will be imported

#### Step 3: Run the Actual Migration
If the preview looks good:
```bash
python scripts/migrate_from_weekly_reports.py
```

Type `yes` when asked to confirm.

The script will:
- Find the most recent weekly report for each property
- Extract all the historical data from those reports
- Save it to the centralized database
- Take just a few minutes for all properties

#### Step 4: Check Your Dashboard
1. Open your dashboard
2. Select any property
3. Scroll down to the graphs
4. You should see your complete historical data!

---

### Option 2: Manual Entry (Using Excel)

Use this if you have historical data in spreadsheets or need to add specific data manually.

#### Step 1: Generate the Template
```bash
python scripts/import_historical_from_excel.py --generate-template marbella_history.xlsx
```

This creates an Excel file named `marbella_history.xlsx` (you can name it whatever you want).

#### Step 2: Open and Fill the Excel File
1. Open `marbella_history.xlsx` in Excel
2. Go to the "Historical Data" sheet
3. You'll see sample data - delete those rows
4. Fill in your own data:
   - **date**: Week date in format YYYY-MM-DD (like 2024-01-15)
   - **occupancy_percentage**: Occupancy % as a number (like 95.5)
   - **leased_percentage**: Leased % as a number (like 97.0)
   - Other columns are optional
5. Save the file

#### Step 3: Preview the Import
```bash
python scripts/import_historical_from_excel.py marbella_history.xlsx "Marbella" --dry-run
```

This shows what will be imported without actually saving it.

#### Step 4: Import the Data
```bash
python scripts/import_historical_from_excel.py marbella_history.xlsx "Marbella"
```

Type the property name exactly as it appears in your dashboard.

---

## Testing the System

### Test 1: Check Historical Graphs

1. **Open your dashboard** in a web browser
2. **Select a property** from the dropdown
3. **Scroll down** to the graphs section
4. **Look for the "Occupancy Trends" graph**
   - Should show occupancy %, leased %, and projected % over time
   - Should have data points going back in time
   - Lines should be smooth and connected

**What success looks like:**
- Graph shows multiple weeks of data
- Data matches what you expect from your reports
- No gaps or missing data points

### Test 2: Upload New Weekly Reports

1. **Collect this week's Yardi reports:**
   - ResAnalytics_Box_Score_Summary.xlsx
   - Work_Order_Report.xlsx
   - Pending_Make_Ready_Unit_Details.xlsx
   - ResARAnalytics_Delinquency_Summary.xlsx
   - Residents_on_Notice.xlsx
   - Any other reports you normally upload

2. **Open the dashboard**

3. **Use the upload section in the sidebar:**
   - Select property
   - Select report date (today's date)
   - Click "Choose files" and select all your reports
   - Click "Upload Files"

4. **Wait for upload to complete**
   - Progress bar will show
   - You'll see "Updating historical data..." message
   - Dashboard will refresh automatically

5. **Check the graphs again**
   - Should now show one additional week of data
   - New data point should appear on the right side of graphs

**What success looks like:**
- Upload completes without errors
- Historical data updated automatically
- Graphs immediately show the new week
- Total number of data points increased by 1

### Test 3: Verify Data in S3

If you have access to your S3 bucket:

1. **Navigate to S3 in AWS Console**
2. **Open your bucket** (e.g., arcan-dashboard-data-...)
3. **Navigate to:** `data/historical/`
4. **You should see folders** for each property:
   ```
   data/
   └── historical/
       ├── Marbella/
       │   └── historical_data.json
       ├── Abbey_Lake/
       │   └── historical_data.json
       └── (other properties...)
   ```
5. **Download one of the JSON files** and open in a text editor
6. **Look for `weekly_occupancy_data`** array
7. **Should see multiple entries** with dates, occupancy percentages, etc.

---

## Common Questions

### Q: Do I need to upload comprehensive weekly reports anymore?
**A:** No! Just upload the individual Yardi reports (Box Score, Work Orders, etc.) and the system automatically builds the historical data.

### Q: What happens to my existing weekly report uploads?
**A:** They stay in S3. The migration script extracts their historical data once, then you don't need them anymore.

### Q: Can I still upload comprehensive weekly reports?
**A:** Yes, but it's not necessary. The system now builds historical data automatically from individual reports.

### Q: How do I add data from before I started using the system?
**A:** Use the Excel import tool (Option 2 above) to manually add older data.

### Q: What if I need to correct a mistake in the historical data?
**A:** Use the Excel import tool. When you import data for a date that already exists, it updates that date's data.

### Q: How do I know if historical data is updating?
**A:** After each upload, check the console output for "Updating historical data..." and "Successfully updated historical data" messages.

---

## Troubleshooting

### Problem: Graphs show "No historical data found"

**Solutions:**
1. Run the migration script (Option 1 above)
2. Upload some weekly reports to trigger automatic data building
3. Check S3 bucket for `data/historical/{PropertyName}/historical_data.json`

### Problem: Upload successful but graphs don't update

**Solutions:**
1. Refresh your browser (Ctrl+F5 or Cmd+Shift+R)
2. Clear browser cache
3. Check the console logs during upload for any errors
4. Verify the property name matches exactly

### Problem: Excel import says "No module named 'pandas'"

**Solution:**
The server needs to install dependencies:
```bash
pip install pandas openpyxl
```

### Problem: Migration script finds no weekly reports

**Solutions:**
1. Check S3 bucket structure: `data/MM_DD_YYYY/PropertyName/`
2. Verify filenames contain "weekly report" (case insensitive)
3. Make sure files are .xlsx format

---

## Video Tutorial (Coming Soon)

For a video walkthrough, contact your technical team or check the project documentation.

---

## Need Help?

If something doesn't work:
1. Check the console logs for error messages
2. Take a screenshot of any errors
3. Note which step you were on
4. Contact your technical support team with:
   - What you were trying to do
   - What happened instead
   - Any error messages
   - Screenshots

---

## Summary Checklist

After setup, verify these items:

- [ ] Migration script ran successfully (or Excel import completed)
- [ ] Dashboard graphs show historical data
- [ ] Can upload new weekly reports
- [ ] Graphs automatically update after uploads
- [ ] S3 has `data/historical/` folder with JSON files
- [ ] Console shows "Successfully updated historical data" after uploads

If all boxes are checked, the system is working correctly! 🎉

---

**Last Updated:** 2026-01-08
