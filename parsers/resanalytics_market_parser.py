"""
Parser for ResAnalytics Market Rent Schedule reports.

Pattern: ResAnalytics_Market*
Example: ResAnalytics_Market_Rent_Schedule_marbla.xlsx
"""

import pandas as pd
import re
from typing import Dict, Any


def parse_resanalytics_market_rent(file_path: str) -> Dict[str, Any]:
    """
    Parse ResAnalytics Market Rent Schedule Excel file.
    
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
    date_match = re.search(r'As Of = (.+)', str(df_raw.iloc[2, 0]))
    if date_match:
        metadata['as_of_date'] = date_match.group(1)
    
    # Find the header rows (multi-row headers)
    header_start = None
    for i, row in df_raw.iterrows():
        if 'Property' in str(row.iloc[0]) and 'Name' in str(row.iloc[1]):
            header_start = i
            break
    
    market_rent_df = pd.DataFrame()
    
    if header_start is not None:
        # Extract multi-row headers
        header_rows = []
        for j in range(3):  # Check up to 3 rows for headers
            if header_start + j < len(df_raw):
                header_rows.append(df_raw.iloc[header_start + j, :].fillna('').astype(str).tolist())
        
        # Combine headers intelligently
        headers = []
        max_cols = max(len(row) for row in header_rows) if header_rows else 0
        
        for i in range(max_cols):
            header_parts = []
            for row in header_rows:
                if i < len(row) and row[i].strip():
                    header_parts.append(row[i].strip())
            
            if header_parts:
                # Join unique parts
                unique_parts = []
                for part in header_parts:
                    if part not in unique_parts:
                        unique_parts.append(part)
                headers.append(' '.join(unique_parts))
            else:
                headers.append(f'Column_{i}')
        
        # Remove empty trailing columns
        while headers and headers[-1].startswith('Column_'):
            headers.pop()
        
        # Extract market rent data
        data_start = header_start + len(header_rows)
        market_data = []
        
        for i in range(data_start, len(df_raw)):
            row_data = df_raw.iloc[i, :len(headers)].fillna('').astype(str).tolist()
            if any(cell.strip() for cell in row_data):  # Skip empty rows
                market_data.append(row_data)
        
        if market_data:
            market_rent_df = pd.DataFrame(market_data, columns=headers)
            
            # Clean up numeric columns
            for col in market_rent_df.columns:
                if 'units' in col.lower() or 'rent' in col.lower() or 'average' in col.lower():
                    market_rent_df[col] = market_rent_df[col].str.replace(',', '').replace('', '0')
                    market_rent_df[col] = pd.to_numeric(market_rent_df[col], errors='coerce')
        
        metadata['total_properties'] = len(market_rent_df) if not market_rent_df.empty else 0
    
    return {
        'metadata': metadata,
        'market_rent_data': market_rent_df,
        'file_path': file_path,
        'parser_type': 'resanalytics_market_rent'
    }


def identify_resanalytics_market_file(filename: str) -> bool:
    """
    Check if filename matches ResAnalytics Market pattern.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        True if file matches pattern, False otherwise
    """
    base_name = re.sub(r'_[a-z]+\.xlsx$', '', filename.lower())
    return base_name.startswith('resanalytics_market')


if __name__ == "__main__":
    # Test the parser
    test_file = "/Users/jsai23/Workspace/Arcan/data/08_04_2025/Marbella /ResAnalytics_Market_Rent_Schedule_marbla.xlsx"
    result = parse_resanalytics_market_rent(test_file)
    print("Metadata:", result['metadata'])
    print("Market rent data shape:", result['market_rent_data'].shape)
    print("Columns:", result['market_rent_data'].columns.tolist())
    if not result['market_rent_data'].empty:
        print(result['market_rent_data'].to_string())
