"""
Parser for ResAnalytic Lease Expiration reports.

Pattern: ResAnalytic_Lease*
Example: ResAnalytic_Lease_Expiration_marbla.xlsx
"""

import pandas as pd
import re
from typing import Dict, Any


def parse_resanalytic_lease_expiration(file_path: str) -> Dict[str, Any]:
    """
    Parse ResAnalytic Lease Expiration Excel file.
    
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
    
    # Month/Year (row 2)
    date_match = re.search(r'Month Year = (.+)', str(df_raw.iloc[2, 0]))
    if date_match:
        metadata['month_year'] = date_match.group(1)
    
    # Find the header row
    header_row = None
    for i, row in df_raw.iterrows():
        if 'Property' in str(row.iloc[0]) and 'Address' in str(row.iloc[1]):
            header_row = i
            break
    
    lease_expiration_df = pd.DataFrame()
    
    if header_row is not None:
        # Extract headers
        headers = df_raw.iloc[header_row, :].fillna('').astype(str).tolist()
        headers = [h.strip() for h in headers if h.strip()]
        
        # Extract lease expiration data
        lease_data = []
        for i in range(header_row + 1, len(df_raw)):
            row_data = df_raw.iloc[i, :len(headers)].fillna('').astype(str).tolist()
            if any(cell.strip() for cell in row_data):  # Skip empty rows
                lease_data.append(row_data)
        
        if lease_data:
            lease_expiration_df = pd.DataFrame(lease_data, columns=headers)
            
            # Clean up numeric columns
            numeric_cols = ['Units', 'MTM']  # Month-to-Month
            for col in numeric_cols:
                if col in lease_expiration_df.columns:
                    lease_expiration_df[col] = lease_expiration_df[col].str.replace(',', '').replace('', '0')
                    lease_expiration_df[col] = pd.to_numeric(lease_expiration_df[col], errors='coerce')
        
        metadata['total_properties'] = len(lease_expiration_df) if not lease_expiration_df.empty else 0
        
        # Calculate summary statistics
        if not lease_expiration_df.empty and 'Units' in lease_expiration_df.columns:
            metadata['total_units'] = lease_expiration_df['Units'].sum()
            if 'MTM' in lease_expiration_df.columns:
                metadata['total_mtm'] = lease_expiration_df['MTM'].sum()
    
    return {
        'metadata': metadata,
        'lease_expiration_data': lease_expiration_df,
        'file_path': file_path,
        'parser_type': 'resanalytic_lease_expiration'
    }


def identify_resanalytic_lease_file(filename: str) -> bool:
    """
    Check if filename matches ResAnalytic Lease pattern.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        True if file matches pattern, False otherwise
    """
    base_name = re.sub(r'_[a-z]+\.xlsx$', '', filename.lower())
    return base_name.startswith('resanalytic_lease')


if __name__ == "__main__":
    # Test the parser
    test_file = "/Users/shivaanikomanduri/ArcanClean/data/08_04_2025/Marbella /ResAnalytic_Lease_Expiration_marbla.xlsx"
    result = parse_resanalytic_lease_expiration(test_file)
    print("Metadata:", result['metadata'])
    print("Lease expiration data shape:", result['lease_expiration_data'].shape)
    print("Columns:", result['lease_expiration_data'].columns.tolist())
    if not result['lease_expiration_data'].empty:
        print(result['lease_expiration_data'].to_string())
