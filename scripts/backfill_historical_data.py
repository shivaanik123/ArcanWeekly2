#!/usr/bin/env python3
"""
Backfill script to extract historical data from weekly reports to Parquet files.

Two property types:
1. Internally Managed (INPUT sheet) - all data in one sheet
2. Externally Managed (Occupancy + Financial sheets) - data split across two sheets

Weekly reports aggregate history, so only the latest report is needed.
"""

import os
import sys
import glob

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
BUCKET_COPY_DIR = os.path.join(PROJECT_DIR, "bucket_copy")
INPUT_DIR = os.path.join(BUCKET_COPY_DIR, "data")
OUTPUT_DIR = os.path.join(BUCKET_COPY_DIR, "historicaldata")


def get_latest_week_dir() -> str:
    """Get the most recent week folder that has property subfolders."""
    weeks = [d for d in os.listdir(INPUT_DIR) if os.path.isdir(os.path.join(INPUT_DIR, d)) and '_' in d]
    if not weeks:
        return None

    def parse_date(w):
        parts = w.split('_')
        if len(parts) == 3:
            m, d, y = parts
            y = '20' + y if len(y) == 2 else y
            return f"{y}{m.zfill(2)}{d.zfill(2)}"
        return w

    # Sort by date descending, find first with property folders
    for week in sorted(weeks, key=parse_date, reverse=True):
        week_path = os.path.join(INPUT_DIR, week)
        subdirs = [d for d in os.listdir(week_path) if os.path.isdir(os.path.join(week_path, d))]
        if subdirs:
            return week_path
    return None


def extract_internally_managed(file_path: str) -> dict:
    """Extract from INPUT sheet (internally managed properties)."""
    result = {'occupancy': [], 'work_orders': [], 'collections': [], 'rent': [], 'financial': []}

    df = pd.read_excel(file_path, sheet_name='INPUT', header=None)

    # Detect column layout by finding Date columns in row 1
    # Format A: Rent at 42, Work Orders at 46
    # Format B: Rent at 41, Work Orders at 45
    # Format C: Rent at 40, Work Orders at 44
    date_cols = [i for i in range(35, min(50, df.shape[1]))
                 if pd.notna(df.iloc[1, i]) and str(df.iloc[1, i]).strip() == 'Date']

    if 42 in date_cols:
        rent_date_col, wo_date_col = 42, 46
    elif 41 in date_cols:
        rent_date_col, wo_date_col = 41, 45
    elif 40 in date_cols:
        rent_date_col, wo_date_col = 40, 44
    else:
        rent_date_col, wo_date_col = 41, 45  # fallback

    # Historical occupancy: cols 12-13 (Date, Occupancy %)
    for i in range(2, min(200, len(df))):
        try:
            date_val = df.iloc[i, 12]
            occ_val = df.iloc[i, 13]
            if pd.notna(date_val) and hasattr(date_val, 'year') and pd.notna(occ_val):
                occ = float(occ_val) * 100 if float(occ_val) <= 1 else float(occ_val)
                result['occupancy'].append({
                    'date': date_val.strftime('%Y-%m-%d'),
                    'occupancy_pct': occ,
                    'leased_pct': None,
                    'projected_pct': None
                })
        except:
            continue

    # Work orders: (Date, Work Orders, Make Readies)
    for i in range(2, min(200, len(df))):
        try:
            date_val = df.iloc[i, wo_date_col] if df.shape[1] > wo_date_col else None
            if pd.notna(date_val) and hasattr(date_val, 'year'):
                wo = int(df.iloc[i, wo_date_col + 1]) if pd.notna(df.iloc[i, wo_date_col + 1]) else 0
                mr = int(df.iloc[i, wo_date_col + 2]) if pd.notna(df.iloc[i, wo_date_col + 2]) else 0
                result['work_orders'].append({
                    'date': date_val.strftime('%Y-%m-%d'),
                    'work_orders': wo,
                    'make_readies': mr
                })
        except:
            continue

    # Collections: cols 29-32 (Date, Charges, Collected, %)
    for i in range(2, min(100, len(df))):
        try:
            date_val = df.iloc[i, 29] if df.shape[1] > 29 else None
            if pd.notna(date_val) and hasattr(date_val, 'year'):
                pct = float(df.iloc[i, 32]) if pd.notna(df.iloc[i, 32]) else 0
                pct = pct * 100 if pct <= 1 else pct
                result['collections'].append({
                    'date': date_val.strftime('%Y-%m-%d'),
                    'charges': float(df.iloc[i, 30]) if pd.notna(df.iloc[i, 30]) else 0,
                    'collected': float(df.iloc[i, 31]) if pd.notna(df.iloc[i, 31]) else 0,
                    'collections_pct': pct
                })
        except:
            continue

    # Rent: (Date, Market Rent, In-Place Rent)
    for i in range(2, min(100, len(df))):
        try:
            date_val = df.iloc[i, rent_date_col] if df.shape[1] > rent_date_col else None
            if pd.notna(date_val) and hasattr(date_val, 'year'):
                result['rent'].append({
                    'date': date_val.strftime('%Y-%m-%d'),
                    'market_rent': float(df.iloc[i, rent_date_col + 1]) if pd.notna(df.iloc[i, rent_date_col + 1]) else 0,
                    'occupied_rent': float(df.iloc[i, rent_date_col + 2]) if pd.notna(df.iloc[i, rent_date_col + 2]) else 0
                })
        except:
            continue

    # Financial (Revenue/Expenses): cols 18-23 (Date, Income Actual, Income Budget, NaN, Expense Actual, Expense Budget)
    for i in range(2, min(100, len(df))):
        try:
            date_val = df.iloc[i, 18] if df.shape[1] > 18 else None
            if pd.notna(date_val) and hasattr(date_val, 'year'):
                income_actual = df.iloc[i, 19] if pd.notna(df.iloc[i, 19]) else None
                expense_actual = df.iloc[i, 22] if pd.notna(df.iloc[i, 22]) else None
                if income_actual or expense_actual:
                    result['financial'].append({
                        'date': date_val.strftime('%Y-%m-%d'),
                        'revenue': float(income_actual) if income_actual else None,
                        'expenses': float(expense_actual) if expense_actual else None
                    })
        except:
            continue

    return result


