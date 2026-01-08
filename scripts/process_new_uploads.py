#!/usr/bin/env python3
"""
Process New S3 Uploads and Update Historical Data

Run this script after uploading files directly to S3 to update historical data.

Usage:
    python scripts/process_new_uploads.py <week> <property>
    python scripts/process_new_uploads.py 01_15_2025 Marbella

Options:
    --all           Process all weeks and properties
    --week WEEK     Process specific week (MM_DD_YYYY format)
    --property PROP Process specific property
"""

import sys
import os
import argparse
import logging
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.s3_service import get_storage_service
from utils.historical_data_service import HistoricalDataService
from data.loader import load_property_data

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def process_week_property(week: str, property_name: str) -> bool:
    """Process a single week/property combination"""
    try:
        week_date = datetime.strptime(week, "%m_%d_%Y")

        logging.info(f"Processing {property_name} - {week}")

        storage_service = get_storage_service()
        historical_service = HistoricalDataService(storage_service)

        parsed_data = load_property_data(week, property_name)

        if not parsed_data:
            logging.warning(f"No data found for {property_name} - {week}")
            return False

        success = historical_service.update_with_new_week_data(
            property_name=property_name,
            parsed_data=parsed_data,
            report_date=week_date
        )

        if success:
            logging.info(f"✓ Updated historical data for {property_name}")
        else:
            logging.error(f"✗ Failed to update {property_name}")

        return success

    except Exception as e:
        logging.error(f"Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Process new S3 uploads')
    parser.add_argument('week', nargs='?', help='Week (MM_DD_YYYY)')
    parser.add_argument('property', nargs='?', help='Property name')
    parser.add_argument('--all', action='store_true', help='Process all')

    args = parser.parse_args()

    if args.all:
        logging.info("Processing all weeks and properties...")
        storage_service = get_storage_service()
        weeks = storage_service.list_weeks()

        success_count = 0
        fail_count = 0

        for week in weeks:
            properties = storage_service.list_properties(week)
            for prop in properties:
                if process_week_property(week, prop):
                    success_count += 1
                else:
                    fail_count += 1

        logging.info(f"\nDone: {success_count} success, {fail_count} failed")
        return 0 if fail_count == 0 else 1

    elif args.week and args.property:
        success = process_week_property(args.week, args.property)
        return 0 if success else 1

    else:
        parser.error("Provide week and property, or use --all")


if __name__ == '__main__':
    sys.exit(main())
