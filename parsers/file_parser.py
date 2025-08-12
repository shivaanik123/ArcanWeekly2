"""
Main file parser dispatcher for real estate data files.

This module automatically identifies file types based on naming patterns
and routes them to the appropriate specialized parser.
"""

import os
import re
from typing import Dict, Any, Optional, List

try:
    from .resanalytics_box_parser import parse_resanalytics_box_score, identify_resanalytics_box_file
    from .work_order_parser import parse_work_order_report, identify_work_order_file
    from .resanalytics_unit_parser import parse_resanalytics_unit_availability, identify_resanalytics_unit_file
    from .resanalytics_market_parser import parse_resanalytics_market_rent, identify_resanalytics_market_file
    from .resanalytic_lease_parser import parse_resanalytic_lease_expiration, identify_resanalytic_lease_file
    from .budget_comparison_parser import parse_budget_comparison, identify_budget_comparison_file
    from .pending_make_parser import parse_pending_make_ready, identify_pending_make_file
    from .resaranalytics_delinquency_parser import parse_resaranalytics_delinquency, identify_resaranalytics_delinquency_file
    from .residents_on_notice_parser import parse_residents_on_notice, identify_residents_on_notice_file
except ImportError:
    # For running as main script
    from resanalytics_box_parser import parse_resanalytics_box_score, identify_resanalytics_box_file
    from work_order_parser import parse_work_order_report, identify_work_order_file
    from resanalytics_unit_parser import parse_resanalytics_unit_availability, identify_resanalytics_unit_file
    from resanalytics_market_parser import parse_resanalytics_market_rent, identify_resanalytics_market_file
    from resanalytic_lease_parser import parse_resanalytic_lease_expiration, identify_resanalytic_lease_file
    from budget_comparison_parser import parse_budget_comparison, identify_budget_comparison_file
    from pending_make_parser import parse_pending_make_ready, identify_pending_make_file
    from resaranalytics_delinquency_parser import parse_resaranalytics_delinquency, identify_resaranalytics_delinquency_file
    from residents_on_notice_parser import parse_residents_on_notice, identify_residents_on_notice_file


# File type patterns and their corresponding parsers
FILE_PATTERNS = [
    {
        'pattern': 'resanalytics_box',
        'identifier': identify_resanalytics_box_file,
        'parser': parse_resanalytics_box_score,
        'description': 'ResAnalytics Box Score Summary'
    },
    {
        'pattern': 'work_order',
        'identifier': identify_work_order_file,
        'parser': parse_work_order_report,
        'description': 'Work Order Report'
    },
    {
        'pattern': 'resanalytics_unit',
        'identifier': identify_resanalytics_unit_file,
        'parser': parse_resanalytics_unit_availability,
        'description': 'ResAnalytics Unit Availability Details'
    },
    {
        'pattern': 'resanalytics_market',
        'identifier': identify_resanalytics_market_file,
        'parser': parse_resanalytics_market_rent,
        'description': 'ResAnalytics Market Rent Schedule'
    },
    {
        'pattern': 'resanalytic_lease',
        'identifier': identify_resanalytic_lease_file,
        'parser': parse_resanalytic_lease_expiration,
        'description': 'ResAnalytic Lease Expiration'
    },
    {
        'pattern': 'budget_comparison',
        'identifier': identify_budget_comparison_file,
        'parser': parse_budget_comparison,
        'description': 'Budget Comparison'
    },
    {
        'pattern': 'pending_make',
        'identifier': identify_pending_make_file,
        'parser': parse_pending_make_ready,
        'description': 'Pending Make Ready Unit Details'
    },
    {
        'pattern': 'resaranalytics_delinquency',
        'identifier': identify_resaranalytics_delinquency_file,
        'parser': parse_resaranalytics_delinquency,
        'description': 'ResARAnalytics Delinquency Summary'
    },
    {
        'pattern': 'residents_on_notice',
        'identifier': identify_residents_on_notice_file,
        'parser': parse_residents_on_notice,
        'description': 'Residents on Notice Report'
    }
]


