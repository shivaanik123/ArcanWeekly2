"""
Parser for ResAnalytics Unit Availability Details reports.

Pattern: ResAnalytics_Unit*
Example: ResAnalytics_Unit_Availability_Details_marbla.xlsx
"""

import pandas as pd
import re
from typing import Dict, Any, Optional, List


def parse_resanalytics_unit_availability(file_path: str) -> Dict[str, Any]:
    """
    Parse ResAnalytics Unit Availability Details Excel file.
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        Dictionary containing parsed data with metadata and dataframes
    """
    
    # Read the Excel file without headers to analyze structure
    df_raw = pd.read_excel(file_path, sheet_name=0, header=None)
    
    # Extract metadata from header rows
    metadata = {}
    
    # Property name (row 1)
    property_match = re.search(r'(\w+)\s*\((\w+)\)', str(df_raw.iloc[1, 0]))
    if property_match:
        metadata['property_name'] = property_match.group(1)
        metadata['property_code'] = property_match.group(2)
    
    # As of date (row 2)
    date_match = re.search(r'As Of: (.+)', str(df_raw.iloc[2, 0]))
    if date_match:
        metadata['as_of_date'] = date_match.group(1)
    
    # Other settings
    for i in range(3, 6):
        if i < len(df_raw):
            cell_value = str(df_raw.iloc[i, 0])
            if 'Pre-Leased:' in cell_value:
                metadata['showing_pre_leased'] = 'Yes' in cell_value
            elif 'Occupied:' in cell_value:
                metadata['showing_occupied'] = 'Yes' in cell_value
            elif 'Group By:' in cell_value:
                metadata['group_by'] = cell_value.split('Group By:')[1].strip()
    
    # Find the header rows (Unit availability data has multi-row headers)
    header_start = None
    for i, row in df_raw.iterrows():
        if 'Unit' in str(row.iloc[0]) and 'Resident' in str(row.iloc[1]):
            header_start = i
            break
    
    data_sections = {}
    
    if header_start is not None:
        # Extract multi-row headers (typically 2 rows)
        header_row1 = df_raw.iloc[header_start, :].fillna('').astype(str).tolist()
        header_row2 = df_raw.iloc[header_start + 1, :].fillna('').astype(str).tolist()
        
        # Combine headers intelligently
        headers = []
        for i, (h1, h2) in enumerate(zip(header_row1, header_row2)):
            if h1.strip() and h2.strip():
                if h1.strip() == h2.strip():
                    headers.append(h1.strip())
                else:
                    headers.append(f"{h1.strip()} {h2.strip()}".strip())
            elif h1.strip():
                headers.append(h1.strip())
            elif h2.strip():
                headers.append(h2.strip())
            else:
                headers.append(f"Column_{i}")
        
        # Remove empty trailing columns
        while headers and headers[-1].startswith('Column_'):
            headers.pop()
        
        # Find different sections in the data
        current_section = None
        sections_data = {}
        
        for i in range(header_start + 2, len(df_raw)):
            row_data = df_raw.iloc[i, :len(headers)].fillna('').astype(str).tolist()
            first_cell = row_data[0].strip() if row_data else ''
            
            # Check if this is a section header
            if first_cell and ' - ' in first_cell and all(not cell.strip() for cell in row_data[1:3]):
                current_section = first_cell
                sections_data[current_section] = []
            elif first_cell and any(cell.strip() for cell in row_data):
                # This is actual data
                if current_section:
                    sections_data[current_section].append(row_data)
        
        # Convert sections to DataFrames
        for section_name, section_data in sections_data.items():
            if section_data:
                section_df = pd.DataFrame(section_data, columns=headers)
                
                # Clean up numeric columns
                for col in section_df.columns:
                    if 'rent' in col.lower() or 'deposit' in col.lower():
                        # Try to convert rent/deposit columns to numeric
                        section_df[col] = section_df[col].str.replace(r'[,$]', '', regex=True)
                        section_df[col] = pd.to_numeric(section_df[col], errors='coerce')
                
                data_sections[section_name] = section_df
        
        metadata['sections_found'] = list(data_sections.keys())
        metadata['total_units'] = sum(len(df) for df in data_sections.values())
    
    return {
        'metadata': metadata,
        'data_sections': data_sections,
        'file_path': file_path,
        'parser_type': 'resanalytics_unit_availability'
    }


def identify_resanalytics_unit_file(filename: str) -> bool:
    """
    Check if filename matches ResAnalytics Unit pattern.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        True if file matches pattern, False otherwise
    """
    # Remove property identifier and extension for pattern matching
    base_name = re.sub(r'_[a-z]+\.xlsx$', '', filename.lower())
    return base_name.startswith('resanalytics_unit')


if __name__ == "__main__":
    # Test the parser
    test_file = "/Users/jsai23/Workspace/Arcan/data/08_04_2025/Marbella /ResAnalytics_Unit_Availability_Details_marbla.xlsx"
    result = parse_resanalytics_unit_availability(test_file)
    print("Metadata:", result['metadata'])
    print("Data sections:", list(result['data_sections'].keys()))
    for section_name, df in result['data_sections'].items():
        print(f"{section_name}: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
