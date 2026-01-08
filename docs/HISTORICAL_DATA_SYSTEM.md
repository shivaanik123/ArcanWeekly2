# Centralized Historical Data System

## Overview

The Arcan Weekly Dashboard now uses a **centralized historical data system** that automatically aggregates metrics from individual Yardi reports into a single source of truth in S3. This eliminates the need to maintain separate comprehensive weekly reports with historical data.

## Architecture

### Before (Old System)
```
❌ Problems:
- Each weekly report contained full historical data
- Historical data duplicated across multiple reports
- Data could become inconsistent
- Required maintaining comprehensive Excel reports manually
- Graphs only showed data from latest comprehensive report
```

### After (New System)
```
✅ Benefits:
- Single centralized historical data store in S3
- Automatic updates when new weekly reports uploaded
- Data extracted from individual Yardi reports
- No need to maintain separate comprehensive reports
- Historical trends built automatically over time
- Graphs always show complete historical data
```

## Data Flow

### 1. Upload Individual Yardi Reports
When you upload weekly reports through the dashboard:

```
Upload Weekly Reports
├── ResAnalytics_Box_Score_Summary.xlsx
├── Work_Order_Report.xlsx
├── ResAnalytics_Unit_Availability_Details.xlsx
├── Pending_Make_Ready_Unit_Details.xlsx
├── ResARAnalytics_Delinquency_Summary.xlsx
└── Residents_on_Notice.xlsx
```

### 2. Automatic Historical Data Update
The system automatically:

1. **Extracts** current week metrics from uploaded reports:
   - Occupancy % (from Box Score)
   - Leased % (from Box Score)
   - Total/Occupied/Vacant units (from Box Score)
   - Work Orders count (from Work Orders report)
   - Make Ready count (from Make Ready report)
   - Collections % (from Delinquency report)
   - Notice units (from Residents on Notice)

2. **Loads** existing centralized historical data from S3

3. **Merges** new week data with historical data

4. **Deduplicates** by date (prevents duplicate entries)

5. **Saves** updated historical data back to S3

### 3. Dashboard Display
The dashboard loads centralized historical data and displays:

- Occupancy Trends (3-line chart: Occupancy, Leased, Projected)
- Maintenance Analytics (Work Orders, Make Ready trends)
- Collections Performance
- All other historical graphs

## S3 Structure

### Centralized Historical Data Location
```
s3://bucket-name/
├── data/
│   ├── historical/                    # Centralized historical data
│   │   ├── Marbella/
│   │   │   └── historical_data.json   # Single source of truth
│   │   ├── 55_Pharr/
│   │   │   └── historical_data.json
│   │   └── Abbey_Lake/
│   │       └── historical_data.json
│   │
│   └── MM_DD_YYYY/                    # Weekly uploads
│       ├── PropertyName/
│       │   ├── ResAnalytics_Box_Score_Summary.xlsx
│       │   ├── Work_Order_Report.xlsx
│       │   └── ... (other reports)
│       └── ...
```

### Historical Data JSON Schema
```json
{
  "property_name": "Marbella",
  "last_updated": "2025-01-08T12:00:00",
  "metadata": {
    "total_units": 200,
    "models": 2,
    "office": 1,
    "location": "Atlanta, GA"
  },
  "weekly_occupancy_data": [
    {
      "date": "2024-01-01T00:00:00",
      "occupancy_percentage": 95.5,
      "leased_percentage": 97.0,
      "projected_percentage": 96.0,
      "total_units": 200,
      "occupied_units": 191,
      "vacant_units": 9,
      "notice_units": 5,
      "available_units": 4,
      "make_readies_count": 3,
      "work_orders_count": 12,
      "collections_percentage": 98.5,
      "projected_occupancy_30day": 96.0,
      "projected_move_ins_30day": 5,
      "projected_move_outs_30day": 3,
      "evictions_30day": 1
    },
    // ... more weeks
  ],
  "weekly_financial_data": [
    // Future: financial metrics
  ]
}
```

## Key Components

### 1. HistoricalDataService (`utils/historical_data_service.py`)
Main service for managing centralized historical data:

**Key Methods:**
- `load_historical_data(property_name)` - Load historical data from S3
- `save_historical_data(property_name, data)` - Save historical data to S3
- `extract_week_data_from_reports(parsed_data, report_date)` - Extract metrics from individual Yardi reports
- `update_with_new_week_data(property_name, parsed_data, report_date)` - Update historical data with new week

### 2. Enhanced Upload Handler (`utils/upload_handler.py`)
Automatically triggers historical data updates:

**Updated Flow:**
```python
1. Upload files to S3
2. Parse uploaded files
3. Extract current week metrics
4. Update centralized historical data
5. Clear cache and refresh dashboard
```

### 3. Updated Dashboard (`app.py`)
Loads from centralized historical data:

```python
# Old: Load from comprehensive weekly report
comprehensive_data = parse_file("Weekly Report.xlsx")

# New: Load from centralized S3 storage
historical_data = historical_service.load_historical_data(property_name)
```

### 4. Migration Scripts

Two migration scripts are available depending on your data:

#### A. Migrate from Comprehensive Weekly Reports (`scripts/migrate_from_weekly_reports.py`)
**Use this when:** You have comprehensive weekly reports with embedded historical data

**Best for:** Quickly populating months of historical data from existing reports

**How it works:**
- Finds the most recent comprehensive weekly report for each property
- Extracts all historical data from that report
- Populates centralized database in one step

