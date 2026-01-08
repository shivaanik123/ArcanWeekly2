# Testing Checklist - Historical Data System

Use this checklist to verify the new historical data system is working correctly.

---

## Pre-Testing Setup

- [ ] Code has been deployed to your server/environment
- [ ] You have access to the dashboard URL
- [ ] You have access to AWS S3 console (optional but helpful)
- [ ] You have sample weekly reports ready to upload

---

## Test 1: Initial Migration

### If you have comprehensive weekly reports in S3:

**Steps:**
1. Open terminal/command prompt on your server
2. Navigate to the project directory
3. Run: `python scripts/migrate_from_weekly_reports.py --dry-run`

**Expected Result:**
- [ ] Script shows list of properties found
- [ ] Shows number of weeks of data per property
- [ ] Shows date range for each property
- [ ] No error messages

4. Run: `python scripts/migrate_from_weekly_reports.py`
5. Type `yes` when prompted

**Expected Result:**
- [ ] Script processes each property
- [ ] Shows "Successfully migrated" for each property
- [ ] No errors at the end
- [ ] Summary shows success count > 0

---

## Test 2: Check Historical Data in S3

1. Log into AWS Console
2. Navigate to S3
3. Open your bucket (e.g., `arcan-dashboard-data-...`)
4. Navigate to `data/historical/`

**Expected Result:**
- [ ] Folder exists: `data/historical/`
- [ ] Contains folders for your properties (e.g., `Marbella/`, `Abbey_Lake/`)
- [ ] Each property folder has `historical_data.json`
- [ ] JSON files are not empty (download and check)
- [ ] JSON contains `weekly_occupancy_data` array with multiple entries

**Sample JSON structure to verify:**
```json
{
  "property_name": "Marbella",
  "last_updated": "2026-01-08T12:00:00",
  "weekly_occupancy_data": [
    {
      "date": "2024-01-01T00:00:00",
      "occupancy_percentage": 95.5,
      "leased_percentage": 97.0,
      ...
    },
    {
      "date": "2024-01-08T00:00:00",
      ...
    }
  ]
}
```

---

## Test 3: Verify Dashboard Graphs

1. Open your dashboard in a web browser
2. Select a property from the dropdown

**Expected Result:**
- [ ] Property loads without errors
- [ ] Current week data displays (occupancy, leased %, etc.)

3. Scroll down to the graphs section

**Expected Result - Occupancy Trends Graph:**
- [ ] Graph is visible and rendered
- [ ] Shows three lines: Occupancy %, Leased %, Projected %
- [ ] X-axis shows dates going back in time
- [ ] Multiple data points visible (not just one or two)
- [ ] Lines are connected (not just dots)
- [ ] Data looks reasonable (percentages between 0-100)
- [ ] Hover over points shows correct values

**Expected Result - Other Graphs:**
- [ ] Work Orders / Make Ready graph shows data
- [ ] Collections graph shows data (if available)
- [ ] Lease expirations graph shows data (if available)
- [ ] All graphs load without errors

4. Select a different property

**Expected Result:**
- [ ] Graphs update with different property's data
- [ ] No errors when switching properties

---

## Test 4: Upload New Weekly Reports

1. In the dashboard sidebar, find the "Bulk Upload" section
2. Select a property from dropdown
3. Select today's date
4. Click "Upload Reports" and choose files:
   - [ ] ResAnalytics_Box_Score_Summary.xlsx
   - [ ] Work_Order_Report.xlsx
   - [ ] Pending_Make_Ready_Unit_Details.xlsx
   - [ ] ResARAnalytics_Delinquency_Summary.xlsx
   - [ ] Residents_on_Notice.xlsx

**Expected Result:**
- [ ] All files show as "valid"
- [ ] No files show as "invalid"

5. Check "Backup existing files"
6. Click "Upload Files"

**Expected Result:**
- [ ] Progress bar shows upload progress
- [ ] All files upload successfully
- [ ] Message shows "Upload complete!"
- [ ] Message shows "Updating historical data..."
- [ ] No error messages
- [ ] Dashboard refreshes automatically

---

## Test 5: Verify Historical Data Updated

1. After upload completes and dashboard refreshes
2. Select the property you just uploaded to
3. Scroll to graphs

**Expected Result:**
- [ ] Occupancy Trends graph shows one additional data point
- [ ] New data point appears at the right end (most recent date)
- [ ] Value matches the data you uploaded
- [ ] Graph updates smoothly without errors

4. Check S3 (optional):
   - Navigate to `data/historical/{PropertyName}/historical_data.json`
   - Download the file
   - Open in text editor
   - Find the last entry in `weekly_occupancy_data`

**Expected Result:**
- [ ] Last entry's date matches today's upload date
- [ ] Last entry's occupancy_percentage matches Box Score report
- [ ] Last entry has work_orders_count > 0 (if you had work orders)
- [ ] File's `last_updated` timestamp is recent (today)

---

## Test 6: Manual Excel Import (Optional)

1. Generate template:
```bash
python scripts/import_historical_from_excel.py --generate-template test_import.xlsx
```

**Expected Result:**
- [ ] File `test_import.xlsx` created
- [ ] Can open in Excel
- [ ] Has "Historical Data" sheet with sample data
- [ ] Has "Instructions" sheet with documentation

