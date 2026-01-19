"""
Parser for ResARAnalytics Delinquency Summary reports.

Pattern: ResARAnalytics_Delinquency*
Example: ResARAnalytics_Delinquency_Summary_marbla.xlsx
"""

import re
from typing import Dict, Any, Optional

import pandas as pd


def _extract_delinquency_buckets(
    delinquency_df: pd.DataFrame,
    metadata: Dict[str, Any]
) -> None:
    """
    Extract 0-30 Owed and 31-60 Owed from Grand Total row.

    Args:
        delinquency_df: Parsed delinquency dataframe
        metadata: Metadata dict to update with extracted values
    """
    if delinquency_df.empty:
        metadata['owed_0_30'] = 0.0
        metadata['owed_31_60'] = 0.0
        return

    first_col = delinquency_df.columns[0]

    # Find the Grand Total or Total row
    grand_total_row = delinquency_df[
        delinquency_df[first_col].astype(str).str.lower().str.contains(
            'grand total|total', na=False
        )
    ]

    # If no explicit total row found, use the last row
    if grand_total_row.empty and len(delinquency_df) > 0:
        grand_total_row = delinquency_df.iloc[[-1]]

    if grand_total_row.empty:
        metadata['owed_0_30'] = 0.0
        metadata['owed_31_60'] = 0.0
        return

    # Find 0-30 Owed column
    owed_0_30_col = next(
        (col for col in delinquency_df.columns
         if '0-30' in col and 'owed' in col.lower()),
        None
    )
    if owed_0_30_col:
        try:
            metadata['owed_0_30'] = float(grand_total_row[owed_0_30_col].iloc[0])
        except (ValueError, TypeError):
            metadata['owed_0_30'] = 0.0
    else:
        metadata['owed_0_30'] = 0.0

    # Find 31-60 Owed column
    owed_31_60_col = next(
        (col for col in delinquency_df.columns
         if '31-60' in col and 'owed' in col.lower()),
        None
    )
    if owed_31_60_col:
        try:
            metadata['owed_31_60'] = float(grand_total_row[owed_31_60_col].iloc[0])
        except (ValueError, TypeError):
            metadata['owed_31_60'] = 0.0
    else:
        metadata['owed_31_60'] = 0.0


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
    # Look for row with 'Property' in first column and 'Total' or '0-30' in row
    header_start: Optional[int] = None
    for i, row in df_raw.iterrows():
        row_str = str(row.values)
        if 'Property' in str(row.iloc[0]) and ('Total' in row_str or '0-30' in row_str):
            header_start = i
            break

    delinquency_df = pd.DataFrame()

    if header_start is not None:
        # Extract multi-row headers
        header_row1 = df_raw.iloc[header_start, :].fillna('').astype(str).tolist()
        header_row2 = df_raw.iloc[header_start + 1, :].fillna('').astype(str).tolist()

        # Combine headers intelligently
        headers = []
        for h1, h2 in zip(header_row1, header_row2):
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
            if 'UserId' in first_cell or 'Date :' in first_cell:
                break

            if any(cell.strip() for cell in row_data):
                delinq_data.append(row_data)

        if delinq_data:
            delinquency_df = pd.DataFrame(delinq_data, columns=headers)

            # Clean up numeric columns
            for col in delinquency_df.columns:
                keywords = ['total', 'charges', 'owed', 'future']
                if any(keyword in col.lower() for keyword in keywords):
                    delinquency_df[col] = delinquency_df[col].str.replace(
                        r'[,$]', '', regex=True
                    )
                    delinquency_df[col] = pd.to_numeric(
                        delinquency_df[col], errors='coerce'
                    )

        metadata['property_count'] = len(delinquency_df)

        # Calculate summary from data
        if not delinquency_df.empty:
            total_charges_col = next(
                (col for col in delinquency_df.columns
                 if 'total' in col.lower() and 'charges' in col.lower()),
                None
            )
            if total_charges_col:
                metadata['total_charges'] = delinquency_df[total_charges_col].sum()

            # Extract delinquency bucket values for collections calculation
            _extract_delinquency_buckets(delinquency_df, metadata)

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
    base_name = re.sub(r'_[a-z0-9]+\.xlsx$', '', filename.lower())
    return base_name.startswith('resaranalytics_delinquency')


if __name__ == "__main__":
    TEST_FILE = (
        "/Users/shivaanikomanduri/ArcanClean/data/08_04_2025/Marbella /"
        "ResARAnalytics_Delinquency_Summary_marbla.xlsx"
    )
    result = parse_resaranalytics_delinquency(TEST_FILE)
    print("Metadata:", result['metadata'])
    print("Delinquency data shape:", result['delinquency_data'].shape)
    print("Columns:", result['delinquency_data'].columns.tolist())
    if not result['delinquency_data'].empty:
        print(result['delinquency_data'].to_string())