def extract_externally_managed(file_path: str) -> dict:
    """Extract from Occupancy + Financial sheets (externally managed properties)."""
    result = {'occupancy': [], 'work_orders': [], 'collections': [], 'rent': [], 'financial': []}

    # Occupancy sheet: cols 13-18 (Date, Occupancy, Leased, Projection, Make Ready, Work Orders)
    df_occ = pd.read_excel(file_path, sheet_name='Occupancy', header=None)
    for i in range(20, len(df_occ)):
        try:
            date_val = df_occ.iloc[i, 13]
            if pd.isna(date_val) or not hasattr(date_val, 'year'):
                continue

            date_str = date_val.strftime('%Y-%m-%d')
            occ = df_occ.iloc[i, 14]
            leased = df_occ.iloc[i, 15]
            proj = df_occ.iloc[i, 16]
            mr = df_occ.iloc[i, 17]
            wo = df_occ.iloc[i, 18]

            # Convert decimals to percentages
            occ_pct = float(occ) * 100 if pd.notna(occ) and float(occ) <= 1 else (float(occ) if pd.notna(occ) else None)
            leased_pct = float(leased) * 100 if pd.notna(leased) and float(leased) <= 1 else (float(leased) if pd.notna(leased) else None)
            proj_pct = float(proj) * 100 if pd.notna(proj) and float(proj) <= 1 else (float(proj) if pd.notna(proj) else None)

            if occ_pct is not None:
                result['occupancy'].append({
                    'date': date_str,
                    'occupancy_pct': occ_pct,
                    'leased_pct': leased_pct,
                    'projected_pct': proj_pct
                })

            wo_count = int(wo) if pd.notna(wo) else 0
            mr_count = int(mr) if pd.notna(mr) else 0
            if wo_count > 0 or mr_count > 0:
                result['work_orders'].append({
                    'date': date_str,
                    'work_orders': wo_count,
                    'make_readies': mr_count
                })
        except:
            continue

    # Financial sheet: cols 12-21 (Date, Market Rent, Occupied Rent, Revenue, Expenses, Owed, Charges, Collections, Renewals, Move Outs)
    df_fin = pd.read_excel(file_path, sheet_name='Financial', header=None)
    for i in range(2, len(df_fin)):
        try:
            date_val = df_fin.iloc[i, 12]
            if pd.isna(date_val) or not hasattr(date_val, 'year'):
                continue

            date_str = date_val.strftime('%Y-%m-%d')
            market_rent = df_fin.iloc[i, 13]
            occupied_rent = df_fin.iloc[i, 14]
            revenue = df_fin.iloc[i, 15]
            expenses = df_fin.iloc[i, 16]
            charges = df_fin.iloc[i, 18]
            collections = df_fin.iloc[i, 19]

            # Rent data
            if pd.notna(market_rent) or pd.notna(occupied_rent):
                result['rent'].append({
                    'date': date_str,
                    'market_rent': float(market_rent) if pd.notna(market_rent) else None,
                    'occupied_rent': float(occupied_rent) if pd.notna(occupied_rent) else None
                })

            # Revenue/Expenses
            if pd.notna(revenue) or pd.notna(expenses):
                result['financial'].append({
                    'date': date_str,
                    'revenue': float(revenue) if pd.notna(revenue) else None,
                    'expenses': float(expenses) if pd.notna(expenses) else None
                })

            # Collections
            if pd.notna(charges) or pd.notna(collections):
                coll_pct = (float(collections) / float(charges) * 100) if pd.notna(charges) and pd.notna(collections) and float(charges) > 0 else None
                result['collections'].append({
                    'date': date_str,
                    'charges': float(charges) if pd.notna(charges) else None,
                    'collected': float(collections) if pd.notna(collections) else None,
                    'collections_pct': coll_pct
                })
        except:
            continue

    return result


