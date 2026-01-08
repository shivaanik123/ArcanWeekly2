# Migration Scripts

This directory contains scripts for migrating and importing historical data to the centralized S3 storage.

## Overview

There are three approaches to populate historical data:

### Option 1: Migrate from Comprehensive Weekly Reports (RECOMMENDED)

**Script:** `migrate_from_weekly_reports.py`

**Use when:** You have comprehensive weekly reports with embedded historical data

**Advantage:** Much faster - extracts months of data in one step per property

**Usage:**
```bash
# Preview what will be migrated
python scripts/migrate_from_weekly_reports.py --dry-run

# Migrate all properties
python scripts/migrate_from_weekly_reports.py

# Migrate specific property
python scripts/migrate_from_weekly_reports.py --property "Marbella"

# See detailed logs
python scripts/migrate_from_weekly_reports.py --verbose
```

**How it works:**
1. Scans S3 for all comprehensive weekly reports
2. Finds the most recent report for each property
3. Extracts ALL historical data from that report
4. Populates centralized database at `data/historical/{property}/historical_data.json`

### Option 2: Migrate from Individual Yardi Reports

**Script:** `migrate_historical_data.py`

**Use when:** You only have individual Yardi reports (Box Score, Work Orders, etc.)

**Advantage:** Works with any uploaded data, even without comprehensive reports

**Usage:**
```bash
# Preview what will be migrated
python scripts/migrate_historical_data.py --dry-run

# Migrate all properties
python scripts/migrate_historical_data.py

# Migrate specific property
python scripts/migrate_historical_data.py --property "Marbella"

# See detailed logs
python scripts/migrate_historical_data.py --verbose
```

**How it works:**
1. Scans S3 for all week/property combinations
2. For each week, downloads and parses individual reports
3. Extracts current week metrics from each report
4. Builds historical data week by week
5. Saves to centralized database

### Option 3: Manual Import from Excel File

**Script:** `import_historical_from_excel.py`

**Use when:** You want to manually add or edit historical data

**Advantage:** Complete control over data, useful for corrections or backfilling

**Usage:**
```bash
# Step 1: Generate Excel template
python scripts/import_historical_from_excel.py --generate-template historical_template.xlsx

# Step 2: Fill in your data in the Excel file

# Step 3: Preview import
python scripts/import_historical_from_excel.py historical_template.xlsx "Marbella" --dry-run

# Step 4: Import (merges with existing data)
python scripts/import_historical_from_excel.py historical_template.xlsx "Marbella"

# Replace all existing data (use with caution!)
python scripts/import_historical_from_excel.py historical_template.xlsx "Marbella" --replace
```

**How it works:**
1. Generate Excel template with required columns
2. Fill in historical data (date, occupancy %, leased %, etc.)
3. Import merges new data with existing data (or replaces if --replace flag used)
4. Automatically deduplicates by date

**Template columns:**
- **Required:** date, occupancy_percentage, leased_percentage
- **Optional:** total_units, occupied_units, vacant_units, work_orders_count, make_readies_count, collections_percentage, etc.
- Date format: YYYY-MM-DD
- Percentages: Enter as numbers (95.5 for 95.5%)

## Which Script Should I Use?

### Use `migrate_from_weekly_reports.py` if:
- ✅ You have comprehensive weekly reports uploaded to S3
- ✅ Those reports contain historical data (occupancy trends, etc.)
- ✅ You want to quickly populate months of historical data
- ✅ You want the fastest migration

### Use `migrate_historical_data.py` if:
- ✅ You only have individual Yardi reports (no comprehensive reports)
- ✅ You want to build historical data from scratch
- ✅ You have weeks of individual report uploads

### Use `import_historical_from_excel.py` if:
- ✅ You want to manually add specific historical data
- ✅ You need to correct or update existing data
- ✅ You have historical data from other sources (spreadsheets, databases, etc.)
- ✅ You want to backfill missing weeks
- ✅ You prefer working with Excel over automated scripts

## Before Running Migration

1. **Set up AWS credentials:**
   ```bash
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   export AWS_REGION=us-east-1
   ```

2. **Configure S3 bucket:**
   Create a `.env` file based on `.env.example`:
   ```
   S3_BUCKET_NAME=your-bucket-name
   S3_DATA_PREFIX=data/
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Always run dry-run first:**
   ```bash
   python scripts/migrate_from_weekly_reports.py --dry-run
   ```

## After Migration

Once migration is complete:

1. **Verify the data:**
   - Check S3 at `data/historical/{property_name}/historical_data.json`
   - Load the dashboard and verify graphs show historical trends

2. **Future uploads:**
   - System will automatically update historical data when you upload new weekly reports
   - No need to run migration scripts again

## Example Workflow

### Scenario: You have 6 months of comprehensive weekly reports

```bash
# Step 1: See what will be migrated
python scripts/migrate_from_weekly_reports.py --dry-run

# Step 2: Migrate all properties
python scripts/migrate_from_weekly_reports.py

# Step 3: Verify in dashboard
# - Open dashboard
# - Select a property
# - Check that graphs show 6 months of data

# Step 4: Upload new week
# - Upload new reports through dashboard
# - Historical data automatically updates
```

## Output

Both scripts will:
- Show progress for each property
- Report success/failure counts
- List any errors encountered
- Save to: `s3://bucket/data/historical/{property}/historical_data.json`

## Troubleshooting

### "No module named 'boto3'"
Install dependencies: `pip install -r requirements.txt`

### "No weekly reports found"
- Verify reports are uploaded to S3
- Check filenames contain "weekly report" (case insensitive)
- Verify S3_BUCKET_NAME in .env

### "Failed to parse report"
- Check report format (must be .xlsx)
- Verify report contains historical data
- Run with `--verbose` flag for details

### Data not showing in dashboard
- Clear browser cache
- Restart Streamlit app
- Check S3 for historical_data.json file

## Support

For issues or questions, check:
- Main documentation: `docs/HISTORICAL_DATA_SYSTEM.md`
- Console logs during migration
- S3 bucket structure

---

**Note:** Always run with `--dry-run` first to preview changes before migrating!
