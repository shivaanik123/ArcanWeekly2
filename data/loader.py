"""Data loading for dashboard with S3 support"""

import os
import sys
import tempfile
from typing import Dict, Any, List

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from parsers.file_parser import parse_directory
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
    
    property_code = None
    for filename in excel_files:
        parts = filename.split('_')
        for part in parts:
            if part.endswith('.xlsx'):
                extracted = part.replace('.xlsx', '')
                if extracted and not extracted.isdigit() and len(extracted) > 2:
                    property_code = extracted
                    break
        if property_code:
            break
    
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
        
        results = parse_directory(temp_property_path, property_filter=property_code)
        organized_data = {'raw_data': {}}
        
        for filename, file_data in results['files_parsed'].items():
            parser_type = file_data['parser_type']
            organized_data['raw_data'][parser_type] = file_data
        
        return organized_data