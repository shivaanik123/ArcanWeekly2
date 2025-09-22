"""
Move Schedule section component
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta

def calculate_weekly_move_schedule(unit_availability_data: Dict[str, Any], total_units: int, current_occupied: int) -> List[Dict[str, Any]]:
    """
    Calculate weekly move schedule from Unit Availability Details data.
    
    Args:
        unit_availability_data: Raw unit availability data containing data_sections
        total_units: Total number of units in the property (e.g., 96 for Marbella)
        current_occupied: Currently occupied units from Box Score Summary
        
    Returns:
        List of weekly move schedule data
    """
    # Debug: Print what data we received
    print(f"DEBUG: unit_availability_data keys: {list(unit_availability_data.keys()) if unit_availability_data else 'None'}")
    
    if 'data_sections' in unit_availability_data:
        print(f"DEBUG: data_sections found! Keys: {list(unit_availability_data['data_sections'].keys())}")
        for section_name, df in unit_availability_data['data_sections'].items():
            if df is not None and not df.empty:
                print(f"DEBUG: Section '{section_name}' has columns: {list(df.columns)}")
                print(f"DEBUG: Section '{section_name}' has {len(df)} rows")
    else:
        print("DEBUG: No 'data_sections' found in unit_availability_data")
    # Get current date and find the Sunday of current week (week of ETL report)
    current_date = datetime.now()
    
    # If unit_availability_data has metadata with as_of_date, use that instead
    if 'metadata' in unit_availability_data and 'as_of_date' in unit_availability_data['metadata']:
        try:
            current_date = datetime.strptime(unit_availability_data['metadata']['as_of_date'], '%m/%d/%Y')
        except:
            # If parsing fails, use current date
            pass
    
    # Find the Sunday of the current week
    days_since_sunday = current_date.weekday() + 1  # Monday=0, so Sunday=6, adjust to Sunday=0
    if days_since_sunday == 7:  # If it's already Sunday
        days_since_sunday = 0
    
    current_sunday = current_date - timedelta(days=days_since_sunday)
    
    # Initialize weekly schedule (6 weeks forecast)
    schedule_data = []
    
    # Start with actual current occupied units from Box Score Summary
    # total_units is the maximum capacity (96 for Marbella)
    # current_occupied is the actual occupied units right now
    running_occupied = current_occupied
    print(f"DEBUG: Starting with {current_occupied} occupied units out of {total_units} total units")
    
    for week in range(6):
        week_start = current_sunday + timedelta(weeks=week)
        week_end = week_start + timedelta(days=6)  # 7 day period
        
        # Format week for display (MM/DD)
        week_label = week_start.strftime("%m/%d")
        
        # Count moves for this week
        move_ins = 0
        move_outs = 0
        
        # Debug: Track what we're processing
        debug_moves = []
        
        # Process unit availability data if available
        if 'data_sections' in unit_availability_data:
            for section_name, df in unit_availability_data['data_sections'].items():
                if df is not None and not df.empty:
                    # Count Move Ins
                    if 'Move In' in df.columns:
                        for _, row in df.iterrows():
                            if pd.notna(row['Move In']) and str(row['Move In']).strip() != '' and str(row['Move In']).strip().lower() != 'nan':
                                try:
                                    move_date = pd.to_datetime(row['Move In']).date()
                                    if week_start.date() <= move_date <= week_end.date():
                                        move_ins += 1
                                        debug_moves.append(f"Move In: {move_date} in week {week_label}")
                                except Exception as e:
                                    debug_moves.append(f"Failed to parse Move In: {row['Move In']} - {str(e)}")
                    
                    # Count Move Outs  
                    if 'Move Out' in df.columns:
                        for _, row in df.iterrows():
                            if pd.notna(row['Move Out']) and str(row['Move Out']).strip() != '' and str(row['Move Out']).strip().lower() != 'nan':
                                try:
                                    move_date = pd.to_datetime(row['Move Out']).date()
                                    if week_start.date() <= move_date <= week_end.date():
                                        move_outs += 1
                                        debug_moves.append(f"Move Out: {move_date} in week {week_label}")
                                except Exception as e:
                                    debug_moves.append(f"Failed to parse Move Out: {row['Move Out']} - {str(e)}")
        
        # Debug: Print what we found for this week (only if we found moves)
        if debug_moves:
            print(f"Week {week_label} ({week_start.date()} to {week_end.date()}): {debug_moves}")
        
        # Calculate net change and update occupied units
        net_change = move_ins - move_outs
        running_occupied += net_change
        
        # Cap occupied units at total property capacity
        if running_occupied > total_units:
            running_occupied = total_units
        elif running_occupied < 0:
            running_occupied = 0
        
        # Calculate occupancy percentage
        occupancy_percent = int((running_occupied / total_units) * 100) if total_units > 0 else 89
        
        schedule_data.append({
            "Week": week_label,
            "Move Ins": move_ins,
            "Move Outs": move_outs,
            "Units": running_occupied,  # This is occupied units, not total units
            "Occupancy": f"{occupancy_percent}%"
        })
    
    return schedule_data

def render_move_schedule(unit_availability_data: Dict[str, Any], total_units: int, current_occupied: int):
    """Render the Move Schedule card with dark blue styling."""
    
    # Calculate real move schedule from unit availability data
    schedule_data = calculate_weekly_move_schedule(unit_availability_data, total_units, current_occupied)
    
    # Create the card container matching other tables
    st.markdown("""
    <div class="dashboard-card">
        <div class="dashboard-card-header">
            <h3>Move Schedule</h3>
        </div>
        <div class="dashboard-card-content">
    """, unsafe_allow_html=True)
    
    # Generate table rows without header
    table_rows = ""
    
    # Convert schedule data to metric format like other tables
    metrics_data = []
    for item in schedule_data:
        metrics_data.append(f"{item['Week']}: {item['Move Ins']} in, {item['Move Outs']} out, {item['Units']} units ({item['Occupancy']})")
    
    for i, metric_text in enumerate(metrics_data):
        week = schedule_data[i]['Week']
        table_rows += f"""
        <div class="metric-row">
            <span class="metric-label">{week}</span>
            <span class="metric-value">{schedule_data[i]['Move Ins']}/{schedule_data[i]['Move Outs']}/{schedule_data[i]['Occupancy']}</span>
        </div>
        """
    
    st.markdown(table_rows, unsafe_allow_html=True)
    
    # Add footer
    st.markdown("""
        <div class="schedule-footer">
            *6-week forecast from historical data
        </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
