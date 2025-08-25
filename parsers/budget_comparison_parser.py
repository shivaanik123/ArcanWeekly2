"""
Parser for Budget Comparison reports.

Pattern: Budget_Comparison*
Example: Budget_Comparison(with_PTD)_marbla_Accrual^AJEs^Modified Accrual.xlsx
"""

import pandas as pd
import re
from typing import Dict, Any


def parse_budget_comparison(file_path: str) -> Dict[str, Any]:
    """
    Parse Budget Comparison Excel file.
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        Dictionary containing parsed data with metadata and dataframes
    """
    
    # Read the Excel file without headers to analyze structure
    df_raw = pd.read_excel(file_path, sheet_name=0, header=None)
    
    # Extract metadata from header rows
    metadata = {}
    
    # Property name (row 0)
    property_match = re.search(r'(\w+)\s*\((\w+)\)', str(df_raw.iloc[0, 0]))
    if property_match:
        metadata['property_name'] = property_match.group(1)
        metadata['property_code'] = property_match.group(2)
    
    # Report type (row 1)
    if len(df_raw) > 1:
        metadata['report_type'] = str(df_raw.iloc[1, 0]).strip()
    
    # Period (row 2)
    period_match = re.search(r'Period = (.+)', str(df_raw.iloc[2, 0]))
    if period_match:
        metadata['period'] = period_match.group(1)
    
    # Book and Tree info (row 3)
    book_match = re.search(r'Book = (.+)', str(df_raw.iloc[3, 0]))
    if book_match:
        book_info = book_match.group(1)
        if ';' in book_info:
            parts = book_info.split(';')
            metadata['books'] = [b.strip() for b in parts[0].split(',')]
            tree_part = parts[1].strip() if len(parts) > 1 else ''
            tree_match = re.search(r'Tree = (.+)', tree_part)
            if tree_match:
                metadata['tree'] = tree_match.group(1)
    
    # Find the header row (contains MTD Actual, MTD Budget, etc.)
    header_row = None
    for i, row in df_raw.iterrows():
        if 'MTD Actual' in str(row.iloc[2]) or 'MTD Budget' in str(row.iloc[3]):
            header_row = i
            break
    
    budget_data_df = pd.DataFrame()
    
    if header_row is not None:
        # Extract headers
        headers = df_raw.iloc[header_row, :].fillna('').astype(str).tolist()
        headers = [h.strip() for h in headers if h.strip()]
        
        # Clean up headers
        clean_headers = []
        for h in headers:
            if h and not h.startswith('Unnamed'):
                clean_headers.append(h)
            else:
                clean_headers.append(f'Column_{len(clean_headers)}')
        
        # Extract budget data
        budget_data = []
        for i in range(header_row + 1, len(df_raw)):
            row_data = df_raw.iloc[i, :len(clean_headers)].fillna('').astype(str).tolist()
            if any(cell.strip() for cell in row_data):  # Skip empty rows
                budget_data.append(row_data)
        
        if budget_data:
            budget_data_df = pd.DataFrame(budget_data, columns=clean_headers)
            
            # Clean up numeric columns (anything that looks like an amount)
            for col in budget_data_df.columns:
                if any(keyword in col.lower() for keyword in ['actual', 'budget', 'variance', 'ytd']):
                    try:
                        # Convert to string first, then clean
                        series = budget_data_df[col].astype(str)
                        series = series.str.replace(r'[,$()]', '', regex=True)
                        series = series.str.replace('-', '0')  # Handle empty values
                        budget_data_df[col] = pd.to_numeric(series, errors='coerce')
                    except Exception:
                        # If conversion fails, leave as is
                        pass
        
        metadata['budget_line_items'] = len(budget_data_df) if not budget_data_df.empty else 0
    
    return {
        'metadata': metadata,
        'budget_data': budget_data_df,
        'file_path': file_path,
        'parser_type': 'budget_comparison'
    }


def identify_budget_comparison_file(filename: str) -> bool:
    """
    Check if filename matches Budget Comparison pattern.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        True if file matches pattern, False otherwise
    """
    base_name = re.sub(r'_[a-z]+\.xlsx$', '', filename.lower())
    # Handle special characters in budget comparison files
    base_name = re.sub(r'\([^)]*\)', '', base_name)  # Remove parentheses content
    base_name = re.sub(r'\^[^_]*', '', base_name)    # Remove ^ content
    return base_name.strip().startswith('budget_comparison')


if __name__ == "__main__":
    # Test the parser
    test_file = "/Users/jsai23/Workspace/Arcan/data/08_04_2025/Marbella /Budget_Comparison(with_PTD)_marbla_Accrual^AJEs^Modified Accrual.xlsx"
    result = parse_budget_comparison(test_file)
    print("Metadata:", result['metadata'])
    print("Budget data shape:", result['budget_data'].shape)
    print("Columns:", result['budget_data'].columns.tolist())
    if not result['budget_data'].empty:
        print("Sample data:")
        print(result['budget_data'].head(3).to_string())
