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
    print(f"🔍 LOADING DATA: week={week}, property_name='{property_name}'")
    
    storage_service = get_storage_service()
    folder_path = f"{week}/{property_name}"
    print(f"🔍 LOADING DATA: Looking for files in folder_path='{folder_path}'")
    
    excel_files = storage_service.list_files(folder_path)
    print(f"🔍 LOADING DATA: Found {len(excel_files)} files directly: {excel_files}")
    
    if not excel_files:
        print(f"🔍 LOADING DATA: No files found directly, checking all properties in week {week}")
        all_properties = storage_service.list_properties(week)
        print(f"🔍 LOADING DATA: All properties in week: {all_properties}")
        
        for prop in all_properties:
            print(f"🔍 LOADING DATA: Checking prop='{prop}' against property_name='{property_name}'")
            if prop.strip() == property_name or prop == property_name + " ":
                print(f"🔍 LOADING DATA: Match found! Using prop='{prop}'")
                excel_files = storage_service.list_files(week, prop)
                property_name = prop
                break
        
        print(f"🔍 LOADING DATA: After property matching, found {len(excel_files)} files: {excel_files}")
    
    if not excel_files:
        error_msg = f"Data not found for {property_name} in week {week}"
        print(f"❌ LOADING DATA: {error_msg}")
        return {'error': error_msg}
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_property_path = os.path.join(temp_dir, property_name.strip())
        print(f"🔍 LOADING DATA: Creating temp directory: {temp_property_path}")
        os.makedirs(temp_property_path, exist_ok=True)
        
        print(f"🔍 LOADING DATA: Downloading {len(excel_files)} files...")
        for filename in excel_files:
            file_s3_key = f"{week}/{property_name}/{filename}"
            print(f"🔍 LOADING DATA: Downloading {file_s3_key}")
            file_data = storage_service.read_file(file_s3_key)
            if file_data:
                temp_file_path = os.path.join(temp_property_path, filename)
                with open(temp_file_path, 'wb') as f:
                    f.write(file_data)
                print(f"🔍 LOADING DATA: Successfully wrote {filename} ({len(file_data)} bytes)")
            else:
                print(f"❌ LOADING DATA: Failed to read {file_s3_key}")
        
        print(f"🔍 LOADING DATA: Parsing directory (all files)")
        results = parse_directory(temp_property_path)
        print(f"🔍 LOADING DATA: Parse results: {len(results.get('files_parsed', {}))} files parsed")
        organized_data = {'raw_data': {}}
        
        for filename, file_data in results['files_parsed'].items():
            parser_type = file_data['parser_type']
            organized_data['raw_data'][parser_type] = file_data
        
        return organized_data