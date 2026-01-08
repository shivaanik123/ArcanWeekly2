#!/usr/bin/env python3
"""
Import Historical Data from Excel Template

This script allows you to manually add or update historical data by uploading
a standardized Excel file. Useful for:
- Adding older historical data not in S3
- Manually correcting or updating data
- Bulk importing from other sources

Usage:
    python scripts/import_historical_from_excel.py <excel_file> <property_name> [--dry-run]

Examples:
    # Preview import
    python scripts/import_historical_from_excel.py marbella_history.xlsx "Marbella" --dry-run

    # Import data
    python scripts/import_historical_from_excel.py marbella_history.xlsx "Marbella"

    # Generate template
    python scripts/import_historical_from_excel.py --generate-template historical_template.xlsx
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.s3_service import get_storage_service
from utils.historical_data_service import HistoricalDataService


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def generate_template(output_file: str):
    """
    Generate an Excel template for manual historical data entry

    Args:
        output_file: Path to save the template
    """
    logging.info(f"Generating Excel template: {output_file}")

    # Create sample data
    sample_data = {
        'date': [
            '2024-01-01',
            '2024-01-08',
            '2024-01-15',
            '2024-01-22',
            '2024-01-29',
        ],
        'occupancy_percentage': [95.5, 96.0, 95.0, 94.5, 96.5],
        'leased_percentage': [97.0, 97.5, 96.5, 96.0, 98.0],
        'projected_percentage': [96.0, 96.5, 95.5, 95.0, 97.0],
        'total_units': [200, 200, 200, 200, 200],
        'occupied_units': [191, 192, 190, 189, 193],
        'vacant_units': [9, 8, 10, 11, 7],
        'notice_units': [5, 4, 6, 5, 3],
        'available_units': [4, 4, 4, 6, 4],
        'make_readies_count': [3, 2, 4, 3, 2],
        'work_orders_count': [12, 10, 15, 11, 9],
        'collections_percentage': [98.5, 98.0, 97.5, 98.2, 99.0],
        'projected_occupancy_30day': [96.0, 96.5, 95.5, 95.0, 97.0],
        'projected_move_ins_30day': [5, 6, 4, 5, 7],
        'projected_move_outs_30day': [3, 4, 5, 6, 2],
        'evictions_30day': [1, 0, 1, 2, 0],
    }

    df = pd.DataFrame(sample_data)

    # Create Excel writer with formatting
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Write data sheet
        df.to_excel(writer, sheet_name='Historical Data', index=False)

        # Write instructions sheet
        instructions = pd.DataFrame({
            'Instructions': [
                '1. Fill out the Historical Data sheet with your property data',
                '2. Date format: YYYY-MM-DD (e.g., 2024-01-15)',
                '3. Percentages: Enter as numbers (95.5 for 95.5%)',
                '4. Required columns: date, occupancy_percentage, leased_percentage',
                '5. Optional columns: All others (will default to 0 if missing)',
                '6. Save the file and run: python scripts/import_historical_from_excel.py <file> <property>',
                '',
                'Column Descriptions:',
                '- date: Week date (YYYY-MM-DD)',
                '- occupancy_percentage: Physical occupancy % (0-100)',
                '- leased_percentage: Leased % (0-100)',
                '- projected_percentage: 30-day projected occupancy %',
                '- total_units: Total units in property',
                '- occupied_units: Currently occupied units',
                '- vacant_units: Vacant units',
                '- notice_units: Units with notice to vacate',
                '- available_units: Available for rent',
                '- make_readies_count: Units in make-ready status',
                '- work_orders_count: Open work orders',
                '- collections_percentage: Collections rate %',
                '- projected_occupancy_30day: 30-day forecast %',
                '- projected_move_ins_30day: Expected move-ins (30 days)',
                '- projected_move_outs_30day: Expected move-outs (30 days)',
                '- evictions_30day: Expected evictions (30 days)',
            ]
        })
        instructions.to_excel(writer, sheet_name='Instructions', index=False)

        # Auto-adjust column widths
        worksheet = writer.sheets['Historical Data']
        for column in df.columns:
            max_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            worksheet.column_dimensions[chr(65 + col_idx)].width = max_length + 2

        instructions_sheet = writer.sheets['Instructions']
        instructions_sheet.column_dimensions['A'].width = 80

    logging.info(f"✅ Template created: {output_file}")
    logging.info(f"   Open the file, fill in your data, and import using:")
    logging.info(f"   python scripts/import_historical_from_excel.py {output_file} \"PropertyName\"")


def parse_excel_file(excel_file: str) -> List[Dict[str, Any]]:
    """
    Parse Excel file and extract historical data

    Args:
        excel_file: Path to Excel file

    Returns:
        List of historical data records
    """
    logging.info(f"Reading Excel file: {excel_file}")

    try:
        # Read the Historical Data sheet
        df = pd.read_excel(excel_file, sheet_name='Historical Data')

        logging.info(f"Found {len(df)} rows in Excel file")

        # Validate required columns
        required_columns = ['date', 'occupancy_percentage', 'leased_percentage']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        # Optional columns with defaults
        optional_columns = {
            'projected_percentage': 0.0,
            'total_units': 0,
            'occupied_units': 0,
            'vacant_units': 0,
            'notice_units': 0,
            'available_units': 0,
            'make_readies_count': 0,
            'work_orders_count': 0,
            'collections_percentage': 0.0,
            'projected_occupancy_30day': 0.0,
            'projected_move_ins_30day': 0,
            'projected_move_outs_30day': 0,
            'evictions_30day': 0,
        }

        # Add missing optional columns with defaults
        for col, default_value in optional_columns.items():
            if col not in df.columns:
                df[col] = default_value

        # Convert to list of dictionaries
        records = []
        for idx, row in df.iterrows():
            try:
                # Parse date
                date_value = row['date']
                if isinstance(date_value, str):
                    date_obj = datetime.strptime(date_value, '%Y-%m-%d')
                elif isinstance(date_value, pd.Timestamp):
                    date_obj = date_value.to_pydatetime()
                else:
                    date_obj = pd.to_datetime(date_value).to_pydatetime()

                record = {
                    'date': date_obj.isoformat(),
                    'occupancy_percentage': float(row['occupancy_percentage']),
                    'leased_percentage': float(row['leased_percentage']),
                    'projected_percentage': float(row.get('projected_percentage', 0.0)),
                    'total_units': int(row.get('total_units', 0)),
                    'occupied_units': int(row.get('occupied_units', 0)),
                    'vacant_units': int(row.get('vacant_units', 0)),
                    'notice_units': int(row.get('notice_units', 0)),
                    'available_units': int(row.get('available_units', 0)),
                    'make_readies_count': int(row.get('make_readies_count', 0)),
                    'work_orders_count': int(row.get('work_orders_count', 0)),
                    'collections_percentage': float(row.get('collections_percentage', 0.0)),
                    'projected_occupancy_30day': float(row.get('projected_occupancy_30day', 0.0)),
                    'projected_move_ins_30day': int(row.get('projected_move_ins_30day', 0)),
                    'projected_move_outs_30day': int(row.get('projected_move_outs_30day', 0)),
                    'evictions_30day': int(row.get('evictions_30day', 0)),
                }

                records.append(record)

            except Exception as e:
                logging.warning(f"Error parsing row {idx + 2}: {e}")
                continue

        logging.info(f"Successfully parsed {len(records)} records")

        # Show date range
        if records:
            dates = [r['date'] for r in records]
            logging.info(f"Date range: {min(dates)} to {max(dates)}")

        return records

    except Exception as e:
        logging.error(f"Error reading Excel file: {e}")
        raise


def import_historical_data(
    excel_file: str,
    property_name: str,
    dry_run: bool = False,
    merge: bool = True
) -> bool:
    """
    Import historical data from Excel file

    Args:
        excel_file: Path to Excel file
        property_name: Name of the property
        dry_run: If True, don't actually write to S3
        merge: If True, merge with existing data; if False, replace

    Returns:
        True if successful, False otherwise
    """
    try:
        # Parse Excel file
        new_records = parse_excel_file(excel_file)

        if not new_records:
            logging.error("No valid records found in Excel file")
            return False

        # Initialize services
        storage_service = get_storage_service()
        historical_service = HistoricalDataService(storage_service)

        # Load existing data if merging
        if merge:
            logging.info(f"Loading existing historical data for {property_name}...")
            historical_data = historical_service.load_historical_data(property_name)

            if historical_data:
                existing_records = historical_data.get('weekly_occupancy_data', [])
                logging.info(f"Found {len(existing_records)} existing records")

                # Merge new records
                existing_dates = {record['date'] for record in existing_records}
                new_count = 0
                updated_count = 0

                for new_record in new_records:
                    if new_record['date'] in existing_dates:
                        # Update existing record
                        for i, record in enumerate(existing_records):
                            if record['date'] == new_record['date']:
                                existing_records[i] = new_record
                                updated_count += 1
                                break
                    else:
                        # Add new record
                        existing_records.append(new_record)
                        new_count += 1

                # Sort by date
                existing_records.sort(key=lambda x: x['date'])

                historical_data['weekly_occupancy_data'] = existing_records

                logging.info(f"Merge summary: {new_count} new records, {updated_count} updated records")
                logging.info(f"Total records after merge: {len(existing_records)}")

            else:
                # No existing data, create new
                logging.info(f"No existing data found, creating new historical data")
                historical_data = {
                    'property_name': property_name,
                    'metadata': {},
                    'weekly_occupancy_data': sorted(new_records, key=lambda x: x['date']),
                    'weekly_financial_data': []
                }
        else:
            # Replace mode
            logging.warning(f"REPLACE mode: Will overwrite all existing data for {property_name}")
            historical_data = {
                'property_name': property_name,
                'metadata': {},
                'weekly_occupancy_data': sorted(new_records, key=lambda x: x['date']),
                'weekly_financial_data': []
            }

        # Show summary
        total_records = len(historical_data['weekly_occupancy_data'])
        logging.info(f"\nFinal data summary:")
        logging.info(f"  Property: {property_name}")
        logging.info(f"  Total records: {total_records}")

        if total_records > 0:
            dates = [r['date'] for r in historical_data['weekly_occupancy_data']]
            logging.info(f"  Date range: {min(dates)} to {max(dates)}")

        if dry_run:
            logging.info(f"\n[DRY RUN] Would save {total_records} records to S3")
            logging.info(f"[DRY RUN] S3 location: data/historical/{property_name}/historical_data.json")
            return True

        # Save to S3
        logging.info(f"\nSaving to S3...")
        success = historical_service.save_historical_data(property_name, historical_data)

        if success:
            logging.info(f"✅ Successfully imported {total_records} records for {property_name}")
            logging.info(f"   Data saved to S3: data/historical/{property_name}/historical_data.json")
        else:
            logging.error(f"❌ Failed to save data to S3")

        return success

    except Exception as e:
        logging.error(f"Error importing historical data: {e}")
        import traceback
        logging.debug(traceback.format_exc())
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Import historical data from Excel file or generate template'
    )
    parser.add_argument(
        'excel_file',
        nargs='?',
        help='Path to Excel file with historical data'
    )
    parser.add_argument(
        'property_name',
        nargs='?',
        help='Name of the property'
    )
    parser.add_argument(
        '--generate-template',
        metavar='FILE',
        help='Generate Excel template and save to FILE'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview import without writing to S3'
    )
    parser.add_argument(
        '--replace',
        action='store_true',
        help='Replace existing data instead of merging (dangerous!)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Generate template mode
    if args.generate_template:
        generate_template(args.generate_template)
        return 0

    # Import mode
    if not args.excel_file or not args.property_name:
        parser.error("excel_file and property_name are required (unless using --generate-template)")

    logging.info("=" * 80)
    logging.info("Import Historical Data from Excel")
    logging.info("=" * 80)

    if args.dry_run:
        logging.info("Running in DRY RUN mode - no data will be written\n")

    if args.replace:
        logging.warning("REPLACE mode enabled - will overwrite existing data!")
        if not args.dry_run:
            response = input("Are you sure you want to REPLACE all existing data? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                logging.info("Import cancelled")
                return 0

    # Import the data
    success = import_historical_data(
        excel_file=args.excel_file,
        property_name=args.property_name,
        dry_run=args.dry_run,
        merge=not args.replace
    )

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
