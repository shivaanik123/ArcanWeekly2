"""
Centralized Historical Data Service

This service manages a centralized historical data store in S3, providing:
- Single source of truth for historical property data
- Automatic updates when new weekly reports are uploaded
- Deduplication and validation of historical records
- Support for both internal and external report formats

S3 Structure:
    data/historical/{property_name}/historical_data.json
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from utils.s3_service import S3DataService

logger = logging.getLogger(__name__)


class HistoricalDataService:
    """Service for managing centralized historical data in S3"""

    HISTORICAL_PREFIX = "historical"

    def __init__(self, storage_service: S3DataService):
        """
        Initialize the historical data service

        Args:
            storage_service: S3DataService instance for storage operations
        """
        self.storage = storage_service

    def _get_historical_data_key(self, property_name: str) -> str:
        """
        Get the S3 key for a property's historical data

        Args:
            property_name: Name of the property

        Returns:
            S3 key string (e.g., "data/historical/Marbella/historical_data.json")
        """
        # Normalize property name for consistency
        normalized_name = property_name.strip().replace(" ", "_")
        return f"{self.storage.data_prefix}{self.HISTORICAL_PREFIX}/{normalized_name}/historical_data.json"

    def _serialize_date(self, obj: Any) -> Any:
        """
        Custom JSON serializer for datetime objects

        Args:
            obj: Object to serialize

        Returns:
            Serialized representation
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def _deserialize_date(self, date_str: str) -> datetime:
        """
        Deserialize ISO format date string to datetime

        Args:
            date_str: ISO format date string

        Returns:
            datetime object
        """
        try:
            return datetime.fromisoformat(date_str)
        except (ValueError, AttributeError):
            logger.warning(f"Failed to parse date: {date_str}")
            return None

    def load_historical_data(self, property_name: str) -> Optional[Dict[str, Any]]:
        """
        Load centralized historical data for a property from S3

        Args:
            property_name: Name of the property

        Returns:
            Historical data dictionary or None if not found

        Structure:
            {
                'property_name': str,
                'last_updated': str (ISO format),
                'metadata': {
                    'total_units': int,
                    'models': int,
                    'office': int,
                    'location': str
                },
                'weekly_occupancy_data': [
                    {
                        'date': str (ISO format),
                        'occupancy_percentage': float,
                        'leased_percentage': float,
                        'projected_percentage': float,
                        'make_readies_count': int,
                        'work_orders_count': int
                    },
                    ...
                ],
                'weekly_financial_data': [
                    {
                        'date': str (ISO format),
                        'revenue': float,
                        'expenses': float,
                        'noi': float,
                        'collections_percentage': float
                    },
                    ...
                ]
            }
        """
        s3_key = self._get_historical_data_key(property_name)

        if not self.storage.file_exists(s3_key):
            logger.info(f"No historical data found for {property_name} at {s3_key}")
            return None

        try:
            content = self.storage.read_file(s3_key)
            data = json.loads(content)

            logger.info(f"Loaded historical data for {property_name}: {len(data.get('weekly_occupancy_data', []))} weeks")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse historical data for {property_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading historical data for {property_name}: {e}")
            return None

    def save_historical_data(self, property_name: str, data: Dict[str, Any]) -> bool:
        """
        Save centralized historical data for a property to S3

        Args:
            property_name: Name of the property
            data: Historical data dictionary

        Returns:
            True if successful, False otherwise
        """
        s3_key = self._get_historical_data_key(property_name)

        try:
            # Add last_updated timestamp
            data['last_updated'] = datetime.now().isoformat()
            data['property_name'] = property_name

            # Serialize to JSON
            json_content = json.dumps(data, indent=2, default=self._serialize_date)

            # Write to S3
            self.storage.write_file(s3_key, json_content.encode('utf-8'))

            logger.info(f"Saved historical data for {property_name} to {s3_key}")
            return True

        except Exception as e:
            logger.error(f"Error saving historical data for {property_name}: {e}")
            return False

    def extract_week_data_from_reports(
        self,
        parsed_data: Dict[str, Any],
        report_date: datetime
    ) -> Dict[str, Any]:
        """
        Extract current week's data from individual Yardi reports

        This extracts metrics from:
        - Box Score: Occupancy %, Leased %, Total Units, Occupied/Vacant counts
        - Work Orders: Count of work orders
        - Pending Make Ready: Count of make ready units
        - Delinquency: Collections rate
        - Residents on Notice: Notice counts, evictions

        Args:
            parsed_data: Dictionary of parsed reports from parse_directory()
            report_date: Date of the week being processed

        Returns:
            Dictionary with extracted week data
        """
        week_data = {
            'date': report_date.isoformat(),
            'occupancy_percentage': 0.0,
            'leased_percentage': 0.0,
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
            'evictions_30day': 0
        }

        try:
            # Extract from Box Score
            if 'resanalytics_box_score' in parsed_data:
                box_score = parsed_data['resanalytics_box_score']
                data_sections = box_score.get('data_sections', {})

                # Get availability section
                if 'availability' in data_sections:
                    availability_df = data_sections['availability']

                    if not availability_df.empty and len(availability_df.columns) >= 2:
                        # Look for occupancy and leased percentages
                        for idx, row in availability_df.iterrows():
                            metric_name = str(row.iloc[0]).lower() if len(row) > 0 else ""
                            value = row.iloc[1] if len(row) > 1 else None

                            if 'occupancy' in metric_name and '%' in metric_name:
                                try:
                                    week_data['occupancy_percentage'] = float(str(value).strip('%'))
                                except (ValueError, AttributeError):
                                    pass

                            elif 'leased' in metric_name and '%' in metric_name:
                                try:
                                    week_data['leased_percentage'] = float(str(value).strip('%'))
                                except (ValueError, AttributeError):
                                    pass

                            elif 'total' in metric_name and 'unit' in metric_name:
                                try:
                                    week_data['total_units'] = int(value)
                                except (ValueError, AttributeError, TypeError):
                                    pass

                            elif 'occupied' in metric_name:
                                try:
                                    week_data['occupied_units'] = int(value)
                                except (ValueError, AttributeError, TypeError):
                                    pass

                            elif 'vacant' in metric_name:
                                try:
                                    week_data['vacant_units'] = int(value)
                                except (ValueError, AttributeError, TypeError):
                                    pass

            # Extract from Work Orders
            if 'work_order_report' in parsed_data:
                work_orders = parsed_data['work_order_report'].get('work_orders')
                if work_orders is not None and hasattr(work_orders, '__len__'):
                    week_data['work_orders_count'] = len(work_orders)

            # Extract from Pending Make Ready
            if 'pending_make_ready' in parsed_data:
                make_ready_data = parsed_data['pending_make_ready'].get('make_ready_data')
                if make_ready_data is not None and hasattr(make_ready_data, '__len__'):
                    week_data['make_readies_count'] = len(make_ready_data)

            # Extract from Delinquency (Collections)
            if 'resaranalytics_delinquency' in parsed_data:
                delinquency = parsed_data['resaranalytics_delinquency']
                data_sections = delinquency.get('data_sections', {})

                if 'summary' in data_sections:
                    summary_df = data_sections['summary']

                    if not summary_df.empty:
                        for idx, row in summary_df.iterrows():
                            metric_name = str(row.iloc[0]).lower() if len(row) > 0 else ""

                            if 'collection' in metric_name and '%' in metric_name:
                                value = row.iloc[1] if len(row) > 1 else None
                                try:
                                    week_data['collections_percentage'] = float(str(value).strip('%'))
                                except (ValueError, AttributeError):
                                    pass

            # Extract from Residents on Notice
            if 'residents_on_notice' in parsed_data:
                notice_data = parsed_data['residents_on_notice']
                data_sections = notice_data.get('data_sections', {})

                if 'summary' in data_sections:
                    summary_df = data_sections['summary']

                    if not summary_df.empty:
                        for idx, row in summary_df.iterrows():
                            metric_name = str(row.iloc[0]).lower() if len(row) > 0 else ""
                            value = row.iloc[1] if len(row) > 1 else None

                            if 'total' in metric_name and 'notice' in metric_name:
                                try:
                                    week_data['notice_units'] = int(value)
                                except (ValueError, AttributeError, TypeError):
                                    pass

                            elif 'eviction' in metric_name:
                                try:
                                    week_data['evictions_30day'] = int(value)
                                except (ValueError, AttributeError, TypeError):
                                    pass

            # Extract from Unit Availability (for projections)
            if 'resanalytics_unit_availability' in parsed_data:
                unit_avail = parsed_data['resanalytics_unit_availability']
                data_sections = unit_avail.get('data_sections', {})

                if 'move_schedule' in data_sections:
                    move_schedule_df = data_sections['move_schedule']

                    if not move_schedule_df.empty:
                        # Count move-ins and move-outs in next 30 days
                        # This is simplified - actual implementation depends on data structure
                        week_data['projected_move_ins_30day'] = 0
                        week_data['projected_move_outs_30day'] = 0

            logger.info(f"Extracted week data: Occ={week_data['occupancy_percentage']}%, "
                       f"Leased={week_data['leased_percentage']}%, "
                       f"WO={week_data['work_orders_count']}, "
                       f"MR={week_data['make_readies_count']}")

        except Exception as e:
            logger.error(f"Error extracting week data: {e}")

        return week_data

    def update_with_new_week_data(
        self,
        property_name: str,
        parsed_data: Dict[str, Any],
        report_date: datetime
    ) -> bool:
        """
        Update centralized historical data with new week's data from individual Yardi reports

        This method:
        1. Loads existing historical data (or creates new structure)
        2. Extracts current week metrics from individual reports
        3. Deduplicates by date
        4. Appends new data
        5. Sorts by date
        6. Saves back to S3

        Args:
            property_name: Name of the property
            parsed_data: Dictionary of parsed reports from parse_directory()
            report_date: Date of the new reports

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing historical data or create new structure
            historical_data = self.load_historical_data(property_name)

            if historical_data is None:
                historical_data = {
                    'property_name': property_name,
                    'metadata': {},
                    'weekly_occupancy_data': [],
                    'weekly_financial_data': []
                }
                logger.info(f"Creating new historical data structure for {property_name}")

            # Extract week data from individual reports
            week_data = self.extract_week_data_from_reports(parsed_data, report_date)

            # Deduplicate by date
            existing_dates = {record['date'] for record in historical_data['weekly_occupancy_data']}

            if week_data['date'] not in existing_dates:
                historical_data['weekly_occupancy_data'].append(week_data)
                logger.info(f"Added new occupancy record for {property_name} on {report_date.date()}")
            else:
                # Update existing record with new data
                for i, record in enumerate(historical_data['weekly_occupancy_data']):
                    if record['date'] == week_data['date']:
                        historical_data['weekly_occupancy_data'][i] = week_data
                        logger.info(f"Updated existing occupancy record for {property_name} on {report_date.date()}")
                        break

            # Sort by date (oldest first)
            historical_data['weekly_occupancy_data'].sort(key=lambda x: x['date'])

            # Save updated historical data
            success = self.save_historical_data(property_name, historical_data)

            if success:
                logger.info(f"Successfully updated historical data for {property_name}. "
                           f"Total records: {len(historical_data['weekly_occupancy_data'])}")

            return success

        except Exception as e:
            logger.error(f"Error updating historical data for {property_name}: {e}")
            return False

    def migrate_from_comprehensive_report(
        self,
        property_name: str,
        comprehensive_data: Dict[str, Any]
    ) -> bool:
        """
        Migrate historical data from a comprehensive weekly report to centralized storage

        This is used for initial population of historical data from existing reports.

        Args:
            property_name: Name of the property
            comprehensive_data: Parsed comprehensive report data

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if historical data already exists
            existing_data = self.load_historical_data(property_name)

            if existing_data and len(existing_data.get('weekly_occupancy_data', [])) > 0:
                logger.info(f"Historical data already exists for {property_name}, merging...")

            # Create new structure or use existing
            historical_data = existing_data or {
                'property_name': property_name,
                'metadata': {},
                'weekly_occupancy_data': [],
                'weekly_financial_data': []
            }

            # Update metadata
            if 'metadata' in comprehensive_data:
                historical_data['metadata'].update(comprehensive_data['metadata'])

            # Extract historical occupancy data
            if 'historical_data' in comprehensive_data and 'weekly_occupancy_data' in comprehensive_data['historical_data']:
                historical_records = comprehensive_data['historical_data']['weekly_occupancy_data']

                existing_dates = {record['date'] for record in historical_data['weekly_occupancy_data']}

                added_count = 0
                for record in historical_records:
                    # Normalize record structure
                    normalized_record = {
                        'date': record['date'].isoformat() if isinstance(record['date'], datetime) else record['date'],
                        'occupancy_percentage': record.get('occupancy_percentage', 0.0),
                        'leased_percentage': record.get('leased_percentage', 0.0),
                        'projected_percentage': record.get('projected_percentage', 0.0),
                        'make_readies_count': record.get('make_readies_count', 0),
                        'work_orders_count': record.get('work_orders_count', 0)
                    }

                    if normalized_record['date'] not in existing_dates:
                        historical_data['weekly_occupancy_data'].append(normalized_record)
                        existing_dates.add(normalized_record['date'])
                        added_count += 1

                logger.info(f"Migrated {added_count} historical records for {property_name}")

            # Sort by date
            historical_data['weekly_occupancy_data'].sort(key=lambda x: x['date'])

            # Save to S3
            return self.save_historical_data(property_name, historical_data)

        except Exception as e:
            logger.error(f"Error migrating historical data for {property_name}: {e}")
            return False

    def list_properties_with_historical_data(self) -> List[str]:
        """
        List all properties that have centralized historical data

        Returns:
            List of property names
        """
        try:
            prefix = f"{self.storage.data_prefix}{self.HISTORICAL_PREFIX}/"

            # List all folders in the historical prefix
            # This is a simplified version - actual implementation depends on S3 structure
            # You may need to implement a method in S3DataService to list folders

            logger.info(f"Listing properties with historical data under {prefix}")

            # Placeholder - implement based on your S3 structure
            return []

        except Exception as e:
            logger.error(f"Error listing properties with historical data: {e}")
            return []
