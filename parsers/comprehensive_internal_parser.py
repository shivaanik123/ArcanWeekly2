"""
Parser for Comprehensive Internal Reports (2-sheet format)

Examples: Marbella, Abbey Lake, Woodland Common, etc.
Sheets: ['Occupancy', 'Financial']
"""

import pandas as pd
import re
from typing import Dict, Any, List, Optional
from datetime import datetime


def parse_comprehensive_internal_report(file_path: str) -> Dict[str, Any]:
    """
    Parse comprehensive internal report with Occupancy and Financial sheets.
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        Dictionary containing parsed data with metadata and historical trends
    """
    
    result = {
        'metadata': {},
        'current_week_data': {},
        'historical_data': {},
        'file_path': file_path,
        'parser_type': 'comprehensive_internal'
    }
    
    try:
        # Parse Occupancy sheet
        occupancy_data = parse_occupancy_sheet(file_path)
        result['current_week_data'].update(occupancy_data['current_week'])
        result['historical_data'].update(occupancy_data['historical'])
        result['metadata'].update(occupancy_data['metadata'])
        
        # Parse Financial sheet
        financial_data = parse_financial_sheet(file_path)
        result['current_week_data'].update(financial_data['current_week'])
        result['historical_data'].update(financial_data['historical'])
        
    except Exception as e:
        result['error'] = f"Error parsing comprehensive internal report: {str(e)}"
    
    return result


def parse_occupancy_sheet(file_path: str) -> Dict[str, Any]:
    """Parse the Occupancy sheet for current and historical data."""
    
    df = pd.read_excel(file_path, sheet_name='Occupancy', header=None)
    
    result = {
        'metadata': {},
        'current_week': {},
        'historical': {}
    }
    
    # Extract metadata from header rows
    try:
        # Property info (rows 1-7)
        result['metadata']['property_name'] = str(df.iloc[1, 1]) if not pd.isna(df.iloc[1, 1]) else ''
        result['metadata']['total_units'] = int(df.iloc[2, 1]) if not pd.isna(df.iloc[2, 1]) else 0
        result['metadata']['models'] = int(df.iloc[3, 1]) if not pd.isna(df.iloc[3, 1]) else 0
        result['metadata']['office'] = int(df.iloc[4, 1]) if not pd.isna(df.iloc[4, 1]) else 0
        result['metadata']['location'] = str(df.iloc[6, 1]) if not pd.isna(df.iloc[6, 1]) else ''
        
        # Report date
        if not pd.isna(df.iloc[0, 5]):
            result['metadata']['report_date'] = df.iloc[0, 5]
            
    except Exception as e:
        print(f"Warning: Could not extract metadata: {e}")
    
    # Extract current week data (rows 15-18)
    try:
        result['current_week']['occupancy_percent'] = float(df.iloc[16, 4]) if not pd.isna(df.iloc[16, 4]) else 0.0
        result['current_week']['leased_percent'] = float(df.iloc[16, 5]) if not pd.isna(df.iloc[16, 5]) else 0.0
        result['current_week']['total_units'] = int(df.iloc[16, 7]) if not pd.isna(df.iloc[16, 7]) else 0
        result['current_week']['occupied_units'] = int(df.iloc[16, 8]) if not pd.isna(df.iloc[16, 8]) else 0
        result['current_week']['vacant_units'] = int(df.iloc[16, 9]) if not pd.isna(df.iloc[16, 9]) else 0
        result['current_week']['notice_units'] = int(df.iloc[16, 10]) if not pd.isna(df.iloc[16, 10]) else 0
        
        # 30-day projections (row 17-18)
        result['current_week']['projected_occupancy_30day'] = float(df.iloc[18, 4]) if not pd.isna(df.iloc[18, 4]) else 0.0
        result['current_week']['available_units'] = int(df.iloc[18, 5]) if not pd.isna(df.iloc[18, 5]) else 0
        result['current_week']['projected_move_ins_30day'] = int(df.iloc[18, 6]) if not pd.isna(df.iloc[18, 6]) else 0
        result['current_week']['projected_move_outs_30day'] = int(df.iloc[18, 8]) if not pd.isna(df.iloc[18, 8]) else 0
        result['current_week']['evictions_30day'] = int(df.iloc[18, 9]) if not pd.isna(df.iloc[18, 9]) else 0
        
    except Exception as e:
        print(f"Warning: Could not extract current week data: {e}")
    
    # Extract historical weekly data (rows 45-102 approximately)
    historical_weeks = []
    
    # Find the start of historical data by looking for the first date in column 13
    start_row = None
    for i in range(20, len(df)):
        if not pd.isna(df.iloc[i, 13]) and isinstance(df.iloc[i, 13], datetime):
            start_row = i
            break
    
    if start_row:
        for i in range(start_row, len(df)):
            try:
                # Check if we have a valid date in column 13
                if not pd.isna(df.iloc[i, 13]) and isinstance(df.iloc[i, 13], datetime):
                    week_data = {
                        'date': df.iloc[i, 13],
                        'occupancy_percent': float(df.iloc[i, 14]) if not pd.isna(df.iloc[i, 14]) else 0.0,
                        'leased_percent': float(df.iloc[i, 15]) if not pd.isna(df.iloc[i, 15]) else 0.0,
                        'projection_percent': float(df.iloc[i, 16]) if not pd.isna(df.iloc[i, 16]) else 0.0,
                        'make_readies_count': int(df.iloc[i, 17]) if not pd.isna(df.iloc[i, 17]) else 0,
                        'work_orders_count': int(df.iloc[i, 18]) if not pd.isna(df.iloc[i, 18]) else 0
                    }
                    historical_weeks.append(week_data)
                else:
                    # Stop when we reach empty rows
                    break
            except Exception as e:
                print(f"Warning: Could not parse row {i}: {e}")
                continue
    
    result['historical']['weekly_occupancy_data'] = historical_weeks
    
    return result


