"""
Parser for ResAnalytics Box Score Summary reports.

Pattern: ResAnalytics_Box*
Example: ResAnalytics_Box_Score_Summary_marbla.xlsx
"""

import pandas as pd
import re
from typing import Dict, Any, Optional


def parse_resanalytics_box_score(file_path: str) -> Dict[str, Any]:
    """
    Parse ResAnalytics Box Score Summary Excel file.
    Extracts all three main sections: Availability, Resident Activity, and Conversion Ratios
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        Dictionary containing parsed data with metadata and dataframes
    """
    
    # Read the Excel file without headers to analyze structure
    df_raw = pd.read_excel(file_path, sheet_name=0, header=None)
    
    # Extract metadata from header rows
    metadata = {}
    
    # Property name - look in first few rows
    for i in range(min(5, len(df_raw))):
        cell_value = str(df_raw.iloc[i, 0])
        property_match = re.search(r'(\w+)\s*\((\w+)\)', cell_value)
        if property_match:
            metadata['property_name'] = property_match.group(1)
            metadata['property_code'] = property_match.group(2)
            break
    
    # Date range - look for date patterns
    for i in range(min(10, len(df_raw))):
        cell_value = str(df_raw.iloc[i, 0])
        date_match = re.search(r'Date.*?=.*?([0-9/\-]+.*?[0-9/\-]+)', cell_value)
        if date_match:
            metadata['date_range'] = date_match.group(1)
            break
    
    # Find data sections using flexible pattern matching
    data_sections = {}
    
    # Define section patterns - flexible matching
    section_patterns = {
        'availability': ['availability', 'avail'],
        'resident_activity': ['resident', 'activity'],
        'conversion_ratios': ['conversion', 'ratios']
    }
    
    # Find all sections
    section_locations = {}
    for i, row in df_raw.iterrows():
        first_cell = str(row.iloc[0]).lower().strip()
        
        for section_name, patterns in section_patterns.items():
            # For conversion_ratios, need both patterns in same cell
            if section_name == 'conversion_ratios':
                if all(pattern in first_cell for pattern in patterns):
                    section_locations[section_name] = i
            else:
                # For other sections, any pattern matches
                if any(pattern in first_cell for pattern in patterns):
                    section_locations[section_name] = i
    
    # Extract each section
    for section_name, start_row in section_locations.items():
        try:
            section_data = _extract_section_data(df_raw, start_row, section_name)
            if section_data is not None and not section_data.empty:
                data_sections[section_name] = section_data
        except Exception as e:
            print(f"Warning: Could not parse {section_name} section: {e}")
    
    return {
        'metadata': metadata,
        'data_sections': data_sections,
        'file_path': file_path,
        'parser_type': 'resanalytics_box_score'
    }


def _extract_section_data(df_raw: pd.DataFrame, start_row: int, section_name: str) -> Optional[pd.DataFrame]:
    """
    Extract data from a specific section of the Box Score file.
    
    Args:
        df_raw: Raw dataframe
        start_row: Row where section starts
        section_name: Name of the section being parsed
        
    Returns:
        DataFrame with section data or None if parsing fails
    """
    
    # Find the header row (usually 1-3 rows after section title)
    header_row = None
    best_score = 0
    
    for i in range(start_row + 1, min(start_row + 5, len(df_raw))):
        if i < len(df_raw):
            # Look for a row that looks like headers (contains common column names)
            row_data = df_raw.iloc[i, :].fillna('').astype(str).tolist()
            joined_row = ' '.join(row_data).lower()
            
            # Score the row based on how many header words it contains
            header_words = ['code', 'name', 'units', 'calls', 'move', 'rent', 'contact', 'walk', 'email', 'web', 'sms']
            score = sum(1 for word in header_words if word in joined_row)
            
            # Prefer rows that start with 'Code' (typical first column)
            if row_data[0].lower().strip() == 'code':
                score += 5
            
            if score > best_score:
                best_score = score
                header_row = i
    
    if header_row is None:
        return None
    
    # Extract headers
    headers = df_raw.iloc[header_row, :].fillna('').astype(str).tolist()
    
    # Clean and limit headers
    clean_headers = []
    for h in headers:
        h = h.strip()
        if h and not h.startswith('Unnamed'):
            clean_headers.append(h)
        else:
            break  # Stop at first empty header
    
    if not clean_headers:
        return None
    
    # Extract data rows
    data_rows = []
    for i in range(header_row + 1, len(df_raw)):
        row_data = df_raw.iloc[i, :len(clean_headers)].fillna('').astype(str).tolist()
        
        # Stop at empty row or next section
        if not any(cell.strip() for cell in row_data):
            continue  # Skip empty rows
        
        # Stop if we hit another section (contains section keywords)  
        first_cell = row_data[0].lower().strip()
        if (any(keyword in first_cell for keyword in ['availability', 'resident', 'activity']) or
            ('conversion' in first_cell and 'ratios' in first_cell)):
            break
        
        data_rows.append(row_data)
        
        # Stop if we see "Total" row (usually end of section)
        if 'total' in first_cell and len(data_rows) > 2:  # Need at least some data rows
            break
    
    if not data_rows:
        return None
    
    # Create DataFrame
    df = pd.DataFrame(data_rows, columns=clean_headers)
    
    # Clean up numeric columns based on section type
    if section_name == 'availability':
        numeric_patterns = ['sq ft', 'rent', 'units', 'occupied', 'vacant']
    elif section_name == 'resident_activity':
        numeric_patterns = ['units', 'move', 'reverse', 'cancel', 'notice', 'term']
    elif section_name == 'conversion_ratios':
        numeric_patterns = ['calls', 'walk', 'email', 'sms', 'web', 'chat', 'contact', 'other']
    else:
        numeric_patterns = ['units', 'count', 'total']
    
    for col in df.columns:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in numeric_patterns):
            try:
                # Clean numeric data
                df[col] = df[col].str.replace(',', '').str.replace('$', '').str.strip()
                df[col] = df[col].replace('', '0')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            except:
                pass  # Keep as string if conversion fails
    
    return df


def identify_resanalytics_box_file(filename: str) -> bool:
    """
    Check if filename matches ResAnalytics Box Score pattern.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        True if file matches pattern, False otherwise
    """
    # Remove property identifier and extension for pattern matching
    base_name = re.sub(r'_[a-z0-9]+\.xlsx$', '', filename.lower())
    return base_name.startswith('resanalytics_box')


if __name__ == "__main__":
    # Test the parser
    test_file = "/Users/shivaanikomanduri/ArcanClean/data/08_04_2025/Marbella /ResAnalytics_Box_Score_Summary_marbla.xlsx"
    result = parse_resanalytics_box_score(test_file)
    print("Metadata:", result['metadata'])
    print("Data sections:", list(result['data_sections'].keys()))
    if 'availability' in result['data_sections']:
        print("Availability data shape:", result['data_sections']['availability'].shape)
        print("Availability columns:", result['data_sections']['availability'].columns.tolist())
