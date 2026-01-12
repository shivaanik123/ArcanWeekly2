"""
Simple business calculations for dashboard metrics
"""

import pandas as pd
from typing import Dict, Any
from datetime import datetime, timedelta

def get_box_score_metrics(data: Dict[str, Any]) -> Dict[str, float]:
    """Get metrics from Box Score Summary data."""
    metrics = {
        'total_units': 0, 'occupied_units': 0, 'vacant_rented': 0, 'vacant_unrented': 0,
        'notice_rented': 0, 'notice_unrented': 0, 'model': 0, 'down': 0,
        'percent_occupied': 0.0, 'percent_leased': 0.0
    }
    
    if 'data_sections' not in data or 'availability' not in data['data_sections']:
        return metrics
    
    df = data['data_sections']['availability']
    total_row = df[df['Name'].str.contains('Total', case=False, na=False)]
    
    if total_row.empty:
        return metrics
    
    row = total_row.iloc[0]
    metrics['total_units'] = int(row.get('Units', 0))
    metrics['vacant_rented'] = int(row.get('Vacant Rented', 0))
    metrics['vacant_unrented'] = int(row.get('Vacant Unrented', 0))
    metrics['notice_rented'] = int(row.get('Notice Rented', 0))
    metrics['notice_unrented'] = int(row.get('Notice Unrented', 0))
    metrics['model'] = int(row.get('Model', 0))
    metrics['down'] = int(row.get('Down', 0))
    metrics['percent_occupied'] = float(row.get('% Occ', 0))
    metrics['percent_leased'] = float(row.get('% Leased', 0))
    
    # Calculate occupied units
    vacant_total = metrics['vacant_rented'] + metrics['vacant_unrented']
    metrics['occupied_units'] = metrics['total_units'] - vacant_total
    
    return metrics

def get_move_schedule(data: Dict[str, Any], week_start: datetime) -> Dict[str, Any]:
    """Get move-in/move-out schedule for the week."""
    week_end = week_start + timedelta(days=6)
    metrics = {'move_ins_this_week': 0, 'move_outs_this_week': 0, 'weekly_schedule': []}
    
    if 'data_sections' not in data:
        return metrics
    
    # Collect all units
    all_units = []
    for section_name, df in data['data_sections'].items():
        for _, row in df.iterrows():
            all_units.append(row)
    
    # Count moves this week
    for unit in all_units:
        # Move ins
        if 'Move In' in unit and pd.notna(unit['Move In']):
            try:
                move_date = pd.to_datetime(unit['Move In']).date()
                if week_start.date() <= move_date <= week_end.date():
                    metrics['move_ins_this_week'] += 1
            except:
                pass
        
        # Move outs
        if 'Move Out' in unit and pd.notna(unit['Move Out']):
            try:
                move_date = pd.to_datetime(unit['Move Out']).date()
                if week_start.date() <= move_date <= week_end.date():
                    metrics['move_outs_this_week'] += 1
            except:
                pass
    
    # Generate daily schedule
    for i in range(7):
        current_date = week_start + timedelta(days=i)
        date_str = current_date.strftime('%m/%d')
        
        day_move_ins = 0
        day_move_outs = 0
        
        for unit in all_units:
            # Check move ins for this day
            if 'Move In' in unit and pd.notna(unit['Move In']):
                try:
                    move_date = pd.to_datetime(unit['Move In']).date()
                    if move_date == current_date.date():
                        day_move_ins += 1
                except:
                    pass
            
            # Check move outs for this day
            if 'Move Out' in unit and pd.notna(unit['Move Out']):
                try:
                    move_date = pd.to_datetime(unit['Move Out']).date()
                    if move_date == current_date.date():
                        day_move_outs += 1
                except:
                    pass
        
        # Calculate units occupied for this day
        base_occupied = metrics.get('base_occupied', 0)
        cumulative_moves = sum([day['move_ins'] - day['move_outs'] for day in metrics['weekly_schedule']])
        units_occupied = base_occupied + cumulative_moves + day_move_ins - day_move_outs
        
        metrics['weekly_schedule'].append({
            'week': date_str,
            'move_ins': day_move_ins,
            'move_outs': day_move_outs,
            'units': units_occupied,
            'occupancy': 0  # Will calculate later with total units
        })
    
    return metrics

