"""
Parser for Pending Make Ready Unit Details reports.

Pattern: Pending_Make*
Example: Pending_Make_Ready_Unit_Details._marbla.xlsx
"""

import pandas as pd
import re
from typing import Dict, Any


def parse_pending_make_ready(file_path: str) -> Dict[str, Any]:
    """
    Parse Pending Make Ready Unit Details Excel file.
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        Dictionary containing parsed data with metadata and dataframes
    """
    
    # Read the Excel file without headers to analyze structure
    df_raw = pd.read_excel(file_path, sheet_name=0, header=None)
    
    # Extract metadata from header rows
    metadata = {}
    
    # Extract property and date info from row 1
    if len(df_raw) > 1:
        filter_info = str(df_raw.iloc[1, 0])
        property_match = re.search(r'Property=(\w+)', filter_info)
        if property_match:
            metadata['property_code'] = property_match.group(1)
        
        date_match = re.search(r'Till Dates\([^)]+\)=(\d{2}/\d{2}/\d{4})', filter_info)
        if date_match:
            metadata['till_date'] = date_match.group(1)
    
    # Find the header rows (multi-row headers)
    header_start = None
    for i, row in df_raw.iterrows():
        if 'Property' in str(row.iloc[0]) and 'Date' in str(row.iloc[1]):
            header_start = i
            break
    
    make_ready_df = pd.DataFrame()
    
    if header_start is not None:
        # Extract multi-row headers
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
                break  # Stop at first empty column pair
        
        # Extract make ready data
        make_ready_data = []
        for i in range(header_start + 2, len(df_raw)):
            row_data = df_raw.iloc[i, :len(headers)].fillna('').astype(str).tolist()
            if any(cell.strip() for cell in row_data):  # Skip empty rows
                make_ready_data.append(row_data)
        
        if make_ready_data:
            make_ready_df = pd.DataFrame(make_ready_data, columns=headers)
            
            # Clean up data types
            for col in make_ready_df.columns:
                if 'bedrooms' in col.lower():
                    make_ready_df[col] = pd.to_numeric(make_ready_df[col], errors='coerce')
                elif 'date' in col.lower():
                    # Try to convert date columns
                    make_ready_df[col] = pd.to_datetime(make_ready_df[col], errors='coerce')
        
        metadata['pending_units'] = len(make_ready_df) if not make_ready_df.empty else 0
        
        # Summary statistics
        if not make_ready_df.empty:
            bedroom_col = next((col for col in make_ready_df.columns if 'bedrooms' in col.lower()), None)
            if bedroom_col:
                bedroom_summary = make_ready_df[bedroom_col].value_counts().to_dict()
                metadata['bedroom_breakdown'] = bedroom_summary
    
    return {
        'metadata': metadata,
        'make_ready_data': make_ready_df,
        'file_path': file_path,
        'parser_type': 'pending_make_ready'
    }


def identify_pending_make_file(filename: str) -> bool:
    """
    Check if filename matches Pending Make Ready pattern.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        True if file matches pattern, False otherwise
    """
    base_name = re.sub(r'_[a-z]+\.xlsx$', '', filename.lower())
    base_name = base_name.replace('._', '_')  # Handle the ._ pattern
    return base_name.startswith('pending_make')


if __name__ == "__main__":
    # Test the parser
    test_file = "/Users/shivaanikomanduri/ArcanClean/data/08_04_2025/Marbella /Pending_Make_Ready_Unit_Details._marbla.xlsx"
    result = parse_pending_make_ready(test_file)
    print("Metadata:", result['metadata'])
    print("Make ready data shape:", result['make_ready_data'].shape)
    print("Columns:", result['make_ready_data'].columns.tolist())
    if not result['make_ready_data'].empty:
        print(result['make_ready_data'].to_string())
