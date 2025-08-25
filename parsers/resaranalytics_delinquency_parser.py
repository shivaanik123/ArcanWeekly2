"""
Parser for ResARAnalytics Delinquency Summary reports.

Pattern: ResARAnalytics_Delinquency*
Example: ResARAnalytics_Delinquency_Summary_marbla.xlsx
"""

import pandas as pd
import re
from typing import Dict, Any


def parse_resaranalytics_delinquency(file_path: str) -> Dict[str, Any]:
    """
    Parse ResARAnalytics Delinquency Summary Excel file.
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        Dictionary containing parsed data with metadata and dataframes
    """
    
    # Read the Excel file without headers to analyze structure
    df_raw = pd.read_excel(file_path, sheet_name=0, header=None)
    
    # Extract metadata from header rows
    metadata = {}
    
    # Report title (row 0)
    metadata['report_title'] = str(df_raw.iloc[0, 0]).strip()
    
    # Extract date and selection info from row 1
    if len(df_raw) > 1:
        header_info = str(df_raw.iloc[1, 0])
        date_match = re.search(r'As Of: (\d{1,2}/\d{1,2}/\d{4})', header_info)
        if date_match:
            metadata['as_of_date'] = date_match.group(1)
        
        if 'All Selected Accounts' in header_info:
            metadata['account_scope'] = 'All Selected Accounts'
    
    # Find the header rows (multi-row headers)
    header_start = None
    for i, row in df_raw.iterrows():
        if 'Property' in str(row.iloc[0]) and 'Total' in str(row.iloc[1]):
            header_start = i
            break
    
    delinquency_df = pd.DataFrame()
    
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
        
        # Extract delinquency data
        delinq_data = []
        for i in range(header_start + 2, len(df_raw)):
            row_data = df_raw.iloc[i, :len(headers)].fillna('').astype(str).tolist()
            first_cell = row_data[0].strip() if row_data else ''
            
            # Skip metadata rows at the bottom
            if 'UserId' in first_cell or 'Date :' in first_cell or 'Time :' in first_cell:
                break
                
            if any(cell.strip() for cell in row_data):  # Skip empty rows
                delinq_data.append(row_data)
        
        if delinq_data:
            delinquency_df = pd.DataFrame(delinq_data, columns=headers)
            
            # Clean up numeric columns (all financial amounts)
            for col in delinquency_df.columns:
                if any(keyword in col.lower() for keyword in ['total', 'charges', 'owed', 'future']):
                    delinquency_df[col] = delinquency_df[col].str.replace(r'[,$]', '', regex=True)
                    delinquency_df[col] = pd.to_numeric(delinquency_df[col], errors='coerce')
        
        metadata['property_count'] = len(delinquency_df) if not delinquency_df.empty else 0
        
        # Calculate summary from data
        if not delinquency_df.empty:
            total_charges_col = next((col for col in delinquency_df.columns if 'total' in col.lower() and 'charges' in col.lower()), None)
            if total_charges_col:
                metadata['total_charges'] = delinquency_df[total_charges_col].sum()
    
    # Extract footer metadata (UserId, Date, Time)
    for i in range(len(df_raw) - 3, len(df_raw)):
        if i >= 0:
            cell_value = str(df_raw.iloc[i, 0])
            if 'UserId' in cell_value:
                user_match = re.search(r'UserId : (\w+)', cell_value)
                date_match = re.search(r'Date : (\d{1,2}/\d{1,2}/\d{4})', cell_value)
                time_match = re.search(r'Time : (.+)', cell_value)
                
                if user_match:
                    metadata['user_id'] = user_match.group(1)
                if date_match:
                    metadata['report_date'] = date_match.group(1)
                if time_match:
                    metadata['report_time'] = time_match.group(1)
    
    return {
        'metadata': metadata,
        'delinquency_data': delinquency_df,
        'file_path': file_path,
        'parser_type': 'resaranalytics_delinquency'
    }


def identify_resaranalytics_delinquency_file(filename: str) -> bool:
    """
    Check if filename matches ResARAnalytics Delinquency pattern.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        True if file matches pattern, False otherwise
    """
    base_name = re.sub(r'_[a-z]+\.xlsx$', '', filename.lower())
    return base_name.startswith('resaranalytics_delinquency')


if __name__ == "__main__":
    # Test the parser
    test_file = "/Users/jsai23/Workspace/Arcan/data/08_04_2025/Marbella /ResARAnalytics_Delinquency_Summary_marbla.xlsx"
    result = parse_resaranalytics_delinquency(test_file)
    print("Metadata:", result['metadata'])
    print("Delinquency data shape:", result['delinquency_data'].shape)
    print("Columns:", result['delinquency_data'].columns.tolist())
    if not result['delinquency_data'].empty:
        print(result['delinquency_data'].to_string())
