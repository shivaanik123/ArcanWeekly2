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
    
    # Try different possible sheet names for occupancy data
    xl_file = pd.ExcelFile(file_path)
    occupancy_sheet_name = None
    
    # Check for common occupancy sheet names
    possible_names = ['Occupancy', 'Occ', 'Occupancy Data']
    for name in possible_names:
        if name in xl_file.sheet_names:
            occupancy_sheet_name = name
            break
    
    if not occupancy_sheet_name:
        print(f"No occupancy sheet found in {xl_file.sheet_names}")
        return {'metadata': {}, 'current_week': {}, 'historical': {}}
        
    df = pd.read_excel(file_path, sheet_name=occupancy_sheet_name, header=None)
    
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
    """Parse the Financial sheet for financial trends including rent data."""
    
    result = {
        'current_week': {},
        'historical': {}
    }
    
    try:
        # Try different possible sheet names for financial data
        xl_file = pd.ExcelFile(file_path)
        financial_sheet_name = None
        
        # Check for common financial sheet names
        possible_names = ['Financial', 'Fin', 'Finance']
        for name in possible_names:
            if name in xl_file.sheet_names:
                financial_sheet_name = name
                break
        
        if not financial_sheet_name:
            print(f"No financial sheet found in {xl_file.sheet_names}")
            return result
            
        df = pd.read_excel(file_path, sheet_name=financial_sheet_name, header=None)
        
        # Check which format this report uses and extract historical data accordingly
        historical_rent_data = []
        
        # Check if this is Marbella format by looking for dates in column 12
        has_date_column = False
        if df.shape[1] > 12:
            for i in range(2, min(10, len(df))):  # Check first few rows
                date_cell = df.iloc[i, 12] if df.shape[1] > 12 else None
                if pd.notna(date_cell) and hasattr(date_cell, 'year'):
                    has_date_column = True
                    break
        
        # Format 1: Marbella-style with dates in column 12 (time-series data)
        if has_date_column:
            for i in range(2, len(df)):
                try:
                    # Check if we have a valid date in column 12
                    date_cell = df.iloc[i, 12] if df.shape[1] > 12 else None
                    if pd.notna(date_cell) and hasattr(date_cell, 'year'):
                        # Extract rent data from columns 13 and 14
                        market_rent = df.iloc[i, 13] if df.shape[1] > 13 and not pd.isna(df.iloc[i, 13]) else 0
                        occupied_rent = df.iloc[i, 14] if df.shape[1] > 14 and not pd.isna(df.iloc[i, 14]) else 0
                        revenue = df.iloc[i, 15] if df.shape[1] > 15 and not pd.isna(df.iloc[i, 15]) else 0
                        expenses = df.iloc[i, 16] if df.shape[1] > 16 and not pd.isna(df.iloc[i, 16]) else 0
                        collections = df.iloc[i, 19] if df.shape[1] > 19 and not pd.isna(df.iloc[i, 19]) else 0
                        
                        # Convert to float if they're strings
                        try:
                            market_rent = float(str(market_rent).replace(',', '').replace('$', ''))
                        except (ValueError, TypeError):
                            market_rent = 0
                            
                        try:
                            occupied_rent = float(str(occupied_rent).replace(',', '').replace('$', ''))
                        except (ValueError, TypeError):
                            occupied_rent = 0
                        
                        rent_data = {
                            'date': date_cell,
                            'market_rent': market_rent,
                            'occupied_rent': occupied_rent,
                            'revenue': float(revenue) if revenue != 0 else 0,
                            'expenses': float(expenses) if expenses != 0 else 0,
                            'collections': float(collections) if collections != 0 else 0
                        }
                        
                        historical_rent_data.append(rent_data)
                        
                except Exception as e:
                    continue  # Skip problematic rows
        
        # Format 2: 55 PHARR-style with monthly columns (limited historical data)
        else:
            try:
                from datetime import datetime
                current_year = datetime.now().year
                
                # Check for month headers in row 4
                month_cols = []
                for col in range(df.shape[1]):
                    cell_val = df.iloc[4, col] if len(df) > 4 else None
                    if pd.notna(cell_val) and str(cell_val).upper() in ['JUNE', 'MAY', 'APRIL', 'MARCH', 'FEBRUARY', 'JANUARY']:
                        month_name = str(cell_val).upper()
                        month_mapping = {'JANUARY': 1, 'FEBRUARY': 2, 'MARCH': 3, 'APRIL': 4, 'MAY': 5, 'JUNE': 6}
                        if month_name in month_mapping:
                            month_num = month_mapping[month_name]
                            month_cols.append((col, month_num, month_name))
                
                # Extract revenue and expense data for each month
                for col, month_num, month_name in month_cols:
                    try:
                        revenue = 0
                        expenses = 0
                        
                        # Look for TOTAL INCOME and calculate total expenses
                        for row in range(len(df)):
                            cell_val = df.iloc[row, 1] if df.shape[1] > 1 else None
                            if pd.notna(cell_val):
                                cell_str = str(cell_val).upper()
                                if 'TOTAL INCOME' in cell_str:
                                    revenue_val = df.iloc[row, col] if df.shape[1] > col else None
                                    if pd.notna(revenue_val):
                                        try:
                                            revenue = float(str(revenue_val).replace(',', ''))
                                        except (ValueError, TypeError):
                                            revenue = 0
                        
                        # Calculate total expenses by summing expense categories
                        expense_categories = ['PAYROLL', 'MANAGEMENT FEE', 'GENERAL', 'REPAIRS', 'MAKE READY']
                        for row in range(len(df)):
                            cell_val = df.iloc[row, 1] if df.shape[1] > 1 else None
                            if pd.notna(cell_val):
                                cell_str = str(cell_val).upper()
                                for category in expense_categories:
                                    if category in cell_str:
                                        expense_val = df.iloc[row, col] if df.shape[1] > col else None
                                        if pd.notna(expense_val):
                                            try:
                                                expenses += float(str(expense_val).replace(',', ''))
                                            except (ValueError, TypeError):
                                                pass
                        
                        if revenue > 0 or expenses > 0:
                            historical_rent_data.append({
                                'date': datetime(current_year, month_num, 1),
                                'market_rent': 0,  # Not available in this format
                                'occupied_rent': 0,  # Not available in this format
                                'revenue': revenue,
                                'expenses': expenses,
                                'collections': 0  # Not available in this format
                            })
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"Error parsing 55 PHARR format: {e}")
        
        # Store historical data
        result['historical']['financial_trends'] = {
            'rent_data': historical_rent_data
        }
        result['historical']['rent_data'] = historical_rent_data
        
        # Set current week data to the most recent rent data if available
        if historical_rent_data:
            latest_rent = historical_rent_data[-1]
            result['current_week']['market_rent'] = latest_rent['market_rent']
            result['current_week']['occupied_rent'] = latest_rent['occupied_rent']
        
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
    test_file = "/Users/jsai23/Workspace/Arcan/data/Comprehensive Reports/Comprehensive Reports/Marbella Weekly Report.xlsx"
    
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
