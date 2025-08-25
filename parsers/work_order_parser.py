"""
Parser for Work Order Report files.

Pattern: Work_Order*
Example: Work_Order_Report_marbla.xlsx
"""

import pandas as pd
import re
from typing import Dict, Any, Optional


def parse_work_order_report(file_path: str) -> Dict[str, Any]:
    """
    Parse Work Order Report Excel file.
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        Dictionary containing parsed data with metadata and dataframes
    """
    
    # Read the Excel file without headers to analyze structure
    df_raw = pd.read_excel(file_path, sheet_name=0, header=None)
    
    # Extract metadata from header rows
    metadata = {}
    
    # Extract property and filter criteria from first rows
    for i in range(min(3, len(df_raw))):
        cell_value = str(df_raw.iloc[i, 0])
        if 'Property=' in cell_value:
            # Extract property code
            property_match = re.search(r'Property=(\w+)', cell_value)
            if property_match:
                metadata['property_code'] = property_match.group(1)
            
            # Extract status filters
            status_match = re.search(r"Status='([^']+)'", cell_value)
            if status_match:
                metadata['status_filters'] = [s.strip() for s in status_match.group(1).split("','")]
    
    # Find the header row (contains columns like WO#, Brief Desc, etc.)
    header_row = None
    for i, row in df_raw.iterrows():
        if 'WO#' in str(row.iloc[0]) or 'Brief Desc' in str(row.iloc[1]):
            header_row = i
            break
    
    if header_row is not None:
        # Extract headers
        headers = df_raw.iloc[header_row, :].fillna('').astype(str).tolist()
        headers = [h.strip() for h in headers if h.strip()]
        
        # Extract work order data
        work_orders = []
        for i in range(header_row + 1, len(df_raw)):
            row_data = df_raw.iloc[i, :len(headers)].fillna('').astype(str).tolist()
            if any(cell.strip() for cell in row_data):  # Skip empty rows
                work_orders.append(row_data)
        
        if work_orders:
            work_order_df = pd.DataFrame(work_orders, columns=headers)
            
            # Clean up data types
            if 'WO#' in work_order_df.columns:
                work_order_df['WO#'] = pd.to_numeric(work_order_df['WO#'], errors='coerce')
            
            # Clean phone numbers if present
            if 'Caller Phone' in work_order_df.columns:
                work_order_df['Caller Phone'] = work_order_df['Caller Phone'].str.replace(r'[^\d]', '', regex=True)
            
            metadata['work_order_count'] = len(work_order_df)
    else:
        work_order_df = pd.DataFrame()
        metadata['work_order_count'] = 0
    
    return {
        'metadata': metadata,
        'work_orders': work_order_df,
        'file_path': file_path,
        'parser_type': 'work_order_report'
    }


def identify_work_order_file(filename: str) -> bool:
    """
    Check if filename matches Work Order pattern.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        True if file matches pattern, False otherwise
    """
    # Remove property identifier and extension for pattern matching
    base_name = re.sub(r'_[a-z0-9]+\.xlsx$', '', filename.lower())
    return base_name.startswith('work_order')


if __name__ == "__main__":
    # Test the parser
    test_file = "/Users/shivaanikomanduri/ArcanClean/data/08_04_2025/Marbella /Work_Order_Report_marbla.xlsx"
    result = parse_work_order_report(test_file)
    print("Metadata:", result['metadata'])
    print("Work orders shape:", result['work_orders'].shape)
    print("Work orders columns:", result['work_orders'].columns.tolist())
    if not result['work_orders'].empty:
        print("Sample work order:")
        print(result['work_orders'].head(1).to_string())
