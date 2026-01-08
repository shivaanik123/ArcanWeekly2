#!/usr/bin/env python3
"""
Migrate Historical Data from Comprehensive Weekly Reports

This script extracts historical data from the most recent comprehensive weekly report
for each property and populates the centralized historical database.

Instead of processing individual Yardi reports week by week, this script uses the
historical data already embedded in comprehensive weekly reports.

Usage:
    python scripts/migrate_from_weekly_reports.py [--property PROPERTY_NAME] [--dry-run]

Options:
    --property  Migrate only a specific property (optional)
    --dry-run   Show what would be migrated without actually writing to S3
    --verbose   Enable verbose logging
    --latest    Only use the most recent weekly report for each property (default)
    --all       Process all weekly reports found (not recommended)
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import tempfile
import shutil

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.s3_service import get_storage_service
from utils.historical_data_service import HistoricalDataService
from parsers.file_parser import parse_file
from config.property_config import PROPERTY_MAPPING


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def find_weekly_reports(storage_service) -> Dict[str, List[Dict[str, Any]]]:
    """
    Find all comprehensive weekly reports in S3

    Returns:
        Dictionary mapping property names to list of weekly report info
        {
            'PropertyName': [
                {
                    'week': '01_15_2025',
                    'filename': 'PropertyName Weekly Report.xlsx',
                    's3_key': 'data/01_15_2025/PropertyName/PropertyName Weekly Report.xlsx',
                    'date': datetime
                },
                ...
            ],
            ...
        }
    """
    reports_by_property = {}

    try:
        weeks = storage_service.list_weeks()
        logging.info(f"Scanning {len(weeks)} weeks in S3...")

        for week_string in weeks:
            try:
                # Parse week date
                week_date = datetime.strptime(week_string, "%m_%d_%Y")

                # Get properties for this week
                properties = storage_service.list_properties(week_string)

                for property_name in properties:
                    # List all files in this week/property folder
                    folder_path = f"{week_string}/{property_name}"
                    all_files = storage_service.list_files(folder_path)

                    # Filter for weekly reports
                    weekly_report_files = [
                        f for f in all_files
                        if 'weekly report' in f.lower() and f.endswith('.xlsx') and not f.startswith('~$')
                    ]

                    for filename in weekly_report_files:
                        s3_key = f"{week_string}/{property_name}/{filename}"

                        if property_name not in reports_by_property:
                            reports_by_property[property_name] = []

                        reports_by_property[property_name].append({
                            'week': week_string,
                            'filename': filename,
                            's3_key': s3_key,
                            'date': week_date
                        })

            except ValueError as e:
                logging.warning(f"Skipping invalid week folder: {week_string}")
                continue

    except Exception as e:
        logging.error(f"Error scanning for weekly reports: {e}")

    return reports_by_property


def get_most_recent_reports(reports_by_property: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """
    Get the most recent weekly report for each property

    Args:
        reports_by_property: Dictionary of all reports by property

    Returns:
        Dictionary mapping property names to their most recent report
    """
    most_recent = {}

    for property_name, reports in reports_by_property.items():
        if reports:
            # Sort by date and get the most recent
            sorted_reports = sorted(reports, key=lambda x: x['date'], reverse=True)
            most_recent[property_name] = sorted_reports[0]

    return most_recent


def download_and_parse_report(storage_service, s3_key: str) -> Optional[Dict[str, Any]]:
    """
    Download and parse a weekly report from S3

    Args:
        storage_service: S3 storage service
        s3_key: S3 key of the report

    Returns:
        Parsed report data or None if error
    """
    try:
        # Create temp directory
        temp_dir = tempfile.mkdtemp()

        # Get original filename
        original_filename = s3_key.split('/')[-1]
        temp_file_path = os.path.join(temp_dir, original_filename)

        # Download from S3
        logging.debug(f"Downloading {s3_key}...")
        file_content = storage_service.read_file(s3_key)

        # Write to temp file
        with open(temp_file_path, 'wb') as f:
            f.write(file_content)

        # Parse the file
        logging.debug(f"Parsing {original_filename}...")
        parsed_data = parse_file(temp_file_path)

        # Clean up temp directory
        shutil.rmtree(temp_dir)

        return parsed_data

    except Exception as e:
        logging.error(f"Error downloading/parsing {s3_key}: {e}")
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir, ignore_errors=True)
        return None


def migrate_property_from_report(
    storage_service,
    historical_service: HistoricalDataService,
    property_name: str,
    report_info: Dict[str, Any],
    dry_run: bool = False
) -> bool:
    """
    Migrate historical data from a comprehensive report

    Args:
        storage_service: S3 storage service
        historical_service: Historical data service
        property_name: Name of the property
        report_info: Report information dictionary
        dry_run: If True, don't actually write to S3

    Returns:
        True if successful, False otherwise
    """
    try:
        logging.info(f"Processing {property_name} from {report_info['week']}")

        # Download and parse the report
        parsed_data = download_and_parse_report(storage_service, report_info['s3_key'])

        if not parsed_data:
            logging.error(f"Failed to parse report for {property_name}")
            return False

        # Check if it has historical data
        has_historical = 'historical_data' in parsed_data and 'weekly_occupancy_data' in parsed_data.get('historical_data', {})

        if not has_historical:
            logging.warning(f"No historical data found in report for {property_name}")
            logging.debug(f"Report keys: {list(parsed_data.keys())}")
            return False

        # Get the historical data
        historical_data = parsed_data['historical_data']
        weekly_occupancy_data = historical_data.get('weekly_occupancy_data', [])

        if not weekly_occupancy_data:
            logging.warning(f"No weekly occupancy data in report for {property_name}")
            return False

        logging.info(f"Found {len(weekly_occupancy_data)} weeks of historical data for {property_name}")

        if dry_run:
            logging.info(f"[DRY RUN] Would migrate {len(weekly_occupancy_data)} weeks for {property_name}")
            # Show date range
            if weekly_occupancy_data:
                dates = [record.get('date') for record in weekly_occupancy_data if record.get('date')]
                if dates:
                    min_date = min(dates)
                    max_date = max(dates)
                    logging.info(f"[DRY RUN] Date range: {min_date} to {max_date}")
            return True

        # Migrate using the historical service
        success = historical_service.migrate_from_comprehensive_report(
            property_name=property_name,
            comprehensive_data=parsed_data
        )

        if success:
            logging.info(f"✅ Successfully migrated {property_name}")
            logging.info(f"   Total weeks: {len(weekly_occupancy_data)}")
        else:
            logging.error(f"❌ Failed to migrate {property_name}")

        return success

    except Exception as e:
        logging.error(f"Error migrating {property_name}: {e}")
        import traceback
        logging.debug(traceback.format_exc())
        return False


def main():
    """Main migration function"""
    parser = argparse.ArgumentParser(
        description='Migrate historical data from comprehensive weekly reports to centralized storage'
    )
    parser.add_argument(
        '--property',
        type=str,
        help='Migrate only a specific property'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without writing to S3'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--latest',
        action='store_true',
        default=True,
        help='Only use the most recent weekly report for each property (default)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all weekly reports found (not recommended)'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    logging.info("=" * 80)
    logging.info("Migrate Historical Data from Comprehensive Weekly Reports")
    logging.info("=" * 80)

    if args.dry_run:
        logging.info("Running in DRY RUN mode - no data will be written")

    # Initialize services
    storage_service = get_storage_service()
    historical_service = HistoricalDataService(storage_service)

    # Find all weekly reports
    logging.info("\nScanning S3 for comprehensive weekly reports...")
    reports_by_property = find_weekly_reports(storage_service)

    if not reports_by_property:
        logging.error("No weekly reports found in S3")
        return 1

    total_reports = sum(len(reports) for reports in reports_by_property.values())
    logging.info(f"Found {total_reports} weekly reports across {len(reports_by_property)} properties")

    # Filter by property if specified
    if args.property:
        if args.property in reports_by_property:
            reports_by_property = {args.property: reports_by_property[args.property]}
            logging.info(f"Filtered to property: {args.property}")
        else:
            logging.error(f"Property '{args.property}' not found")
            logging.info(f"Available properties: {', '.join(sorted(reports_by_property.keys()))}")
            return 1

    # Get most recent reports (unless --all is specified)
    if args.all:
        logging.warning("Processing ALL weekly reports - this may create duplicate data!")
        reports_to_process = reports_by_property
    else:
        logging.info("\nUsing most recent weekly report for each property...")
        most_recent = get_most_recent_reports(reports_by_property)
        reports_to_process = {prop: [report] for prop, report in most_recent.items()}

    # Display migration plan
    logging.info("\nMigration Plan:")
    logging.info("-" * 80)
    for property_name in sorted(reports_to_process.keys()):
        reports = reports_to_process[property_name]
        for report in reports:
            logging.info(f"  {property_name:30} | {report['week']:15} | {report['filename']}")
    logging.info("-" * 80)
    logging.info(f"Total properties: {len(reports_to_process)}")
    logging.info(f"Total reports: {sum(len(r) for r in reports_to_process.values())}")

    # Confirm before proceeding (unless dry run)
    if not args.dry_run:
        response = input("\nProceed with migration? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            logging.info("Migration cancelled")
            return 0

    # Process each property
    logging.info("\n" + "=" * 80)
    logging.info("Starting migration...")
    logging.info("=" * 80 + "\n")

    success_count = 0
    fail_count = 0
    results = []

    for property_name in sorted(reports_to_process.keys()):
        reports = reports_to_process[property_name]

        # For now, just process the first (most recent) report per property
        report = reports[0]

        success = migrate_property_from_report(
            storage_service=storage_service,
            historical_service=historical_service,
            property_name=property_name,
            report_info=report,
            dry_run=args.dry_run
        )

        results.append({
            'property': property_name,
            'success': success,
            'report': report
        })

        if success:
            success_count += 1
        else:
            fail_count += 1

        # Add spacing between properties
        logging.info("")

    # Final summary
    logging.info("=" * 80)
    logging.info("Migration Complete")
    logging.info("=" * 80)
    logging.info(f"Successful: {success_count}")
    logging.info(f"Failed: {fail_count}")
    logging.info(f"Total: {len(results)}")

    # Show failed properties
    if fail_count > 0:
        logging.info("\nFailed Properties:")
        for result in results:
            if not result['success']:
                logging.info(f"  - {result['property']}")

    if args.dry_run:
        logging.info("\nThis was a DRY RUN - no data was written to S3")

    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
