"""
Parser for Budget Comparison reports.

Pattern: Budget_Comparison*
Example: Budget_Comparison(with_PTD)_marbla_Accrual^AJEs^Modified Accrual.xlsx
"""

import re
from typing import Dict, Any

import pandas as pd


# Column index for MTD Actual values in raw data
MTD_ACTUAL_COL_IDX = 2


def _clean_currency_value(value) -> float:
    """Clean a currency value and convert to float."""
    if pd.isna(value):
        return 0.0
    val_str = str(value).replace(',', '').replace('$', '')
    val_str = val_str.replace('(', '-').replace(')', '')
    if not val_str.strip() or val_str.strip() == '0':
        return 0.0
    return float(val_str)


def _extract_collections_line_items(df_raw, header_row: int, metadata: Dict) -> None:
    """
    Extract specific line items for collections calculation from raw data.

    Structure: Column 0 = Account#, Column 1 = Description, Column 2 = MTD Actual
    """
    if header_row is None:
        return

    # Extract Total Income - look for row containing "TOTAL INCOME"
    metadata['total_income'] = 0.0
    for i in range(header_row + 1, len(df_raw)):
        row_str = str(df_raw.iloc[i].values).upper()
        if 'TOTAL INCOME' in row_str:
            try:
                mtd_val = df_raw.iloc[i, MTD_ACTUAL_COL_IDX]
                metadata['total_income'] = _clean_currency_value(mtd_val)
            except (ValueError, TypeError):
                pass
            break

    # Extract Bad Debt Rental Income - account 41799
    metadata['bad_debt_rental_income'] = 0.0
    for i in range(header_row + 1, len(df_raw)):
        row_str = str(df_raw.iloc[i].values)
        if '41799' in row_str:
            try:
                mtd_val = df_raw.iloc[i, MTD_ACTUAL_COL_IDX]
                metadata['bad_debt_rental_income'] = _clean_currency_value(mtd_val)
            except (ValueError, TypeError):
                pass
            break

    # Extract Write Off Rent - account 41800
    metadata['write_off_rent'] = 0.0
    for i in range(header_row + 1, len(df_raw)):
        row_str = str(df_raw.iloc[i].values)
        if '41800' in row_str:
            try:
                mtd_val = df_raw.iloc[i, MTD_ACTUAL_COL_IDX]
                metadata['write_off_rent'] = _clean_currency_value(mtd_val)
            except (ValueError, TypeError):
                pass
            break


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

        # Clean up headers and ensure unique names
        clean_headers = []
        seen_headers = {}
        for h in headers:
            if h and not h.startswith('Unnamed'):
                base_name = h
            else:
                base_name = f'Column_{len(clean_headers)}'

            # Make headers unique by adding suffix if duplicate
            if base_name in seen_headers:
                seen_headers[base_name] += 1
                unique_name = f'{base_name}_{seen_headers[base_name]}'
            else:
                seen_headers[base_name] = 0
                unique_name = base_name

            clean_headers.append(unique_name)

        # Extract budget data
        budget_data = []
        for i in range(header_row + 1, len(df_raw)):
            row_data = df_raw.iloc[i, :len(clean_headers)].fillna('').astype(str).tolist()
            if any(cell.strip() for cell in row_data):
                budget_data.append(row_data)

        if budget_data:
            budget_data_df = pd.DataFrame(budget_data, columns=clean_headers)

            # Clean up numeric columns
            for col in budget_data_df.columns:
                keywords = ['actual', 'budget', 'variance', 'ytd']
                if any(keyword in col.lower() for keyword in keywords):
                    try:
                        series = budget_data_df[col].astype(str)
                        series = series.str.replace(r'[,$()]', '', regex=True)
                        series = series.str.replace('-', '0')
                        budget_data_df[col] = pd.to_numeric(series, errors='coerce')
                    except (ValueError, TypeError):
                        pass

        metadata['budget_line_items'] = len(budget_data_df)

    # Extract collections-specific line items
    _extract_collections_line_items(df_raw, header_row, metadata)

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
    base_name = re.sub(r'_[a-z0-9]+\.xlsx$', '', filename.lower())
    base_name = re.sub(r'\([^)]*\)', '', base_name)
    base_name = re.sub(r'\^[^_]*', '', base_name)
    return base_name.strip().startswith('budget_comparison')


if __name__ == "__main__":
    TEST_FILE = (
        "/Users/shivaanikomanduri/ArcanClean/data/08_04_2025/Marbella /"
        "Budget_Comparison(with_PTD)_marbla_Accrual^AJEs^Modified Accrual.xlsx"
    )
    result = parse_budget_comparison(TEST_FILE)
    print("Metadata:", result['metadata'])
    print("Budget data shape:", result['budget_data'].shape)
    print("Columns:", result['budget_data'].columns.tolist())
    if not result['budget_data'].empty:
        print("Sample data:")
        print(result['budget_data'].head(3).to_string())
