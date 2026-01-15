"""
Simple parser for Projected Occupancy Excel report.

FILE STRUCTURE:
- Row 1: Title "Projected Occupancy"
- Rows 2-6: Metadata (frequency, weeks, total units, current occupancy, week end date)
- Rows 7-8: Column headers
- Row 11: Property name
- Rows 12-17: 6 weeks of forecast data

COLUMNS:
- A: Date (week start date)
- C: Move Ins
- D: Move Outs
- E: Projected Occupancy (number of units)
- F: Projected Occupancy % (percentage)

This report contains pre-calculated 6-week forecasts. No complex logic needed.
"""

import pandas as pd
from typing import Dict, Any


def identify_projected_occupancy_file(filename: str) -> bool:
    """
    Identify if file is a Projected Occupancy report.

    Pattern: Projected_Occupancy_{property}.xlsx
    Example: Projected_Occupancy_55pharr.xlsx

    Args:
        filename: Name of the file to check

    Returns:
        True if matches pattern, False otherwise
    """
    filename_lower = filename.lower()
    return 'projected' in filename_lower and 'occupancy' in filename_lower


def parse_projected_occupancy(file_path: str) -> Dict[str, Any]:
    """
    Parse Projected Occupancy Excel report.

    This is a SIMPLE parser - it reads pre-calculated data from known cell positions.
    No complex calculations needed - the report already has everything.

    Args:
        file_path: Path to Excel file

    Returns:
        Dictionary with:
        - metadata: Report info (total_units, current_occupancy, as_of_date)
        - forecast: List of 6 weeks with move ins/outs and projected occupancy
    """

    # Read Excel file
    df = pd.read_excel(file_path, header=None)

    # STEP 1: Extract metadata from header rows
    # These are in fixed positions - simple and straightforward
    metadata = {
        'report_type': 'projected_occupancy',
        'frequency': str(df.iloc[1, 1]).replace('Frequency = ', '').strip() if pd.notna(df.iloc[1, 1]) else 'Weekly',
        'number_of_weeks': 6,  # Always 6 weeks
        'total_units': None,
        'current_occupancy': None,
        'as_of_date': None,
        'week_end_date': None,
        'property_name': None
    }

    # Extract total units (row 4)
    if pd.notna(df.iloc[3, 1]):
        total_units_text = str(df.iloc[3, 1])
        if 'Total units' in total_units_text:
            parts = total_units_text.split(':')
            if len(parts) > 1:
                metadata['total_units'] = int(parts[1].strip())

    # Extract current occupancy (row 5)
    if pd.notna(df.iloc[4, 1]):
        occupancy_text = str(df.iloc[4, 1])
        if 'Occupancy as of' in occupancy_text:
            parts = occupancy_text.split(':')
            if len(parts) > 1:
                metadata['current_occupancy'] = int(parts[1].strip())

    # Extract dates (row 6)
    if pd.notna(df.iloc[5, 1]):
        date_text = str(df.iloc[5, 1])
        if 'Week end date' in date_text:
            parts = date_text.split(':')
            if len(parts) > 1:
                metadata['week_end_date'] = parts[1].strip()
                metadata['as_of_date'] = parts[1].strip()  # Same as week end date

    # Extract property name (row 11)
    if pd.notna(df.iloc[10, 0]):
        metadata['property_name'] = str(df.iloc[10, 0]).strip()

    # STEP 2: Extract 6 weeks of forecast data
    # Data starts at row 12 (index 11), runs for 6 rows
    # Column mapping: A=Date, C=Move Ins, D=Move Outs, E=Projected Occupancy, F=Projected Occupancy %

    forecast = []

    for row_idx in range(11, 17):  # Rows 12-17 (indices 11-16)
        if row_idx >= len(df):
            break

        row_data = df.iloc[row_idx]

        # Simple column extraction - no complex logic
        week_data = {
            'date': str(row_data[0]) if pd.notna(row_data[0]) else '',  # Column A
            'move_ins': float(row_data[2]) if pd.notna(row_data[2]) else 0.0,  # Column C
            'move_outs': float(row_data[3]) if pd.notna(row_data[3]) else 0.0,  # Column D
            'projected_occupancy': float(row_data[4]) if pd.notna(row_data[4]) else 0.0,  # Column E
            'projected_occupancy_percent': float(row_data[5]) if pd.notna(row_data[5]) else 0.0  # Column F
        }

        forecast.append(week_data)

    # STEP 3: Return clean data structure
    return {
        'metadata': metadata,
        'forecast': forecast,
        'success': True
    }


if __name__ == "__main__":
    # Test the parser with sample file
    test_file = "/path/to/Projected_Occupancy_55pharr.xlsx"

    print("Testing Projected Occupancy Parser")
    print("=" * 50)

    result = parse_projected_occupancy(test_file)

    print("\nMetadata:")
    for key, value in result['metadata'].items():
        print(f"  {key}: {value}")

    print("\n6-Week Forecast:")
    for i, week in enumerate(result['forecast'], 1):
        print(f"\nWeek {i} ({week['date']}):")
        print(f"  Move Ins: {week['move_ins']}")
        print(f"  Move Outs: {week['move_outs']}")
        print(f"  Projected Occupancy: {week['projected_occupancy']} ({week['projected_occupancy_percent']}%)")