def extract_property_data(prop_path: str, prop_name: str) -> dict:
    """Extract data from a property's weekly report."""
    weekly_reports = glob.glob(os.path.join(prop_path, "*Weekly Report*.xlsx"))
    if not weekly_reports:
        return None

    file_path = weekly_reports[0]
    xl = pd.ExcelFile(file_path)

    if 'INPUT' in xl.sheet_names:
        data = extract_internally_managed(file_path)
        data['type'] = 'internal'
    elif 'Occupancy' in xl.sheet_names and 'Financial' in xl.sheet_names:
        data = extract_externally_managed(file_path)
        data['type'] = 'external'
    else:
        print(f"  {prop_name}: Unknown format - sheets: {xl.sheet_names}")
        return None

    # Use folder name as property name (not filename) to match dashboard lookups
    data['property_name'] = prop_name

    return data


def write_parquet_files(property_data: dict, output_dir: str):
    """Write property data to Parquet files organized by year."""
    prop_name = property_data['property_name']
    prop_dir = os.path.join(output_dir, prop_name)

    # Collect all dates to determine years
    all_dates = set()
    for entry in property_data.get('occupancy', []):
        all_dates.add(entry['date'][:4])
    for entry in property_data.get('work_orders', []):
        all_dates.add(entry['date'][:4])
    for entry in property_data.get('collections', []):
        all_dates.add(entry['date'][:4])
    for entry in property_data.get('rent', []):
        all_dates.add(entry['date'][:4])
    for entry in property_data.get('financial', []):
        all_dates.add(entry['date'][:4])

    if not all_dates:
        print(f"  {prop_name}: No data found")
        return

    for year in sorted(all_dates):
        year_dir = os.path.join(prop_dir, year)
        os.makedirs(year_dir, exist_ok=True)

        # Filter by year
        year_occ = [e for e in property_data.get('occupancy', []) if e['date'].startswith(year)]
        year_wo = [e for e in property_data.get('work_orders', []) if e['date'].startswith(year)]
        year_coll = [e for e in property_data.get('collections', []) if e['date'].startswith(year)]
        year_rent = [e for e in property_data.get('rent', []) if e['date'].startswith(year)]
        year_fin = [e for e in property_data.get('financial', []) if e['date'].startswith(year)]

        # Write occupancy.parquet
        if year_occ:
            df = pd.DataFrame(year_occ)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').drop_duplicates(subset=['date'])
            df.to_parquet(os.path.join(year_dir, 'occupancy.parquet'), index=False)

        # Write maintenance.parquet
        if year_wo:
            df = pd.DataFrame(year_wo)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').drop_duplicates(subset=['date'])
            df.to_parquet(os.path.join(year_dir, 'maintenance.parquet'), index=False)

        # Write financial.parquet (merge collections, rent, revenue/expenses)
        fin_records = {}
        for e in year_coll:
            fin_records[e['date']] = {
                'date': e['date'],
                'charges': e.get('charges'),
                'collected': e.get('collected'),
                'collections_pct': e.get('collections_pct'),
                'market_rent': None,
                'occupied_rent': None,
                'revenue': None,
                'expenses': None
            }
        for e in year_rent:
            if e['date'] in fin_records:
                fin_records[e['date']]['market_rent'] = e.get('market_rent')
                fin_records[e['date']]['occupied_rent'] = e.get('occupied_rent')
            else:
                fin_records[e['date']] = {
                    'date': e['date'],
                    'charges': None, 'collected': None, 'collections_pct': None,
                    'market_rent': e.get('market_rent'),
                    'occupied_rent': e.get('occupied_rent'),
                    'revenue': None, 'expenses': None
                }
        for e in year_fin:
            if e['date'] in fin_records:
                fin_records[e['date']]['revenue'] = e.get('revenue')
                fin_records[e['date']]['expenses'] = e.get('expenses')
            else:
                fin_records[e['date']] = {
                    'date': e['date'],
                    'charges': None, 'collected': None, 'collections_pct': None,
                    'market_rent': None, 'occupied_rent': None,
                    'revenue': e.get('revenue'),
                    'expenses': e.get('expenses')
                }

        if fin_records:
            df = pd.DataFrame(sorted(fin_records.values(), key=lambda x: x['date']))
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').drop_duplicates(subset=['date'])
            df.to_parquet(os.path.join(year_dir, 'financial.parquet'), index=False)

    occ_count = len(property_data.get('occupancy', []))
    wo_count = len(property_data.get('work_orders', []))
    fin_count = len(property_data.get('financial', []))
    print(f"  {prop_name}: {len(all_dates)} years, {occ_count} occ, {wo_count} maint, {fin_count} fin")


