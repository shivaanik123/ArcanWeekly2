#!/usr/bin/env python3
"""
Historical Data Migration Script

This script migrates historical data from existing weekly uploads to the centralized
historical data structure in S3. It processes all existing week/property combinations
and builds the centralized historical database.

Usage:
    python scripts/migrate_historical_data.py [--property PROPERTY_NAME] [--dry-run]

Options:
    --property  Migrate only a specific property (optional)
    --dry-run   Show what would be migrated without actually writing to S3
    --verbose   Enable verbose logging
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.s3_service import get_storage_service
from utils.historical_data_service import HistoricalDataService
from data.loader import load_property_data
from config.property_config import PROPERTY_MAPPING


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def get_all_property_week_combinations(storage_service) -> List[Dict[str, Any]]:
    """
    Get all property/week combinations from S3

    Returns:
        List of dictionaries with week, property, and date info
    """
    combinations = []

    try:
        weeks = storage_service.list_weeks()
        logging.info(f"Found {len(weeks)} weeks in S3")

        for week_string in weeks:
            try:
                # Parse week date
                week_date = datetime.strptime(week_string, "%m_%d_%Y")

                # Get properties for this week
                properties = storage_service.list_properties(week_string)

                for property_name in properties:
                    combinations.append({
                        'week': week_string,
                        'property': property_name,
                        'date': week_date
                    })

            except ValueError as e:
                logging.warning(f"Skipping invalid week folder: {week_string}")
                continue

    except Exception as e:
        logging.error(f"Error listing weeks/properties: {e}")

    return combinations


def migrate_property_week(
    storage_service,
    historical_service: HistoricalDataService,
    week: str,
    property_name: str,
    week_date: datetime,
    dry_run: bool = False
) -> bool:
    """
    Migrate a single property/week combination

    Args:
        storage_service: S3 storage service
        historical_service: Historical data service
        week: Week string (e.g., "01_15_2025")
        property_name: Name of the property
        week_date: Date object for the week
        dry_run: If True, don't actually write to S3

    Returns:
        True if successful, False otherwise
    """
    try:
        logging.info(f"Processing {property_name} - {week}")

        # Load and parse the data
        parsed_data = load_property_data(week, property_name)

        if not parsed_data:
            logging.warning(f"No data found for {property_name} - {week}")
            return False

        # Check if we have necessary data
        has_box_score = 'resanalytics_box_score' in parsed_data
        has_comprehensive = 'comprehensive_internal' in parsed_data or 'comprehensive_external' in parsed_data

        if not has_box_score and not has_comprehensive:
            logging.warning(f"No Box Score or Comprehensive report for {property_name} - {week}")
            return False

        if dry_run:
            logging.info(f"[DRY RUN] Would update historical data for {property_name} - {week}")
            return True

        # Update historical data
        success = historical_service.update_with_new_week_data(
            property_name=property_name,
            parsed_data=parsed_data,
            report_date=week_date
        )

        if success:
            logging.info(f"Successfully migrated {property_name} - {week}")
        else:
            logging.error(f"Failed to migrate {property_name} - {week}")

        return success

    except Exception as e:
        logging.error(f"Error migrating {property_name} - {week}: {e}")
        return False


def main():
    """Main migration function"""
    parser = argparse.ArgumentParser(
        description='Migrate historical data from weekly uploads to centralized storage'
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

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    logging.info("=" * 80)
    logging.info("Historical Data Migration Script")
    logging.info("=" * 80)

    if args.dry_run:
        logging.info("Running in DRY RUN mode - no data will be written")

    # Initialize services
    storage_service = get_storage_service()
    historical_service = HistoricalDataService(storage_service)

    # Get all property/week combinations
    logging.info("Scanning S3 for property/week combinations...")
    combinations = get_all_property_week_combinations(storage_service)

    if not combinations:
        logging.error("No property/week combinations found in S3")
        return 1

    logging.info(f"Found {len(combinations)} property/week combinations")

    # Filter by property if specified
    if args.property:
        combinations = [c for c in combinations if c['property'] == args.property]
        logging.info(f"Filtered to {len(combinations)} combinations for property: {args.property}")

    # Group by property for reporting
    by_property = {}
    for combo in combinations:
        prop = combo['property']
        if prop not in by_property:
            by_property[prop] = []
        by_property[prop].append(combo)

    logging.info(f"\nMigration Summary:")
    logging.info(f"  Total properties: {len(by_property)}")
    for prop, combos in by_property.items():
        logging.info(f"    {prop}: {len(combos)} weeks")

    # Confirm before proceeding (unless dry run)
    if not args.dry_run:
        response = input("\nProceed with migration? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            logging.info("Migration cancelled")
            return 0

    # Process each combination
    logging.info("\n" + "=" * 80)
    logging.info("Starting migration...")
    logging.info("=" * 80 + "\n")

    success_count = 0
    fail_count = 0

    for combo in sorted(combinations, key=lambda x: (x['property'], x['date'])):
        success = migrate_property_week(
            storage_service=storage_service,
            historical_service=historical_service,
            week=combo['week'],
            property_name=combo['property'],
            week_date=combo['date'],
            dry_run=args.dry_run
        )

        if success:
            success_count += 1
        else:
            fail_count += 1

    # Final summary
    logging.info("\n" + "=" * 80)
    logging.info("Migration Complete")
    logging.info("=" * 80)
    logging.info(f"Successful: {success_count}")
    logging.info(f"Failed: {fail_count}")
    logging.info(f"Total: {len(combinations)}")

    if args.dry_run:
        logging.info("\nThis was a DRY RUN - no data was written to S3")

    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
