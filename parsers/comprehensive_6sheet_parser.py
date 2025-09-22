"""
Parser for 6-Sheet Comprehensive Reports (55 PHARR format)

Sheets: ['INPUT', 'Cover', 'Occ', 'Fin', 'Col', 'Rent Cash']
Examples: 55 PHARR, and similar properties with this format
"""

import pandas as pd
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np


def parse_comprehensive_6sheet_report(file_path: str) -> Dict[str, Any]:
    """
    Parse comprehensive 6-sheet report format.
    
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
        'parser_type': 'comprehensive_6sheet'
    }
    
    try:
        # Parse INPUT sheet for basic metadata and current data
        input_data = parse_input_sheet(file_path)
        result['metadata'].update(input_data['metadata'])
        result['current_week_data'].update(input_data['current_week'])
        result['historical_data'].update(input_data['historical'])
        
        # Parse Fin sheet for historical financial data
        fin_data = parse_fin_sheet(file_path)
        result['historical_data'].update(fin_data['historical'])
        result['current_week_data'].update(fin_data['current_week'])
        
        # Parse Rent Cash sheet for rent data
        rent_data = parse_rent_cash_sheet(file_path)
        result['current_week_data'].update(rent_data['current_week'])
        
        # Parse Col sheet for collections data
        col_data = parse_col_sheet(file_path)
        result['historical_data'].update(col_data['historical'])
        result['current_week_data'].update(col_data['current_week'])
        
        # Parse Occ sheet for occupancy data (merge carefully to preserve INPUT sheet data)
        occ_data = parse_occ_sheet(file_path)
        result['current_week_data'].update(occ_data['current_week'])
        
        # Merge historical data carefully - don't overwrite existing occupancy data
        for key, value in occ_data['historical'].items():
            if key == 'weekly_occupancy_data' and key in result['historical_data']:
                # Don't overwrite existing occupancy data from INPUT sheet
                continue
            else:
                result['historical_data'][key] = value
        
    except Exception as e:
        result['error'] = f"Error parsing 6-sheet comprehensive report: {str(e)}"
    
    return result


def parse_input_sheet(file_path: str) -> Dict[str, Any]:
    """Parse the INPUT sheet for metadata and current week data."""
    
    result = {
        'metadata': {},
        'current_week': {},
        'historical': {}
    }
    
    try:
        df = pd.read_excel(file_path, sheet_name='INPUT', header=None)
        
        # Extract metadata from first few rows
        for i in range(min(20, len(df))):
            if df.shape[1] > 2:
                label = df.iloc[i, 0] if pd.notna(df.iloc[i, 0]) else ""
                value = df.iloc[i, 2] if pd.notna(df.iloc[i, 2]) else ""
                
                if isinstance(label, str):
                    label_upper = label.upper()
                    if 'PROPERTY' in label_upper:
                        result['metadata']['property_name'] = str(value)
                    elif 'LOCATION' in label_upper:
                        result['metadata']['location'] = str(value)
                    elif label_upper == 'UNITS':  # Exact match for "UNITS" row
                        try:
                            result['metadata']['total_units'] = int(value)
                        except (ValueError, TypeError):
                            pass
                    elif 'WEEK END' in label_upper:
                        result['metadata']['week_end'] = value
                    elif 'TOTAL OCCUPIED UNITS' in label_upper:
                        try:
                            result['current_week']['occupied_units'] = int(value)
                        except (ValueError, TypeError):
                            pass
                    elif 'VACANT RENTABLE UNIT' in label_upper:
                        try:
                            result['current_week']['vacant_units'] = int(value)
                        except (ValueError, TypeError):
                            pass
        
        # Calculate occupancy percentage
        if 'occupied_units' in result['current_week'] and 'total_units' in result['metadata']:
            occupied = result['current_week']['occupied_units']
            total = result['metadata']['total_units']
            if total > 0:
                result['current_week']['occupancy_percentage'] = (occupied / total) * 100
        
        # Extract historical occupancy data from HISTORICAL OCCUPANCY section (columns 12-13)
        historical_occupancy = []
        total_units = result['metadata'].get('total_units', 121)  # Default to 121 for 55 PHARR
        
        # Look for HISTORICAL OCCUPANCY section starting around column 12
        for i in range(1, len(df)):  # Start from row 1 (skip header)
            try:
                # Check if we have a date in column 12 and occupancy percentage in column 13
                date_cell = df.iloc[i, 12] if df.shape[1] > 12 else None
                occupancy_cell = df.iloc[i, 13] if df.shape[1] > 13 else None
                
                if pd.notna(date_cell) and pd.notna(occupancy_cell):
                    if hasattr(date_cell, 'year'):  # It's a date
                        try:
                            occupancy_pct = float(occupancy_cell) * 100  # Convert from decimal to percentage
                            occupied_units = int((occupancy_pct / 100) * total_units)
                            
                            # Create week string for compatibility with existing code
                            week_str = date_cell.strftime('%m/%d')
                            
                            # Extract work order and make ready data from columns 46-47
                            work_orders = 0
                            make_readies = 0
                            
                            try:
                                if df.shape[1] > 46:
                                    wo_cell = df.iloc[i, 46]
                                    if pd.notna(wo_cell) and str(wo_cell).replace('.', '').isdigit():
                                        work_orders = int(float(wo_cell))
                            except (ValueError, TypeError):
                                pass
                                
                            try:
                                if df.shape[1] > 47:
                                    mr_cell = df.iloc[i, 47]
                                    if pd.notna(mr_cell) and str(mr_cell).replace('.', '').isdigit():
                                        make_readies = int(float(mr_cell))
                            except (ValueError, TypeError):
                                pass
                            
                            historical_occupancy.append({
                                'week': week_str,
                                'date': date_cell,
                                'occupied_units': occupied_units,
                                'total_units': total_units,
                                'occupancy_percentage': occupancy_pct,
                                'leased_percentage': occupancy_pct,  # Use same value for now
                                'projected_percentage': occupancy_pct,  # Use same value for now
                                'work_orders_count': work_orders,
                                'make_readies_count': make_readies
                            })
                            
                        except (ValueError, TypeError):
                            continue
                            
            except Exception as e:
                continue
        
        # Sort by date
        historical_occupancy.sort(key=lambda x: x['date'])
        result['historical']['weekly_occupancy_data'] = historical_occupancy
        
        # Extract historical turnover data from HISTORICAL TURNOVER section (columns 15-16)
        historical_turnover = []
        
        for i in range(1, len(df)):  # Start from row 1 (skip header)
            try:
                # Check if we have a date in column 15 and turnover rate in column 16
                date_cell = df.iloc[i, 15] if df.shape[1] > 15 else None
                turnover_cell = df.iloc[i, 16] if df.shape[1] > 16 else None
                
                if pd.notna(date_cell) and pd.notna(turnover_cell):
                    if hasattr(date_cell, 'year'):  # It's a date
                        try:
                            turnover_rate = float(turnover_cell) * 100  # Convert from decimal to percentage
                            
                            historical_turnover.append({
                                'date': date_cell,
                                'turnover_rate': turnover_rate
                            })
                            
                        except (ValueError, TypeError):
                            continue
                            
            except Exception as e:
                continue
        
        # Sort by date
        historical_turnover.sort(key=lambda x: x['date'])
        result['historical']['turnover_data'] = historical_turnover
        
    except Exception as e:
        print(f"Warning: Could not parse INPUT sheet: {e}")
    
    return result


def parse_fin_sheet(file_path: str) -> Dict[str, Any]:
    """Parse the Fin sheet for historical financial data."""
    
    result = {
        'current_week': {},
        'historical': {}
    }
    
    try:
        df = pd.read_excel(file_path, sheet_name='Fin', header=None)
        
        # Find month headers (JUNE, MAY, APRIL, etc.)
        month_cols = []
        current_year = datetime.now().year
        
        for i in range(min(10, len(df))):
            for col in range(df.shape[1]):
                cell_val = df.iloc[i, col] if pd.notna(df.iloc[i, col]) else ""
                if isinstance(cell_val, str):
                    month_name = cell_val.upper().strip()
                    month_mapping = {
                        'JANUARY': 1, 'FEBRUARY': 2, 'MARCH': 3, 'APRIL': 4, 
                        'MAY': 5, 'JUNE': 6, 'JULY': 7, 'AUGUST': 8, 
                        'SEPTEMBER': 9, 'OCTOBER': 10, 'NOVEMBER': 11, 'DECEMBER': 12
                    }
                    if month_name in month_mapping:
                        month_cols.append((col, month_mapping[month_name], month_name))
        
        # Extract financial data for each month
        historical_data = []
        
        for col, month_num, month_name in month_cols:
            try:
                revenue = 0
                expenses = 0
                net_rental_income = 0
                other_income = 0
                
                # Look for specific financial line items
                for row in range(len(df)):
                    label = df.iloc[row, 1] if df.shape[1] > 1 and pd.notna(df.iloc[row, 1]) else ""
                    if isinstance(label, str):
                        label_upper = label.upper()
                        value = df.iloc[row, col] if df.shape[1] > col and pd.notna(df.iloc[row, col]) else 0
                        
                        try:
                            value = float(str(value).replace(',', '')) if value != 0 else 0
                        except (ValueError, TypeError):
                            value = 0
                        
                        if 'TOTAL INCOME' in label_upper:
                            revenue = value
                        elif 'NET RENTAL INCOME' in label_upper:
                            net_rental_income = value
                        elif 'OTHER INCOME' in label_upper:
                            other_income = value
                
                # Calculate total expenses by summing expense categories
                expense_categories = [
                    'PAYROLL', 'MANAGEMENT FEE', 'GENERAL', 'ADMIN', 'UTILITIES',
                    'REPAIRS', 'MAINT', 'CONTRACT', 'MAKE READY', 'RECREATION',
                    'MARKETING', 'INSURANCE', 'TAXES', 'LEGAL'
                ]
                
                for row in range(len(df)):
                    label = df.iloc[row, 1] if df.shape[1] > 1 and pd.notna(df.iloc[row, 1]) else ""
                    if isinstance(label, str):
                        label_upper = label.upper()
                        for category in expense_categories:
                            if category in label_upper and 'INCOME' not in label_upper:
                                value = df.iloc[row, col] if df.shape[1] > col and pd.notna(df.iloc[row, col]) else 0
                                try:
                                    expenses += float(str(value).replace(',', '')) if value != 0 else 0
                                except (ValueError, TypeError):
                                    pass
                
                if revenue > 0 or expenses > 0:
                    historical_data.append({
                        'date': datetime(current_year, month_num, 1),
                        'revenue': revenue,
                        'expenses': expenses,
                        'net_rental_income': net_rental_income,
                        'other_income': other_income,
                        'net_operating_income': revenue - expenses
                    })
                    
            except Exception as e:
                continue
        
        # Sort by date
        historical_data.sort(key=lambda x: x['date'])
        
        # Store historical data
        result['historical']['financial_trends'] = {
            'revenue_expenses': historical_data
        }
        result['historical']['rent_data'] = historical_data  # For compatibility
        
        # Set current week data to the most recent financial data
        if historical_data:
            latest = historical_data[-1]
            result['current_week']['revenue'] = latest['revenue']
            result['current_week']['expenses'] = latest['expenses']
            result['current_week']['net_operating_income'] = latest['net_operating_income']
        
    except Exception as e:
        print(f"Warning: Could not parse Fin sheet: {e}")
    
    return result


def parse_rent_cash_sheet(file_path: str) -> Dict[str, Any]:
    """Parse the Rent Cash sheet for rent and unit data."""
    
    result = {
        'current_week': {}
    }
    
    try:
        df = pd.read_excel(file_path, sheet_name='Rent Cash', header=None)
        
        # Look for TOTALS/AVERAGES row
        for row in range(len(df)):
            label = df.iloc[row, 1] if df.shape[1] > 1 and pd.notna(df.iloc[row, 1]) else ""
            if isinstance(label, str) and 'TOTALS' in label.upper():
                try:
                    # Extract market rent and in-place rent averages
                    market_rent = df.iloc[row, 6] if df.shape[1] > 6 and pd.notna(df.iloc[row, 6]) else 0
                    in_place_rent = df.iloc[row, 7] if df.shape[1] > 7 and pd.notna(df.iloc[row, 7]) else 0
                    vacant_units = df.iloc[row, 4] if df.shape[1] > 4 and pd.notna(df.iloc[row, 4]) else 0
                    
                    result['current_week']['market_rent'] = float(market_rent) if market_rent != 0 else 0
                    result['current_week']['occupied_rent'] = float(in_place_rent) if in_place_rent != 0 else 0
                    result['current_week']['vacant_units_rent'] = int(vacant_units) if vacant_units != 0 else 0
                    
                except (ValueError, TypeError):
                    pass
                break
        
    except Exception as e:
        print(f"Warning: Could not parse Rent Cash sheet: {e}")
    
    return result


def parse_col_sheet(file_path: str) -> Dict[str, Any]:
    """Parse the Col sheet for collections data."""
    
    result = {
        'current_week': {},
        'historical': {}
    }
    
    try:
        df = pd.read_excel(file_path, sheet_name='Col', header=None)
        
        # Look for collections data - this sheet structure needs to be analyzed more
        # For now, we'll extract what we can find
        collections_data = []
        
        # This is a placeholder - would need to see actual collections data structure
        result['historical']['collections_data'] = collections_data
        
    except Exception as e:
        print(f"Warning: Could not parse Col sheet: {e}")
    
    return result


def parse_occ_sheet(file_path: str) -> Dict[str, Any]:
    """Parse the Occ sheet for occupancy trends and current data."""
    
    result = {
        'current_week': {},
        'historical': {}
    }
    
    try:
        df = pd.read_excel(file_path, sheet_name='Occ', header=None)
        
        # Extract current week occupancy data
        for i in range(len(df)):
            for j in range(df.shape[1]):
                cell_val = df.iloc[i, j]
                if pd.notna(cell_val) and isinstance(cell_val, str):
                    cell_upper = cell_val.upper()
                    
                    # Look for occupancy percentages and unit counts
                    if 'TOTAL OCCUPIED PERCENTAGE' in cell_upper:
                        try:
                            occ_pct = df.iloc[i, j+1] if df.shape[1] > j+1 else None
                            if pd.notna(occ_pct):
                                result['current_week']['occupancy_percentage'] = float(occ_pct) * 100
                        except (ValueError, TypeError):
                            pass
                    
                    elif 'TOTAL LEASED PERCENTAGE' in cell_upper:
                        try:
                            leased_pct = df.iloc[i, j+1] if df.shape[1] > j+1 else None
                            if pd.notna(leased_pct):
                                result['current_week']['leased_percentage'] = float(leased_pct) * 100
                        except (ValueError, TypeError):
                            pass
                    
                    elif 'TOTAL OCCUPIED UNITS' in cell_upper:
                        try:
                            occ_units = df.iloc[i, j+1] if df.shape[1] > j+1 else None
                            if pd.notna(occ_units):
                                result['current_week']['occupied_units'] = int(float(occ_units))
                        except (ValueError, TypeError):
                            pass
                    
                    elif 'VACANT RENTABLE UNITS' in cell_upper:
                        try:
                            vacant_units = df.iloc[i, j+1] if df.shape[1] > j+1 else None
                            if pd.notna(vacant_units):
                                result['current_week']['vacant_units'] = int(float(vacant_units))
                        except (ValueError, TypeError):
                            pass
                    
                    elif 'LEASED VACANT UNITS' in cell_upper:
                        try:
                            leased_vacant = df.iloc[i, j+1] if df.shape[1] > j+1 else None
                            if pd.notna(leased_vacant):
                                result['current_week']['leased_vacant_units'] = int(float(leased_vacant))
                        except (ValueError, TypeError):
                            pass
        
        # Extract scheduled move-ins/move-outs (historical trend data)
        move_schedule = []
        for i in range(len(df)):
            date_col = None
            move_ins = None
            move_outs = None
            
            # Look for date and move data in the same row
            for j in range(df.shape[1]):
                cell_val = df.iloc[i, j]
                if pd.notna(cell_val):
                    if hasattr(cell_val, 'year'):  # It's a date
                        date_col = cell_val
                    elif isinstance(cell_val, str) and 'SCHEDULED MOVE' in cell_val.upper():
                        # This is a header row, skip
                        break
                    elif isinstance(cell_val, (int, float)) and date_col is not None:
                        # This might be move-in or move-out data
                        if move_ins is None:
                            move_ins = int(cell_val)
                        elif move_outs is None:
                            move_outs = int(cell_val)
                            # We have both, add to schedule
                            move_schedule.append({
                                'date': date_col,
                                'scheduled_move_ins': move_ins,
                                'scheduled_move_outs': move_outs
                            })
                            break
        
        result['historical']['move_schedule'] = move_schedule
        
        # Create basic occupancy trend data (we'll enhance this with INPUT sheet data)
        occupancy_data = []
        result['historical']['weekly_occupancy_data'] = occupancy_data
        
    except Exception as e:
        print(f"Warning: Could not parse Occ sheet: {e}")
    
    return result


def identify_comprehensive_6sheet_file(file_path: str) -> bool:
    """
    Check if file matches 6-sheet comprehensive report pattern.
    
    Args:
        file_path: Path to the file to check (can be filename or full path)
        
    Returns:
        True if file matches pattern, False otherwise
    """
    import os
    
    # Handle both filename and full path
    if os.path.exists(file_path):
        filename = os.path.basename(file_path)
        check_path = file_path
    else:
        filename = file_path
        check_path = file_path
    
    base_name = filename.lower()
    
    # Check for weekly report pattern and try to identify by sheet structure
    if 'weekly report' in base_name and base_name.endswith('.xlsx'):
        try:
            xl_file = pd.ExcelFile(check_path)
            sheets = set(xl_file.sheet_names)
            required_sheets = {'INPUT', 'Cover', 'Occ', 'Fin', 'Col', 'Rent Cash'}
            
            # If it has all 6 required sheets, it's likely this format
            if required_sheets.issubset(sheets):
                return True
        except:
            pass
    
    return False