def parse_financial_sheet(file_path: str) -> Dict[str, Any]:
    """Parse the Financial sheet for financial trends."""
    
    result = {
        'current_week': {},
        'historical': {}
    }
    
    try:
        df = pd.read_excel(file_path, sheet_name='Financial', header=None)
        
        # Look for financial data patterns
        # This would need more analysis to identify the structure
        result['current_week']['financial_data'] = "Financial data parsing to be implemented"
        result['historical']['financial_trends'] = []
        
    except Exception as e:
        print(f"Warning: Could not parse financial sheet: {e}")
    
    return result


def identify_comprehensive_internal_file(filename: str) -> bool:
    """
    Check if filename matches comprehensive internal report pattern.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        True if file matches pattern, False otherwise
    """
    # Remove path if present
    base_name = filename.lower()
    
    # Check for weekly report pattern
    if 'weekly report' in base_name and base_name.endswith('.xlsx'):
        return True
    
    return False


if __name__ == "__main__":
    # Test the parser
    test_file = "/Users/shivaanikomanduri/ArcanClean/data/Comprehensive Reports/Comprehensive Reports/Marbella Weekly Report.xlsx"
    
    result = parse_comprehensive_internal_report(test_file)
    
    print("=== PARSER TEST RESULTS ===")
    print(f"Property: {result['metadata'].get('property_name', 'Unknown')}")
    print(f"Total Units: {result['metadata'].get('total_units', 0)}")
    print(f"Current Occupancy: {result['current_week_data'].get('occupancy_percent', 0):.2%}")
    print(f"Current Leased: {result['current_week_data'].get('leased_percent', 0):.2%}")
    print(f"Historical Data Points: {len(result['historical_data'].get('weekly_occupancy_data', []))}")
    
    if result['historical_data'].get('weekly_occupancy_data'):
        recent_data = result['historical_data']['weekly_occupancy_data'][-5:]  # Last 5 weeks
        print("\nRecent 5 weeks:")
        for week in recent_data:
            print(f"  {week['date'].strftime('%Y-%m-%d')}: {week['occupancy_percent']:.1%} occ, {week['leased_percent']:.1%} leased, {week['projection_percent']:.1%} proj, {week['make_readies_count']} MR, {week['work_orders_count']} WO")
