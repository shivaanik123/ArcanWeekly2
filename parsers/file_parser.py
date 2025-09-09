"""Main file parser dispatcher for real estate data files."""

import os
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class FileAnalysisResult:
    """Result of filename analysis"""
    filename: str
    report_type: str
    property_code: str
    property_name: str
    is_valid: bool
    error_message: Optional[str] = None
    suggested_fixes: List[str] = None

PROPERTY_MAPPINGS = {
    '55pharr': {'name': '55 Pharr', 'display': '55 Pharr'},
    'abbeylk': {'name': 'Abbey Lake', 'display': 'Abbey Lake'},
    'capella2': {'name': 'Capella', 'display': 'Capella'},
    'colwds': {'name': 'Colony Woods', 'display': 'Colony Woods'},
    'emersn': {'name': 'Emerson 1600', 'display': 'Emerson 1600'},
    'georget': {'name': 'Georgetown', 'display': 'Georgetown'},
    'hampec': {'name': 'Hamptons at East Cobb', 'display': 'Hamptons at East Cobb'},
    'hangar': {'name': 'The Hangar', 'display': 'The Hangar'},
    'haven': {'name': 'Haven', 'display': 'Haven'},
    'kenplc': {'name': 'Kensington Place', 'display': 'Kensington Place'},
    'longvw': {'name': 'Longview', 'display': 'Longview'},
    'manwes': {'name': 'Manchester at Weslyn', 'display': 'Manchester at Weslyn'},
    'marbla': {'name': 'Marbella', 'display': 'Marbella'},
    'marshp': {'name': 'Marsh Point', 'display': 'Marsh Point'},
    'perryh': {'name': 'Perry Heights', 'display': 'Perry Heights'},
    'portico': {'name': 'Portico at Lanier', 'display': 'Portico at Lanier'},
    'talloak': {'name': 'Tall Oaks', 'display': 'Tall Oaks'},
    'tapeprk': {'name': 'Tapestry Park', 'display': 'Tapestry Park'},
    'turn': {'name': 'The Turn', 'display': 'The Turn'},
    'wdlndcm': {'name': 'Woodland Commons', 'display': 'Woodland Commons'},
    '55 pharr': {'name': '55 Pharr', 'display': '55 Pharr'},
    'abbey lake': {'name': 'Abbey Lake', 'display': 'Abbey Lake'},
    'capella': {'name': 'Capella', 'display': 'Capella'},
    'colony woods': {'name': 'Colony Woods', 'display': 'Colony Woods'},
    'emerson 1600': {'name': 'Emerson 1600', 'display': 'Emerson 1600'},
    'georgetown apartments': {'name': 'Georgetown', 'display': 'Georgetown'},
    'hamptons': {'name': 'Hamptons at East Cobb', 'display': 'Hamptons at East Cobb'},
    'kensington': {'name': 'Kensington Place', 'display': 'Kensington Place'},
    'longview': {'name': 'Longview', 'display': 'Longview'},
    'manchester': {'name': 'Manchester at Weslyn', 'display': 'Manchester at Weslyn'},
    'marbella': {'name': 'Marbella', 'display': 'Marbella'},
    'marsh point': {'name': 'Marsh Point', 'display': 'Marsh Point'},
    'perry heights': {'name': 'Perry Heights', 'display': 'Perry Heights'},
    'portico at lanier': {'name': 'Portico at Lanier', 'display': 'Portico at Lanier'},
    'tall oaks': {'name': 'Tall Oaks', 'display': 'Tall Oaks'},
    'tapestry park': {'name': 'Tapestry Park', 'display': 'Tapestry Park'},
    'the hangar at ransley station': {'name': 'The Hangar', 'display': 'The Hangar'},
    'the turn': {'name': 'The Turn', 'display': 'The Turn'},
    'woodland common apartments': {'name': 'Woodland Commons', 'display': 'Woodland Commons'}
}

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
    from .comprehensive_internal_parser import parse_comprehensive_internal_report, identify_comprehensive_internal_file
    from .comprehensive_external_parser import parse_comprehensive_6sheet_report, identify_comprehensive_6sheet_file
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
    from comprehensive_internal_parser import parse_comprehensive_internal_report, identify_comprehensive_internal_file
    from parsers.comprehensive_external_parser import parse_comprehensive_6sheet_report, identify_comprehensive_6sheet_file


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
    },
    {
        'pattern': 'comprehensive_6sheet',
        'identifier': identify_comprehensive_6sheet_file,
        'parser': parse_comprehensive_6sheet_report,
        'description': 'Comprehensive 6-Sheet Weekly Report (55 PHARR format)'
    },
    {
        'pattern': 'comprehensive_internal',
        'identifier': identify_comprehensive_internal_file,
        'parser': parse_comprehensive_internal_report,
        'description': 'Comprehensive Internal Weekly Report (Historical Data)'
    },
    {
        'pattern': 'comprehensive_weekly',
        'identifier': lambda filename: 'weekly report' in filename.lower(),  # Simple pattern check
        'parser': parse_comprehensive_internal_report,
        'description': 'Comprehensive Weekly Report (Property Weekly Report format)'
    }
]


