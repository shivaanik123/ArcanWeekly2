"""
Simple data loading for dashboard
"""

import os
import sys
from typing import Dict, Any, List

# Add parent directory to path to import parsers and config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from parsers.file_parser import parse_directory



def get_available_weeks_and_properties(data_base_path: str) -> Dict[str, List[str]]:
    """Scan data directory to find available weeks and properties."""
    available_data = {'weeks': [], 'properties': []}
    
    if not os.path.exists(data_base_path):
        return available_data
        
    # Scan for week directories (format: MM_DD_YYYY)
    for item in os.listdir(data_base_path):
        week_path = os.path.join(data_base_path, item)
        if os.path.isdir(week_path) and '_' in item:
            available_data['weeks'].append(item)
            
            # Scan for property directories within each week
            for prop_item in os.listdir(week_path):
                prop_path = os.path.join(week_path, prop_item)
                if os.path.isdir(prop_path) and prop_item not in available_data['properties']:
                    available_data['properties'].append(prop_item)
    
    available_data['weeks'].sort()
    available_data['properties'].sort()
    
    return available_data

def load_property_data(data_base_path: str, week: str, property_name: str) -> Dict[str, Any]:
    """Load all data files for a specific week and property."""
    property_path = os.path.join(data_base_path, week, property_name)
    
    if not os.path.exists(property_path):
        return {'error': f"Data not found for {property_name} in week {week}"}
    
    # Extract property code from filenames
    excel_files = [f for f in os.listdir(property_path) if f.endswith('.xlsx')]
    property_code = None
    
    for filename in excel_files:
        parts = filename.split('_')
        for part in parts:
            if part.endswith('.xlsx'):
                property_code = part.replace('.xlsx', '')
                break
        if property_code:
            break
    
    # Parse all files
    results = parse_directory(property_path, property_filter=property_code)
    
    # Organize by parser type
    organized_data = {'raw_data': {}}
    
    for filename, file_data in results['files_parsed'].items():
        parser_type = file_data['parser_type']
        organized_data['raw_data'][parser_type] = file_data
    
    return organized_data