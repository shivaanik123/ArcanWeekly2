"""
Intelligent Filename Analyzer for Bulk ETL Report Uploads
Automatically detects report types and property codes from filenames
"""

import re
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

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

class FilenameAnalyzer:
    """Analyzes ETL report filenames to extract metadata"""
    
    # Comprehensive report type patterns
    REPORT_PATTERNS = {
        'resanalytics_box': {
            'patterns': [
                r'^ResAnalytics_Box_Score_Summary_([^.]+)\.xlsx$',
                r'^ResAnalytics_Box.*?_([^.]+)\.xlsx$'
            ],
            'description': 'ResAnalytics Box Score Summary',
            'priority': 1
        },
        'work_order': {
            'patterns': [
                r'^Work_Order_Report_([^.]+)\.xlsx$',
                r'^Work_Order.*?_([^.]+)\.xlsx$'
            ],
            'description': 'Work Order Report',
            'priority': 1
        },
        'resanalytics_unit': {
            'patterns': [
                r'^ResAnalytics_Unit_Availability_Details_([^.]+)\.xlsx$',
                r'^ResAnalytics_Unit.*?_([^.]+)\.xlsx$'
            ],
            'description': 'ResAnalytics Unit Availability Details',
            'priority': 1
        },
        'resanalytics_market': {
            'patterns': [
                r'^ResAnalytics_Market_Rent_Schedule_([^.]+)\.xlsx$',
                r'^ResAnalytics_Market.*?_([^.]+)\.xlsx$'
            ],
            'description': 'ResAnalytics Market Rent Schedule',
            'priority': 1
        },
        'resanalytic_lease': {
            'patterns': [
                r'^ResAnalytic_Lease_Expiration_([^.]+)\.xlsx$',
                r'^ResAnalytic_Lease.*?_([^.]+)\.xlsx$'
            ],
            'description': 'ResAnalytic Lease Expiration',
            'priority': 1
        },
        'resaranalytics_delinquency': {
            'patterns': [
                r'^ResARAnalytics_Delinquency_Summary_([^.]+)\.xlsx$',
                r'^ResARAnalytics_Delinquency.*?_([^.]+)\.xlsx$'
            ],
            'description': 'ResARAnalytics Delinquency Summary',
            'priority': 1
        },
        'pending_make': {
            'patterns': [
                r'^Pending_Make_Ready_Unit_Details\._([^.]+)\.xlsx$',
                r'^Pending_Make.*?_([^.]+)\.xlsx$'
            ],
            'description': 'Pending Make Ready Unit Details',
            'priority': 1
        },
        'residents_on_notice': {
            'patterns': [
                r'^Residents_on_Notice_([^.]+)\.xlsx$',
                r'^Residents.*?_([^.]+)\.xlsx$'
            ],
            'description': 'Residents on Notice Report',
            'priority': 1
        },
        'budget_comparison': {
            'patterns': [
                r'^Budget_Comparison.*?_([^_]+)_.*\.xlsx$',
                r'^Budget.*?_([^_]+)_.*\.xlsx$'
            ],
            'description': 'Budget Comparison Report',
            'priority': 2
        },
        'comprehensive_weekly': {
            'patterns': [
                r'^(.+?)\s+Weekly\s+Report.*\.xlsx$',
                r'^(.+?)Weekly.*\.xlsx$'
            ],
            'description': 'Comprehensive Weekly Report',
            'priority': 3
        }
    }
    
    # Property code mappings (from property_config.py)
    PROPERTY_MAPPINGS = {
        # Standard codes
        '55pharr': {'name': '55 Pharr', 'display': '55 Pharr'},
        'marbla': {'name': 'Marbella', 'display': 'Marbella'},
        'manwes': {'name': 'Manchester at Weslyn', 'display': 'Manchester at Weslyn'},
        'tapeprk': {'name': 'Tapestry Park', 'display': 'Tapestry Park'},
        'haven': {'name': 'Haven', 'display': 'Haven'},
        'hampec': {'name': 'Hamptons at East Cobb', 'display': 'Hamptons at East Cobb'},
        'talloak': {'name': 'Tall Oaks', 'display': 'Tall Oaks'},
        'colwds': {'name': 'Colony Woods', 'display': 'Colony Woods'},
        'marshp': {'name': 'Marsh Point', 'display': 'Marsh Point'},
        'capella2': {'name': 'Capella', 'display': 'Capella'},
        'emersn': {'name': 'Emerson 1600', 'display': 'Emerson 1600'},
        'wdlndcm': {'name': 'Woodland Commons', 'display': 'Woodland Commons'},
        'turn': {'name': 'The Turn', 'display': 'The Turn'},
        'portico': {'name': 'Portico at Lanier', 'display': 'Portico at Lanier'},
        'georget': {'name': 'Georgetown', 'display': 'Georgetown'},
        'longvw': {'name': 'Longview', 'display': 'Longview'},
        'kenplc': {'name': 'Kensington Place', 'display': 'Kensington Place'},
        'perryh': {'name': 'Perry Heights', 'display': 'Perry Heights'},
        'abbeylk': {'name': 'Abbey Lake', 'display': 'Abbey Lake'},
        
        # Alternative formats found in comprehensive reports
        '55 pharr': {'name': '55 Pharr', 'display': '55 Pharr'},
        'abbey lake': {'name': 'Abbey Lake', 'display': 'Abbey Lake'},
        'capella': {'name': 'Capella', 'display': 'Capella'},
        'colony woods': {'name': 'Colony Woods', 'display': 'Colony Woods'},
        'emerson 1600': {'name': 'Emerson 1600', 'display': 'Emerson 1600'},
        'georgetown apartments': {'name': 'Georgetown', 'display': 'Georgetown'},
        'hamptons': {'name': 'Hamptons at East Cobb', 'display': 'Hamptons at East Cobb'},
        'haven': {'name': 'Haven', 'display': 'Haven'},
        'kensington': {'name': 'Kensington Place', 'display': 'Kensington Place'},
        'longview': {'name': 'Longview', 'display': 'Longview'},
        'manchester': {'name': 'Manchester at Weslyn', 'display': 'Manchester at Weslyn'},
        'marbella': {'name': 'Marbella', 'display': 'Marbella'},
        'marsh point': {'name': 'Marsh Point', 'display': 'Marsh Point'},
        'perry heights': {'name': 'Perry Heights', 'display': 'Perry Heights'},
        'portico at lanier': {'name': 'Portico at Lanier', 'display': 'Portico at Lanier'},
        'tall oaks': {'name': 'Tall Oaks', 'display': 'Tall Oaks'},
        'tapestry park': {'name': 'Tapestry Park', 'display': 'Tapestry Park'},
        'the hangar at ransley station': {'name': 'The Hangar', 'display': 'The Hangar at Ransley Station'},
        'the turn': {'name': 'The Turn', 'display': 'The Turn'},
        'woodland common apartments': {'name': 'Woodland Commons', 'display': 'Woodland Commons'}
    }
    
    def analyze_filename(self, filename: str) -> FileAnalysisResult:
        """
        Analyze a filename to extract report type and property information
        
        Args:
            filename: The filename to analyze
            
        Returns:
            FileAnalysisResult with extracted information
        """
        # Clean filename
        clean_filename = filename.strip()
        
        # Try each report pattern
        for report_type, pattern_info in self.REPORT_PATTERNS.items():
            for pattern in pattern_info['patterns']:
                match = re.match(pattern, clean_filename, re.IGNORECASE)
                if match:
                    property_code_raw = match.group(1).strip()
                    
                    # Normalize property code
                    normalized_property = self._normalize_property_code(property_code_raw)
                    
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
            suggested_fixes=self._suggest_filename_fixes(filename)
        )
    
    def _normalize_property_code(self, raw_code: str) -> Optional[Dict[str, str]]:
        """Normalize property code to standard format"""
        
        # Clean the input
        clean_code = raw_code.lower().strip()
        
        # Remove common suffixes that might appear
        suffixes_to_remove = ['_2', '_1', ' (1)', ' (2)']
        for suffix in suffixes_to_remove:
            if clean_code.endswith(suffix.lower()):
                clean_code = clean_code[:-len(suffix)]
        
        # Direct lookup
        if clean_code in self.PROPERTY_MAPPINGS:
            mapping = self.PROPERTY_MAPPINGS[clean_code]
            return {
                'code': clean_code,
                'name': mapping['name'],
                'display': mapping['display']
            }
        
        # Fuzzy matching for comprehensive reports
        for key, mapping in self.PROPERTY_MAPPINGS.items():
            if clean_code in key or key in clean_code:
                return {
                    'code': key,
                    'name': mapping['name'],
                    'display': mapping['display']
                }
        
        return None
    
    def _suggest_filename_fixes(self, filename: str) -> List[str]:
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
    
    def analyze_bulk_upload(self, filenames: List[str]) -> Dict[str, List[FileAnalysisResult]]:
        """
        Analyze multiple filenames for bulk upload
        
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
            analysis = self.analyze_filename(filename)
            
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
    
    def get_supported_patterns(self) -> List[Dict[str, str]]:
        """Get list of supported filename patterns for user reference"""
        patterns = []
        for report_type, info in self.REPORT_PATTERNS.items():
            patterns.append({
                'report_type': report_type,
                'description': info['description'],
                'example_pattern': info['patterns'][0].replace('([^.]+)', '{property_code}').replace('(.+?)', '{property_name}')
            })
        return patterns

# Usage example
if __name__ == "__main__":
    analyzer = FilenameAnalyzer()
    
    # Test with some sample filenames
    test_files = [
        "ResAnalytics_Box_Score_Summary_marbla.xlsx",
        "Work_Order_Report_55pharr.xlsx",
        "ResAnalytics_Unit_Availability_Details_marbla.xlsx",
        "invalid_filename.xlsx"
    ]
    
    for filename in test_files:
        result = analyzer.analyze_filename(filename)
        print(f"{filename}: {result}")