def identify_file_type(filename: str) -> Optional[Dict[str, Any]]:
    """
    Identify the file type based on filename patterns.
    
    Args:
        filename: Name of the file to identify
        
    Returns:
        Dictionary with pattern info if identified, None otherwise
    """
    for pattern_info in FILE_PATTERNS:
        if pattern_info['identifier'](filename):
            return pattern_info
    
    return None


def parse_file(file_path: str) -> Dict[str, Any]:
    """
    Parse a real estate data file by automatically detecting its type.
    
    Args:
        file_path: Path to the Excel file to parse
        
    Returns:
        Dictionary containing parsed data, metadata, and file info
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    filename = os.path.basename(file_path)
    
    # Identify file type
    pattern_info = identify_file_type(filename)
    
    if pattern_info is None:
        return {
            'error': f"Unknown file type for: {filename}",
            'file_path': file_path,
            'supported_patterns': [p['pattern'] for p in FILE_PATTERNS]
        }
    
    try:
        # Parse the file using the appropriate parser
        result = pattern_info['parser'](file_path)
        
        # Add pattern information to the result
        result['file_type_info'] = {
            'pattern': pattern_info['pattern'],
            'description': pattern_info['description'],
            'filename': filename
        }
        
        return result
        
    except Exception as e:
        return {
            'error': f"Error parsing {filename}: {str(e)}",
            'file_path': file_path,
            'file_type': pattern_info['pattern']
        }


def parse_directory(directory_path: str, property_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    Parse all Excel files in a directory.
    
    Args:
        directory_path: Path to directory containing Excel files
        property_filter: Optional property code filter (e.g., 'marbla')
        
    Returns:
        Dictionary with parsed results for each file
    """
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    results = {
        'directory': directory_path,
        'property_filter': property_filter,
        'files_parsed': {},
        'files_skipped': [],
        'errors': [],
        'summary': {}
    }
    
    # Get all Excel files in the directory
    excel_files = [f for f in os.listdir(directory_path) if f.endswith('.xlsx')]
    
    # Filter by property if specified
    if property_filter:
        excel_files = [f for f in excel_files if property_filter in f]
    
    # Parse each file
    for filename in excel_files:
        file_path = os.path.join(directory_path, filename)
        
        try:
            result = parse_file(file_path)
            
            if 'error' in result:
                results['errors'].append({
                    'filename': filename,
                    'error': result['error']
                })
            else:
                results['files_parsed'][filename] = result
                
        except Exception as e:
            results['errors'].append({
                'filename': filename,
                'error': str(e)
            })
    
    # Generate summary
    results['summary'] = {
        'total_files_found': len(excel_files),
        'files_successfully_parsed': len(results['files_parsed']),
        'files_with_errors': len(results['errors']),
        'file_types_found': {}
    }
    
    # Count file types
    for file_result in results['files_parsed'].values():
        if 'file_type_info' in file_result:
            pattern = file_result['file_type_info']['pattern']
            results['summary']['file_types_found'][pattern] = results['summary']['file_types_found'].get(pattern, 0) + 1
    
    return results


def get_supported_patterns() -> List[Dict[str, str]]:
    """
    Get list of supported file patterns and their descriptions.
    
    Returns:
        List of dictionaries with pattern and description
    """
    return [
        {
            'pattern': p['pattern'],
            'description': p['description']
        }
        for p in FILE_PATTERNS
    ]


if __name__ == "__main__":
    # Test the dispatcher with sample data
    test_dir = "/Users/shivaanikomanduri/ArcanClean/data/08_04_2025/Marbella "
    
    print("Supported file patterns:")
    for pattern in get_supported_patterns():
        print(f"  - {pattern['pattern']}: {pattern['description']}")
    
    print(f"\nParsing directory: {test_dir}")
    results = parse_directory(test_dir, property_filter='marbla')
    
    print(f"\nSummary:")
    print(f"Total files found: {results['summary']['total_files_found']}")
    print(f"Successfully parsed: {results['summary']['files_successfully_parsed']}")
    print(f"Errors: {results['summary']['files_with_errors']}")
    
    print(f"\nFile types found:")
    for file_type, count in results['summary']['file_types_found'].items():
        print(f"  - {file_type}: {count}")
    
    if results['errors']:
        print(f"\nErrors:")
        for error in results['errors']:
            print(f"  - {error['filename']}: {error['error']}")
