"""Data loading for dashboard with S3 support"""

import os
import sys
import tempfile
from datetime import datetime
from typing import Dict, Any, List, Optional

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from parsers.file_parser import parse_directory, parse_file
from utils.s3_service import get_storage_service



def get_available_weeks_and_properties(data_base_path: str = None) -> Dict[str, List[str]]:
    """Find available weeks and properties using S3 storage."""
    from config.property_config import get_all_properties, find_property_by_directory_name
    
    storage_service = get_storage_service()
    available_data = {'weeks': [], 'properties': []}
    
    weeks = storage_service.list_weeks()
    available_data['weeks'] = weeks
    
    properties_set = set()
    for week in weeks:
        week_properties = storage_service.list_properties(week)
        for prop_item in week_properties:
            clean_prop_name = prop_item.strip()
            standard_property_name = find_property_by_directory_name(clean_prop_name)
            if standard_property_name:
                clean_prop_name = standard_property_name
            properties_set.add(clean_prop_name)
    
    all_configured_properties = get_all_properties()
    for prop in all_configured_properties:
        properties_set.add(prop)
    
    available_data['properties'] = sorted(list(properties_set))
    available_data['weeks'].sort()
    
    return available_data

def load_property_data(week: str, property_name: str) -> Dict[str, Any]:
    """Load all data files for a specific week and property using S3 storage."""
    storage_service = get_storage_service()
    folder_path = f"{week}/{property_name}"

    excel_files = storage_service.list_files(folder_path)

    if not excel_files:
        all_properties = storage_service.list_properties(week)

        for prop in all_properties:
            if prop.strip() == property_name or prop == property_name + " ":
                excel_files = storage_service.list_files(week, prop)
                property_name = prop
                break

    if not excel_files:
        return {'error': f"Data not found for {property_name} in week {week}"}

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_property_path = os.path.join(temp_dir, property_name.strip())
        os.makedirs(temp_property_path, exist_ok=True)

        for filename in excel_files:
            file_s3_key = f"{week}/{property_name}/{filename}"
            file_data = storage_service.read_file(file_s3_key)
            if file_data:
                temp_file_path = os.path.join(temp_property_path, filename)
                with open(temp_file_path, 'wb') as f:
                    f.write(file_data)

        results = parse_directory(temp_property_path)
        organized_data = {'raw_data': {}}

        for filename, file_data in results['files_parsed'].items():
            parser_type = file_data['parser_type']
            organized_data['raw_data'][parser_type] = file_data

        return organized_data


def parse_week_date(week: str) -> Optional[datetime]:
    """
    Parse week folder name to datetime.

    Args:
        week: Week folder name (e.g., '01_05_26' for January 5, 2026)

    Returns:
        datetime object or None if parsing fails
    """
    try:
        # Try MM_DD_YY format
        return datetime.strptime(week, '%m_%d_%y')
    except ValueError:
        try:
            # Try MM_DD_YYYY format
            return datetime.strptime(week, '%m_%d_%Y')
        except ValueError:
            return None


def load_previous_month_delinquency(week: str, property_name: str) -> Optional[Dict[str, Any]]:
    """
    Load delinquency data from the most recent week of the previous month.

    Args:
        week: Current week folder name (e.g., '01_05_26')
        property_name: Property name to load data for

    Returns:
        Dictionary containing delinquency data or None if not found
    """
    from parsers.file_parser import parse_file

    # Parse current week date
    current_date = parse_week_date(week)
    if not current_date:
        return None

    # Calculate previous month
    if current_date.month == 1:
        prev_month = 12
        prev_year = current_date.year - 1
    else:
        prev_month = current_date.month - 1
        prev_year = current_date.year

    # Get all available weeks
    storage_service = get_storage_service()
    all_weeks = storage_service.list_weeks()

    # Find weeks from previous month
    prev_month_weeks = []
    for w in all_weeks:
        w_date = parse_week_date(w)
        if w_date and w_date.month == prev_month and w_date.year == prev_year:
            prev_month_weeks.append((w, w_date))

    if not prev_month_weeks:
        return None

    # Sort by date descending to get most recent
    prev_month_weeks.sort(key=lambda x: x[1], reverse=True)
    most_recent_week = prev_month_weeks[0][0]

    # List files in the previous month's week/property folder
    folder_path = f"{most_recent_week}/{property_name}"
    files = storage_service.list_files(folder_path)

    # Look for _2 delinquency file first, then regular
    delinquency_file = None
    for f in files:
        if 'resaranalytics_delinquency' in f.lower() and f.endswith('.xlsx'):
            if '_2.xlsx' in f.lower():
                delinquency_file = f
                break
            elif not delinquency_file:
                delinquency_file = f

    if not delinquency_file:
        # Try with trailing space on property name
        folder_path = f"{most_recent_week}/{property_name} "
        files = storage_service.list_files(folder_path)
        for f in files:
            if 'resaranalytics_delinquency' in f.lower() and f.endswith('.xlsx'):
                if '_2.xlsx' in f.lower():
                    delinquency_file = f
                    break
                elif not delinquency_file:
                    delinquency_file = f

    if not delinquency_file:
        return None

    # Download and parse the file
    file_s3_key = f"{folder_path}/{delinquency_file}"
    file_data = storage_service.read_file(file_s3_key)

    if not file_data:
        return None

    # Write to temp file and parse
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, delinquency_file)
        with open(temp_file_path, 'wb') as f:
            f.write(file_data)

        return parse_file(temp_file_path)