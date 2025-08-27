"""
Simple data loading for dashboard with S3 support
"""

import os
import sys
import tempfile
from typing import Dict, Any, List

# Add parent directory to path to import parsers and config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from parsers.file_parser import parse_directory
from utils.s3_service import get_storage_service



def get_available_weeks_and_properties(data_base_path: str = None) -> Dict[str, List[str]]:
    """Scan data directory to find available weeks and properties using S3 or local storage."""
    from config.property_config import get_all_properties, find_property_by_directory_name
    
    storage_service = get_storage_service()
    available_data = {'weeks': [], 'properties': []}
    
    # Get weeks using storage service
    weeks = storage_service.list_weeks()
    available_data['weeks'] = weeks
    
    # Get all properties across all weeks
    properties_set = set()
    
    for week in weeks:
        week_properties = storage_service.list_properties(week)
        for prop_item in week_properties:
            # Clean up property name (remove trailing spaces)
            clean_prop_name = prop_item.strip()
            
            # Map directory name to standard property name to avoid duplicates
            standard_property_name = find_property_by_directory_name(clean_prop_name)
            if standard_property_name:
                clean_prop_name = standard_property_name
            
            properties_set.add(clean_prop_name)
    
    # Add configured properties that might not have directories yet
    all_configured_properties = get_all_properties()
    for prop in all_configured_properties:
        properties_set.add(prop)
    
    available_data['properties'] = sorted(list(properties_set))
    available_data['weeks'].sort()
    
    return available_data

def load_property_data(week: str, property_name: str) -> Dict[str, Any]:
    """Load all data files for a specific week and property using S3 or local storage."""
    storage_service = get_storage_service()
    
    # Get list of Excel files for this property/week
    folder_path = f"{week}/{property_name}"
    excel_files = storage_service.list_files(folder_path)
    
    if not excel_files:
        # Try with trailing space (common issue) by getting all properties and finding a match
        all_properties = storage_service.list_properties(week)
        property_with_space = None
        
        for prop in all_properties:
            if prop.strip() == property_name or prop == property_name + " ":
                property_with_space = prop
                break
        
        if property_with_space:
            excel_files = storage_service.list_files(week, property_with_space)
            property_name = property_with_space  # Use the actual property name
    
    if not excel_files:
        return {'error': f"Data not found for {property_name} in week {week}"}
    
    # Extract property code from filenames (skip backup files)
    property_code = None
    
    for filename in excel_files:
        parts = filename.split('_')
        # Look for the part before .xlsx, but skip numeric suffixes like "_2"
        for part in parts:
            if part.endswith('.xlsx'):
                extracted = part.replace('.xlsx', '')
                # Skip numeric-only codes (like "2" from "_2.xlsx") and very short codes
                if extracted and not extracted.isdigit() and len(extracted) > 2:
                    property_code = extracted
                    break
        if property_code:
            break
    
    # Create temporary directory to download files for parsing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_property_path = os.path.join(temp_dir, property_name.strip())
        os.makedirs(temp_property_path, exist_ok=True)
        
        # Download all Excel files to temporary directory
        for filename in excel_files:
            file_s3_key = f"{week}/{property_name}/{filename}"
            file_data = storage_service.read_file(file_s3_key)
            if file_data:
                temp_file_path = os.path.join(temp_property_path, filename)
                with open(temp_file_path, 'wb') as f:
                    f.write(file_data)
        
        # Parse all files using existing parser (use property_code if found, otherwise parse all files)
        results = parse_directory(temp_property_path, property_filter=property_code)
        
        # Organize by parser type
        organized_data = {'raw_data': {}}
        
        for filename, file_data in results['files_parsed'].items():
            parser_type = file_data['parser_type']
            organized_data['raw_data'][parser_type] = file_data
        
        return organized_data