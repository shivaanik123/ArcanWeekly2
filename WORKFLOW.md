# Weekly Upload Workflow

## Simple 3-Step Process

### 1. Upload to S3
Upload your weekly Excel files directly to S3:

**Location:** `s3://your-bucket/data/MM_DD_YYYY/PropertyName/`

**Example:**
```
s3://arcan-dashboard-data/data/01_15_2025/Marbella/
├── ResAnalytics_Box_Score_Summary_Marbella.xlsx
├── Work_Order_Report_Marbella.xlsx
├── ResAnalytics_Unit_Availability_Details_Marbella.xlsx
├── Pending_Make_Ready_Unit_Details_Marbella.xlsx
├── ResARAnalytics_Delinquency_Summary_Marbella.xlsx
└── Residents_on_Notice_Marbella.xlsx
```

**Use AWS CLI:**
```bash
aws s3 cp local_files/ s3://bucket/data/01_15_2025/Marbella/ --recursive
```

**Or AWS Console:**
- Navigate to S3 bucket
- Go to `data/01_15_2025/Marbella/`
- Click "Upload" and select files

---

### 2. Process Uploads
Run the processing script to update historical data:

**Single property:**
```bash
python scripts/process_new_uploads.py 01_15_2025 Marbella
```

**All properties:**
```bash
python scripts/process_new_uploads.py --all
```

The script will:
- Read the files from S3
- Extract metrics (occupancy, work orders, etc.)
- Update centralized historical data
- Show success/failure for each property

---

### 3. View Dashboard
Open your dashboard and verify:
- Select the week
- Select the property
- Check graphs show updated data

---

## First Time Setup

Run migration to populate historical data from existing reports:

```bash
python scripts/migrate_from_weekly_reports.py
```

---

## File Naming

Required files (use these patterns):
- `ResAnalytics_Box_Score_Summary_*.xlsx`
- `Work_Order_Report_*.xlsx`
- `ResAnalytics_Unit_Availability_Details_*.xlsx`
- `Pending_Make_Ready_Unit_Details_*.xlsx`
- `ResARAnalytics_Delinquency_Summary_*.xlsx`
- `Residents_on_Notice_*.xlsx`

---

## Troubleshooting

**Files not showing in dashboard:**
- Check S3 location: `data/MM_DD_YYYY/PropertyName/`
- Verify file names match patterns
- Run processing script

**Processing script fails:**
- Check AWS credentials configured
- Verify files are valid Excel format
- Check file permissions in S3

**Historical data not updating:**
- Confirm processing script completed successfully
- Check for error messages in script output
- Verify S3 location: `data/historical/{property}/historical_data.json`

---

## Quick Reference

| Task | Command |
|------|---------|
| Upload files | AWS CLI or Console → `data/MM_DD_YYYY/PropertyName/` |
| Process one property | `python scripts/process_new_uploads.py 01_15_2025 Marbella` |
| Process all | `python scripts/process_new_uploads.py --all` |
| Initial migration | `python scripts/migrate_from_weekly_reports.py` |
| View dashboard | Open browser → Select week/property |