def main():
    print("=" * 60)
    print("HISTORICAL DATA BACKFILL")
    print("=" * 60)

    latest_week = get_latest_week_dir()
    if not latest_week:
        print("ERROR: No week folders found")
        sys.exit(1)

    print(f"\nUsing latest week: {os.path.basename(latest_week)}")
    print(f"Output: {OUTPUT_DIR}\n")

    # Get all properties
    properties = [d for d in os.listdir(latest_week) if os.path.isdir(os.path.join(latest_week, d))]
    print(f"Found {len(properties)} properties\n")

    internal_count = 0
    external_count = 0

    print("=" * 60)
    print("EXTRACTING DATA")
    print("=" * 60 + "\n")

    for prop_name in sorted(properties):
        prop_path = os.path.join(latest_week, prop_name)
        data = extract_property_data(prop_path, prop_name)

        if data:
            if data.get('type') == 'internal':
                internal_count += 1
            else:
                external_count += 1
            write_parquet_files(data, OUTPUT_DIR)

    print("\n" + "=" * 60)
    print("BACKFILL COMPLETE")
    print("=" * 60)
    print(f"\nInternal (INPUT sheet): {internal_count}")
    print(f"External (Occupancy+Financial): {external_count}")
    print(f"Total: {internal_count + external_count}")


if __name__ == "__main__":
    main()
