"""
Parser for Residents on Notice reports.

Pattern: Residents_on_Notice*
Example: Residents_on_Notice_marbla.xlsx
"""

import pandas as pd
import re
from typing import Dict, Any
from datetime import datetime

def parse_residents_on_notice(file_path: str) -> Dict[str, Any]:
    """
    Parse Residents on Notice Excel file.
    
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
        header_info = str(df_raw.iloc[1, 0])
        property_match = re.search(r'Property=(\w+)', header_info)
        if property_match:
            metadata['property_code'] = property_match.group(1)
        
        date_match = re.search(r'As of Date=(\d{2}/\d{2}/\d{4})', header_info)
        if date_match:
            metadata['as_of_date'] = date_match.group(1)
    
    # Find the header row (contains Property, Unit, Resident, etc.)
    header_row = None
    for i, row in df_raw.iterrows():
        row_data = df_raw.iloc[i, :].fillna('').astype(str).tolist()
        if ('Property' in row_data and 'Unit' in row_data and 
            'Resident' in row_data and 'Notice Date' in row_data):
            header_row = i
            break
    
    residents_df = pd.DataFrame()
    
    if header_row is not None:
        # Extract headers
        headers = df_raw.iloc[header_row, :].fillna('').astype(str).tolist()
        headers = [h.strip() for h in headers if h.strip()]
        
        # Extract resident data
        resident_data = []
        for i in range(header_row + 1, len(df_raw)):
            row_data = df_raw.iloc[i, :len(headers)].fillna('').astype(str).tolist()
            if any(cell.strip() for cell in row_data):  # Skip empty rows
                resident_data.append(row_data)
        
        if resident_data:
            residents_df = pd.DataFrame(resident_data, columns=headers)
            
            # Clean up date columns
            date_columns = ['Notice Date', 'Moveout Date']
            for col in date_columns:
                if col in residents_df.columns:
                    try:
                        residents_df[col] = pd.to_datetime(residents_df[col], errors='coerce')
                    except:
                        pass  # Keep as string if conversion fails
    
    # Calculate summary statistics
    summary_stats = {}
    if not residents_df.empty:
        summary_stats['total_residents'] = len(residents_df)
        
        # Count by status
        if 'Status' in residents_df.columns:
            status_counts = residents_df['Status'].value_counts().to_dict()
            summary_stats['status_breakdown'] = status_counts
            summary_stats['notice_count'] = status_counts.get('Notice', 0)
            summary_stats['eviction_count'] = status_counts.get('Eviction', 0)
        
        # Analyze notice dates (time on notice)
        if 'Notice Date' in residents_df.columns:
            try:
                # Calculate days since notice for active notices
                today = datetime.now()
                notice_dates = pd.to_datetime(residents_df['Notice Date'], errors='coerce')
                days_on_notice = (today - notice_dates).dt.days
                
                summary_stats['avg_days_on_notice'] = int(days_on_notice.mean()) if not days_on_notice.isna().all() else 0
                summary_stats['max_days_on_notice'] = int(days_on_notice.max()) if not days_on_notice.isna().all() else 0
            except:
                summary_stats['avg_days_on_notice'] = 0
                summary_stats['max_days_on_notice'] = 0
        
        # Analyze moveout dates (upcoming moveouts)
        if 'Moveout Date' in residents_df.columns:
            try:
                moveout_dates = pd.to_datetime(residents_df['Moveout Date'], errors='coerce')
                today = datetime.now()
                
                # Count moveouts in next 30 days
                next_30_days = today + pd.Timedelta(days=30)
                upcoming_moveouts = moveout_dates[(moveout_dates >= today) & (moveout_dates <= next_30_days)]
                summary_stats['moveouts_next_30_days'] = len(upcoming_moveouts)
                
                # Count overdue moveouts (past moveout date but still on notice)
                overdue_moveouts = moveout_dates[moveout_dates < today]
                summary_stats['overdue_moveouts'] = len(overdue_moveouts)
            except:
                summary_stats['moveouts_next_30_days'] = 0
                summary_stats['overdue_moveouts'] = 0
    
    metadata.update(summary_stats)
    
    return {
        'metadata': metadata,
        'residents_data': residents_df,
        'file_path': file_path,
        'parser_type': 'residents_on_notice'
    }


def identify_residents_on_notice_file(filename: str) -> bool:
    """
    Check if filename matches Residents on Notice pattern.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        True if file matches pattern, False otherwise
    """
    base_name = re.sub(r'_[a-z]+\.xlsx$', '', filename.lower())
    return base_name.startswith('residents_on_notice') or 'residents' in base_name and 'notice' in base_name


if __name__ == "__main__":
    # Test the parser
    test_file = "/Users/shivaanikomanduri/ArcanClean/data/08_04_2025/Marbella /Residents_on_Notice_marbla.xlsx"
    
    try:
        result = parse_residents_on_notice(test_file)
        print("📊 RESIDENTS ON NOTICE PARSER RESULTS:")
        print("=" * 50)
        print("Metadata:", result['metadata'])
        print()
        print("Residents data shape:", result['residents_data'].shape)
        print("Columns:", result['residents_data'].columns.tolist())
        
        if not result['residents_data'].empty:
            print()
            print("Sample data:")
            print(result['residents_data'].head().to_string(index=False))
            
            print()
            print("📈 KEY INSIGHTS:")
            print(f"• Total residents on notice: {result['metadata'].get('total_residents', 0)}")
            print(f"• Notice status: {result['metadata'].get('notice_count', 0)}")
            print(f"• Eviction status: {result['metadata'].get('eviction_count', 0)}")
            print(f"• Avg days on notice: {result['metadata'].get('avg_days_on_notice', 0)}")
            print(f"• Upcoming moveouts (30 days): {result['metadata'].get('moveouts_next_30_days', 0)}")
            print(f"• Overdue moveouts: {result['metadata'].get('overdue_moveouts', 0)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