2. Edit the template:
   - Delete sample rows
   - Add 2-3 weeks of test data with dates before your existing data
   - Save the file

3. Preview import:
```bash
python scripts/import_historical_from_excel.py test_import.xlsx "Marbella" --dry-run
```

**Expected Result:**
- [ ] Shows number of records to be imported
- [ ] Shows date range
- [ ] No error messages
- [ ] Says "[DRY RUN]" (not actually importing)

4. Actually import:
```bash
python scripts/import_historical_from_excel.py test_import.xlsx "Marbella"
```

**Expected Result:**
- [ ] Shows "Successfully imported X records"
- [ ] No error messages

5. Check dashboard graphs

**Expected Result:**
- [ ] Graph shows the additional historical data points
- [ ] New older points appear on the left side of the graph
- [ ] Data looks correct

---

## Test 7: Data Deduplication

1. Upload the same weekly reports again for the same property and date

**Expected Result:**
- [ ] Upload succeeds
- [ ] Message shows "Updated existing occupancy record" (not "Added new")
- [ ] Graph still shows same number of data points (no duplicates)
- [ ] Latest data point is updated, not duplicated

---

## Test 8: Multiple Properties

1. Select different properties from dashboard dropdown
2. For each property, check:

**Expected Result:**
- [ ] Each property shows its own historical data
- [ ] Data doesn't mix between properties
- [ ] Graphs show correct property name
- [ ] All properties load without errors

---

## Test 9: Error Handling

Try these scenarios to verify error handling:

**Scenario A: Upload without selecting property**

**Expected Result:**
- [ ] Upload button disabled or shows message
- [ ] Can't upload without property selected

**Scenario B: Upload invalid file**
- Try uploading a .txt file or .pdf

**Expected Result:**
- [ ] File rejected or shows as invalid
- [ ] Clear error message
- [ ] Other valid files still processable

**Scenario C: Check console logs**
- Open browser developer console (F12)
- Look for any red error messages

**Expected Result:**
- [ ] No JavaScript errors
- [ ] No 404 or 500 errors
- [ ] Console shows success messages for operations

---

## Test 10: Performance

1. Select a property with lots of historical data (6+ months)

**Expected Result:**
- [ ] Dashboard loads in < 10 seconds
- [ ] Graphs render in < 5 seconds
- [ ] No browser lag or freezing
- [ ] Switching properties is smooth

2. Upload reports for multiple properties in sequence

**Expected Result:**
- [ ] Each upload processes in reasonable time (< 2 minutes)
- [ ] No timeouts
- [ ] Historical data updates complete successfully

---

## Final Verification Checklist

After all tests, verify:

**System Health:**
- [ ] No errors in browser console
- [ ] No errors in server logs
- [ ] S3 has centralized historical data for all properties
- [ ] Dashboard loads correctly
- [ ] All graphs display data

**Functionality:**
- [ ] Can upload new weekly reports
- [ ] Historical data updates automatically
- [ ] Graphs show complete history
- [ ] Can switch between properties
- [ ] Data is accurate (matches source reports)

**Data Integrity:**
- [ ] No duplicate data points
- [ ] Dates are in correct order
- [ ] Percentages are in valid range (0-100)
- [ ] Unit counts are reasonable
- [ ] Historical data JSON files are valid

---

## If Tests Fail

### Graph shows "No historical data found"
1. Check S3 for historical_data.json file
2. Run migration script
3. Try uploading reports to trigger data build

### Upload succeeds but graphs don't update
1. Hard refresh browser (Ctrl+F5)
2. Check server logs for errors
3. Verify historical_data_service is being called

### Migration script errors
1. Check S3 credentials are set
2. Verify weekly reports exist in S3
3. Check file naming matches expected pattern

### Excel import errors
1. Verify pandas and openpyxl installed: `pip install pandas openpyxl`
2. Check date format in Excel (YYYY-MM-DD)
3. Verify required columns present

---

## Test Results Template

Copy this and fill out after testing:

```
TESTING COMPLETED: [DATE]
TESTER: [YOUR NAME]

Test 1 - Initial Migration: [ ] PASS [ ] FAIL
Test 2 - Check S3 Data: [ ] PASS [ ] FAIL
Test 3 - Dashboard Graphs: [ ] PASS [ ] FAIL
Test 4 - Upload Reports: [ ] PASS [ ] FAIL
Test 5 - Data Updated: [ ] PASS [ ] FAIL
Test 6 - Excel Import: [ ] PASS [ ] FAIL
Test 7 - Deduplication: [ ] PASS [ ] FAIL
Test 8 - Multiple Properties: [ ] PASS [ ] FAIL
Test 9 - Error Handling: [ ] PASS [ ] FAIL
Test 10 - Performance: [ ] PASS [ ] FAIL

OVERALL RESULT: [ ] ALL PASS [ ] SOME FAILURES

NOTES:
[Add any issues, observations, or concerns here]

ISSUES FOUND:
1.
2.
3.

SCREENSHOTS: [Attach or reference]
```

---

**Good luck with testing! If you encounter issues, refer to QUICK_START_GUIDE.md or contact technical support.**