def get_unit_counts(data: Dict[str, Any]) -> Dict[str, int]:
    """Get unit status counts from Unit Availability data."""
    counts = {
        'notice_units': 0, 'under_eviction': 0, 'pre_leased': 0,
        'vacant_rentable': 0, 'leased_vacant': 0
    }
    
    if 'data_sections' not in data:
        return counts
    
    for section_name, df in data['data_sections'].items():
        section_lower = section_name.lower()
        
        if 'notice' in section_lower:
            # Count evictions
            if 'Status' in df.columns:
                evictions = df[df['Status'].str.contains('eviction', case=False, na=False)]
                counts['under_eviction'] += len(evictions)
                counts['notice_units'] += len(df) - len(evictions)
            else:
                counts['notice_units'] += len(df)
        
        elif 'vacant rented' in section_lower:
            counts['leased_vacant'] += len(df)
            counts['pre_leased'] += len(df)
        
        elif 'vacant unrented' in section_lower:
            counts['vacant_rentable'] += len(df)
    
    return counts

def calculate_projection(box_metrics: Dict[str, float], move_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate projection percentage and status."""
    total_units = box_metrics.get('total_units', 0)
    current_occupied = box_metrics.get('occupied_units', 0)
    move_ins = move_metrics.get('move_ins_this_week', 0)
    move_outs = move_metrics.get('move_outs_this_week', 0)
    
    if total_units == 0:
        return {'projection_percent': 0.0, 'status': 'UNKNOWN'}
    
    # Projection formula: MIN(((Current Occupancy * Total Units) + move ins - move outs) / Total Units, 1)
    projected_occupied = current_occupied + move_ins - move_outs
    projection_percent = min(projected_occupied / total_units, 1.0) * 100
    
    # Determine status
    if projection_percent < 90:
        status = 'ALERT'
    elif projection_percent > 95:
        status = 'GOOD'
    else:
        status = 'WATCH'
    
    return {
        'projection_percent': projection_percent,
        'status': status,
        'projected_occupied': projected_occupied
    }

def calculate_net_to_rent(box_metrics: Dict[str, float], unit_counts: Dict[str, int]) -> int:
    """Calculate Net to Rent: Vacant Rentable - Leased Vacant + Notice units - Pre Leased"""
    return max(0, 
        unit_counts.get('vacant_rentable', 0) - 
        unit_counts.get('leased_vacant', 0) + 
        unit_counts.get('notice_units', 0) - 
        unit_counts.get('pre_leased', 0)
    )

def extract_budget_line_item(budget_data: Dict[str, Any], line_item_name: str) -> float:
    """
    Extract a specific line item value from Budget Comparison data.

    Args:
        budget_data: Parsed Budget Comparison data
        line_item_name: Name of the line item to search for (e.g., 'Total Income', 'Bad Debt')

    Returns:
        The MTD Actual or YTD Actual value for the line item, or 0.0 if not found
    """
    if 'budget_data' not in budget_data or budget_data['budget_data'].empty:
        return 0.0

    df = budget_data['budget_data']

    # Search for the line item by name (case-insensitive, partial match)
    for _, row in df.iterrows():
        # Check both Column_0 and Column_1 for the line item name
        col_0 = str(row.get('Column_0', '')).strip().lower()
        col_1 = str(row.get('Column_1', '')).strip().lower()
        search_term = line_item_name.lower()

        if search_term in col_0 or search_term in col_1:
            # Try to extract MTD Actual or YTD Actual
            mtd_actual = row.get('MTD Actual', 0)
            ytd_actual = row.get('YTD Actual', 0)

            # Return MTD Actual if available, otherwise YTD Actual
            try:
                value = float(mtd_actual) if pd.notna(mtd_actual) and mtd_actual != '' else float(ytd_actual) if pd.notna(ytd_actual) else 0.0
                return value
            except (ValueError, TypeError):
                continue

    return 0.0


def calculate_collections_rate(delinquency_data: Dict[str, Any], box_metrics: Dict[str, float],
                               budget_comparison_data: Dict[str, Any] = None) -> float:
    """
    Calculate collections rate using the correct formula:

    Step 1: Charges = Total Income - Bad Debt Rental Income - Write Off Rent
            (from Budget Comparison report)

    Step 2: Collected = Charges - 0-30 Day Delinquency
            (from Delinquency report)

    Step 3: % Collected = Collected / Charges

    Args:
        delinquency_data: Parsed delinquency report data
        box_metrics: Box score metrics (for legacy compatibility)
        budget_comparison_data: Parsed Budget Comparison report data

    Returns:
        Collections rate as a percentage (0-100)
    """

    # NEW FORMULA: Using Budget Comparison data
    if budget_comparison_data and 'budget_data' in budget_comparison_data:
        # Step 1: Extract financial data from Budget Comparison
        total_income = extract_budget_line_item(budget_comparison_data, 'total income')
        bad_debt = extract_budget_line_item(budget_comparison_data, 'bad debt')
        write_off = extract_budget_line_item(budget_comparison_data, 'write off')

        # Calculate Charges (note: write-offs are often negative, so we ADD them)
        charges = total_income - bad_debt - write_off

        # Step 2: Extract 0-30 Day Delinquency from delinquency report
        delinquency_0_30 = 0.0
        if 'delinquency_data' in delinquency_data and not delinquency_data['delinquency_data'].empty:
            df = delinquency_data['delinquency_data']

            # Look for 0-30 day delinquency column (various possible names)
            possible_columns = ['0-30 Owed', '0-30', '0-30 Days', '0-30 Day', 'Current']

            for col_name in possible_columns:
                if col_name in df.columns:
                    # Sum all rows for this column
                    for _, row in df.iterrows():
                        try:
                            value = float(row.get(col_name, 0))
                            delinquency_0_30 += value
                        except (ValueError, TypeError):
                            continue
                    break

        # Step 3: Calculate collections rate
        if charges > 0:
            collected = charges - delinquency_0_30
            collections_rate = (collected / charges) * 100
            return max(0, min(100, collections_rate))  # Cap between 0-100%

    # FALLBACK: Old formula (if Budget Comparison data not available)
    if 'delinquency_data' not in delinquency_data or delinquency_data['delinquency_data'].empty:
        return 0.0

    df = delinquency_data['delinquency_data']

    # Get total charges and total owed
    total_charges = 0
    total_owed = 0

    for _, row in df.iterrows():
        if 'Total Charges' in df.columns:
            total_charges += float(row.get('Total Charges', 0))
        if 'Total Owed' in df.columns:
            total_owed += float(row.get('Total Owed', 0))

    if total_charges > 0:
        collections_rate = ((total_charges - total_owed) / total_charges) * 100
        return max(0, min(100, collections_rate))  # Cap between 0-100%

    return 0.0

def get_residents_on_notice_metrics(residents_data: Dict[str, Any]) -> Dict[str, int]:
    """Extract metrics from Residents on Notice data."""
    metrics = {
        'total_residents_on_notice': 0,
        'notice_units': 0,  # Will be calculated elsewhere using Box Score formula
        'under_eviction': 0,
        'pre_leased': 0  # Notice Rented = Pre Leased
    }
    
    if 'residents_data' not in residents_data:
        return metrics
    
    df = residents_data['residents_data']
    if df.empty:
        return metrics
    
    # Get eviction count from metadata (more reliable)
    if 'metadata' in residents_data:
        metadata = residents_data['metadata']
        metrics['under_eviction'] = metadata.get('eviction_count', 0)
        # Note: notice_units will be calculated using Box Score formula, not from this data
        metrics['total_residents_on_notice'] = metadata.get('total_residents', 0)
    
    # Pre-leased is Notice Rented from Box Score, not from this report
    # This will be set elsewhere
    
    return metrics

def calculate_notice_units(box_metrics: Dict[str, float], eviction_count: int) -> int:
    """
    Calculate Notice Units using Box Score data and eviction count.
    Formula: Notice Rented + Notice Unrented - Evictions
    """
    notice_rented = box_metrics.get('notice_rented', 0)
    notice_unrented = box_metrics.get('notice_unrented', 0)
    
    notice_units = notice_rented + notice_unrented - eviction_count
    return max(0, notice_units)  # Ensure non-negative result

def get_traffic_metrics(box_data: Dict[str, Any]) -> Dict[str, int]:
    """Extract traffic metrics from box score conversion ratios data."""
    traffic_metrics = {
        'total_traffic': 0,
        'total_applications': 0,
        'approved': 0,
        'cancelled': 0,
        'denied': 0
    }
    
    if 'data_sections' in box_data and 'conversion_ratios' in box_data['data_sections']:
        conv_df = box_data['data_sections']['conversion_ratios']
        
        # Find total row
        total_rows = conv_df[conv_df.iloc[:, 1].str.contains('total', case=False, na=False)]
        
        if not total_rows.empty:
            total_row = total_rows.iloc[0]
            
            # Extract traffic data from total row
            try:
                # Sum up all traffic sources
                calls = int(total_row.get('Calls', 0) or 0)
                walk_in = int(total_row.get('Walk-in', 0) or 0) 
                email = int(total_row.get('Email', 0) or 0)
                web = int(total_row.get('Web', 0) or 0)
                sms = int(total_row.get('SMS', 0) or 0)
                chat = int(total_row.get('Chat', 0) or 0)
                other = int(total_row.get('Other', 0) or 0)
                
                traffic_metrics['total_traffic'] = calls + walk_in + email + web + sms + chat + other
                
                # Get application metrics
                traffic_metrics['total_applications'] = int(total_row.get('Applied', 0) or 0)
                traffic_metrics['approved'] = int(total_row.get('Approved', 0) or 0)
                traffic_metrics['denied'] = int(total_row.get('Denied', 0) or 0)
                traffic_metrics['cancelled'] = int(total_row.get('Cancels', 0) or 0)
                
            except (ValueError, TypeError):
                # Fall back to defaults if conversion fails
                pass
    
    return traffic_metrics