def identify_file_type(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Identify the file type based on file path and patterns.
    
    Args:
        file_path: Path to the file to identify
        
    Returns:
        Dictionary with pattern info if identified, None otherwise
    """
    filename = os.path.basename(file_path)
    for pattern_info in FILE_PATTERNS:
        # Try with full path first (for comprehensive parsers that need to read sheets)
        # then fall back to filename only
        if pattern_info['identifier'](file_path) or pattern_info['identifier'](filename):
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
    pattern_info = identify_file_type(file_path)
    
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


def analyze_filename(filename: str) -> FileAnalysisResult:
    """
    Analyze a filename to extract report type and property information.
    Enhanced version that consolidates filename_analyzer functionality.
    
    Args:
        filename: The filename to analyze
        
    Returns:
        FileAnalysisResult with extracted information
    """
    # Clean filename
    clean_filename = filename.strip()
    
    # Enhanced pattern matching with property extraction
    report_patterns = {
        'resanalytics_box': [
            r'^ResAnalytics_Box_Score_Summary_([^.]+)\.xlsx$',
            r'^ResAnalytics_Box.*?_([^.]+)\.xlsx$'
        ],
        'work_order': [
            r'^Work_Order_Report_([^.]+)\.xlsx$',
            r'^Work_Order.*?_([^.]+)\.xlsx$'
        ],
        'resanalytics_unit': [
            r'^ResAnalytics_Unit_Availability_Details_([^.]+)\.xlsx$',
            r'^ResAnalytics_Unit.*?_([^.]+)\.xlsx$'
        ],
        'resanalytics_market': [
            r'^ResAnalytics_Market_Rent_Schedule_([^.]+)\.xlsx$',
            r'^ResAnalytics_Market.*?_([^.]+)\.xlsx$'
        ],
        'resanalytic_lease': [
            r'^ResAnalytic_Lease_Expiration_([^.]+)\.xlsx$',
            r'^ResAnalytic_Lease.*?_([^.]+)\.xlsx$'
        ],
        'resaranalytics_delinquency': [
            r'^ResARAnalytics_Delinquency_Summary_([^.]+)\.xlsx$',
            r'^ResARAnalytics_Delinquency.*?_([^.]+)\.xlsx$'
        ],
        'pending_make': [
            r'^Pending_Make_Ready_Unit_Details\._([^.]+)\.xlsx$',
            r'^Pending_Make.*?_([^.]+)\.xlsx$'
        ],
        'residents_on_notice': [
            r'^Residents_on_Notice_([^.]+)\.xlsx$',
            r'^Residents.*?_([^.]+)\.xlsx$'
        ],
        'budget_comparison': [
            r'^Budget_Comparison.*?_([^_]+)_.*\.xlsx$',
            r'^Budget.*?_([^_]+)_.*\.xlsx$'
        ],
        'comprehensive_weekly': [
            r'^(.+?)\s+Weekly\s+Report.*\.xlsx$',
            r'^(.+?)Weekly.*\.xlsx$'
        ]
    }
    
    # Try each report pattern
    for report_type, patterns in report_patterns.items():
        for pattern in patterns:
            match = re.match(pattern, clean_filename, re.IGNORECASE)
            if match:
                property_code_raw = match.group(1).strip()
                
                # Normalize property code
                normalized_property = _normalize_property_code(property_code_raw)
                
                if normalized_property:
                    return FileAnalysisResult(
                        filename=filename,
                        report_type=report_type,
                        property_code=normalized_property['code'],
                        property_name=normalized_property['name'],
                        is_valid=True
                    )
    
    # If no pattern matched, return error
    return FileAnalysisResult(
        filename=filename,
        report_type='',
        property_code='',
        property_name='',
        is_valid=False,
        error_message=f"Filename pattern not recognized: {filename}",
        suggested_fixes=_suggest_filename_fixes(filename)
    )


def _normalize_property_code(raw_code: str) -> Optional[Dict[str, str]]:
    """Normalize property code to standard format"""
    
    # Clean the input
    clean_code = raw_code.lower().strip()
    
    # Remove common suffixes that might appear
    suffixes_to_remove = ['_2', '_1', ' (1)', ' (2)']
    for suffix in suffixes_to_remove:
        if clean_code.endswith(suffix.lower()):
            clean_code = clean_code[:-len(suffix)]
    
    # Direct lookup
    if clean_code in PROPERTY_MAPPINGS:
        mapping = PROPERTY_MAPPINGS[clean_code]
        return {
            'code': clean_code,
            'name': mapping['name'],
            'display': mapping['display']
        }
    
    # Fuzzy matching for comprehensive reports
    for key, mapping in PROPERTY_MAPPINGS.items():
        if clean_code in key or key in clean_code:
            return {
                'code': key,
                'name': mapping['name'],
                'display': mapping['display']
            }
    
    return None


def _suggest_filename_fixes(filename: str) -> List[str]:
    """Suggest possible fixes for unrecognized filenames"""
    suggestions = []
    
    # Check for common issues
    if not filename.lower().endswith('.xlsx'):
        suggestions.append("File should have .xlsx extension")
    
    # Check if it might be a report type with wrong format
    lower_filename = filename.lower()
    if 'box' in lower_filename and 'score' in lower_filename:
        suggestions.append("Try: ResAnalytics_Box_Score_Summary_{property_code}.xlsx")
    elif 'work' in lower_filename and 'order' in lower_filename:
        suggestions.append("Try: Work_Order_Report_{property_code}.xlsx")
    elif 'unit' in lower_filename and 'availability' in lower_filename:
        suggestions.append("Try: ResAnalytics_Unit_Availability_Details_{property_code}.xlsx")
    elif 'market' in lower_filename and 'rent' in lower_filename:
        suggestions.append("Try: ResAnalytics_Market_Rent_Schedule_{property_code}.xlsx")
    elif 'lease' in lower_filename and 'expiration' in lower_filename:
        suggestions.append("Try: ResAnalytic_Lease_Expiration_{property_code}.xlsx")
    elif 'delinquency' in lower_filename:
        suggestions.append("Try: ResARAnalytics_Delinquency_Summary_{property_code}.xlsx")
    elif 'make' in lower_filename and 'ready' in lower_filename:
        suggestions.append("Try: Pending_Make_Ready_Unit_Details._{property_code}.xlsx")
    elif 'residents' in lower_filename and 'notice' in lower_filename:
        suggestions.append("Try: Residents_on_Notice_{property_code}.xlsx")
    elif 'budget' in lower_filename:
        suggestions.append("Try: Budget_Comparison_{property_code}_{additional_info}.xlsx")
    
    return suggestions


def analyze_bulk_upload(filenames: List[str]) -> Dict[str, Any]:
    """
    Analyze multiple filenames for bulk upload.
    Enhanced version that consolidates filename_analyzer functionality.
    
    Args:
        filenames: List of filenames to analyze
        
    Returns:
        Dictionary organized by property with analysis results
    """
    results = {
        'valid_files': [],
        'invalid_files': [],
        'by_property': {}
    }
    
    for filename in filenames:
        analysis = analyze_filename(filename)
        
        if analysis.is_valid:
            results['valid_files'].append(analysis)
            
            # Group by property
            prop_key = analysis.property_code
            if prop_key not in results['by_property']:
                results['by_property'][prop_key] = {
                    'property_name': analysis.property_name,
                    'files': []
                }
            results['by_property'][prop_key]['files'].append(analysis)
        else:
            results['invalid_files'].append(analysis)
    
    return results