```bash
# Dry run to see what would be migrated
python scripts/migrate_from_weekly_reports.py --dry-run

# Migrate all properties using their most recent weekly report
python scripts/migrate_from_weekly_reports.py

# Migrate specific property
python scripts/migrate_from_weekly_reports.py --property "Marbella"

# Verbose output
python scripts/migrate_from_weekly_reports.py --verbose
```

#### B. Migrate from Individual Yardi Reports (`scripts/migrate_historical_data.py`)
**Use this when:** You only have individual Yardi reports (Box Score, Work Orders, etc.)

**Best for:** Building historical data from weekly uploads over time

**How it works:**
- Processes each week/property combination
- Extracts current week metrics from individual reports
- Builds historical data week by week

```bash
# Dry run to see what would be migrated
python scripts/migrate_historical_data.py --dry-run

# Migrate all properties
python scripts/migrate_historical_data.py

# Migrate specific property
python scripts/migrate_historical_data.py --property "Marbella"

# Verbose output
python scripts/migrate_historical_data.py --verbose
```

**Recommendation:** If you have comprehensive weekly reports, use script A for faster migration. If you only have individual Yardi reports, use script B.

## Usage Guide

### For New Properties
1. Upload first week's Yardi reports through dashboard
2. Historical data will be automatically created
3. Subsequent uploads will append to historical data

### For Existing Properties (with Comprehensive Weekly Reports)
If you have comprehensive weekly reports with embedded historical data:
1. Run the weekly reports migration script:
   ```bash
   # Dry run to see what would be migrated
   python scripts/migrate_from_weekly_reports.py --dry-run

   # Migrate all properties using their most recent weekly report
   python scripts/migrate_from_weekly_reports.py

   # Migrate specific property
   python scripts/migrate_from_weekly_reports.py --property "Marbella"
   ```

### For Existing Properties (with Individual Yardi Reports)
If you only have individual Yardi reports uploaded:
1. Run the week-by-week migration script:
   ```bash
   python scripts/migrate_historical_data.py
   ```
2. Future uploads will automatically update historical data

### Uploading Weekly Reports
1. Select property from dropdown
2. Select report date
3. Upload individual Yardi Excel files (Box Score, Work Orders, etc.)
4. Click "Upload Files"
5. System automatically:
   - Uploads files to S3
   - Extracts current week metrics
   - Updates centralized historical data
   - Refreshes dashboard with updated graphs

## Data Extraction Details

### From Box Score Report (`ResAnalytics_Box_Score_Summary.xlsx`)
- Occupancy % (Physical Occupancy)
- Leased % (Leased %)
- Total Units
- Occupied Units
- Vacant Units

### From Work Orders Report (`Work_Order_Report.xlsx`)
- Work Orders Count (total rows)

### From Make Ready Report (`Pending_Make_Ready_Unit_Details.xlsx`)
- Make Ready Units Count (total rows)

### From Delinquency Report (`ResARAnalytics_Delinquency_Summary.xlsx`)
- Collections % (Collections Rate)

### From Residents on Notice (`Residents_on_Notice.xlsx`)
- Total Notice Units
- Evictions Count

## Benefits

1. **No Manual Maintenance**: No need to manually update comprehensive Excel reports

2. **Automatic Updates**: Historical data updated automatically on every upload

3. **Single Source of Truth**: One centralized location for all historical data

4. **Consistency**: Data extracted consistently from same sources every week

5. **Scalability**: Easy to add new properties or extend historical data

6. **Deduplication**: Prevents duplicate data entries for same date

7. **Backward Compatible**: Existing uploads can be migrated to new system

## Troubleshooting

### No Historical Data Showing
```
Problem: Dashboard shows "No historical data found"
Solution:
1. Check if historical data exists: data/historical/{PropertyName}/historical_data.json
2. Run migration script to populate from existing uploads
3. Upload new week's reports to trigger creation
```

### Historical Data Not Updating
```
Problem: New uploads not reflected in graphs
Solution:
1. Check console logs for "Updating historical data..." message
2. Verify files were successfully uploaded to S3
3. Check for errors in upload handler logs
4. Clear browser cache and refresh dashboard
```

### Duplicate Data Points
```
Problem: Same date appearing multiple times in graphs
Solution:
System automatically deduplicates by date. If seeing duplicates:
1. Check date format in historical data JSON
2. Re-run migration script to clean up data
```

## Future Enhancements

### Planned Features
- [ ] Financial metrics in historical data
- [ ] Rent trends aggregation
- [ ] Comparative analytics across properties
- [ ] Historical data export functionality
- [ ] Data validation and anomaly detection
- [ ] Automatic backups of historical data
- [ ] Historical data versioning

### Adding New Metrics
To add new metrics to historical data:

1. Update `HistoricalDataService.extract_week_data_from_reports()` to extract new metric
2. Update JSON schema in `weekly_occupancy_data` structure
3. Update dashboard graphs to display new metric
4. Run migration script to rebuild historical data with new metrics

## Technical Notes

### Performance
- Historical data stored as JSON for fast access
- Single file per property (lightweight, ~100KB per property)
- Loaded only once per dashboard session
- Cached in memory during session

### Data Integrity
- Automatic deduplication by date
- ISO 8601 date format for consistency
- Graceful handling of missing data (defaults to 0)
- Validation of data types during extraction

### Backward Compatibility
- Existing comprehensive weekly reports still work
- Migration script handles old data structure
- Gradual migration supported
- No breaking changes to existing functionality

## Support

For issues or questions:
1. Check console logs in dashboard
2. Review S3 bucket structure
3. Run migration script with --verbose flag
4. Contact development team

---

**Last Updated**: 2025-01-08
**Version**: 1.0
