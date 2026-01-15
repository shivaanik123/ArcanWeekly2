"""
Move Schedule section component - SIMPLIFIED VERSION

This component displays the 6-week forecast from the "Projected Occupancy" report.
No complex calculations - just read and display the data.

DATA SOURCE: Projected_Occupancy_{property}.xlsx
- The report contains pre-calculated move ins, move outs, and projected occupancy
- We simply extract and display this data
"""

import streamlit as st
from typing import Dict, Any, List


def get_move_schedule_from_projected_occupancy(projected_occupancy_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract 6-week forecast from Projected Occupancy report.

    This is SIMPLE - no calculations, just data extraction.
    The Projected Occupancy report already contains all calculated values.

    Args:
        projected_occupancy_data: Parsed data from Projected_Occupancy_{property}.xlsx
            Expected structure:
            {
                'forecast': [
                    {
                        'date': '01/11/2026',
                        'move_ins': 0.0,
                        'move_outs': 2.0,
                        'projected_occupancy': 106.0,
                        'projected_occupancy_percent': 86.18
                    },
                    ... (6 weeks total)
                ]
            }

    Returns:
        List of 6 weeks with format:
        [
            {
                "Week": "01/11",
                "Move Ins": 0,
                "Move Outs": 2,
                "Units": 106,
                "Occupancy": "86%"
            },
            ...
        ]
    """

    # Check if we have the forecast data
    if not projected_occupancy_data or 'forecast' not in projected_occupancy_data:
        return []

    forecast = projected_occupancy_data['forecast']

    # Convert to display format - straightforward mapping
    schedule_data = []

    for week in forecast:
        # Simple extraction - no calculations needed
        schedule_data.append({
            "Week": week['date'],  # Date from report (e.g., "01/11/2026")
            "Move Ins": int(week['move_ins']),  # Pre-calculated in report
            "Move Outs": int(week['move_outs']),  # Pre-calculated in report
            "Units": int(week['projected_occupancy']),  # Pre-calculated in report
            "Occupancy": f"{int(week['projected_occupancy_percent'])}%"  # Pre-calculated in report
        })

    return schedule_data

def render_move_schedule(projected_occupancy_data: Dict[str, Any]):
    """
    Render the Move Schedule card with 6-week forecast.

    SIMPLE FUNCTION - just displays pre-calculated data from Projected Occupancy report.

    Args:
        projected_occupancy_data: Parsed data from Projected_Occupancy_{property}.xlsx
    """

    # Create the card container
    st.markdown("""
    <div class="dashboard-card">
        <div class="dashboard-card-header">
            <h3>Move Schedule</h3>
        </div>
        <div class="dashboard-card-content">
    """, unsafe_allow_html=True)

    # Get the 6-week forecast data (simple extraction, no calculations)
    schedule_data = get_move_schedule_from_projected_occupancy(projected_occupancy_data)

    # If no data available, show error message
    if not schedule_data:
        st.markdown("""
        <div class="metric-row">
            <span class="metric-label" style="color: #ff6b6b;">⚠️ Projected Occupancy report not available</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Display the 6 weeks - straightforward table rows
        table_rows = ""

        for item in schedule_data:
            week = item['Week']
            move_ins = item['Move Ins']
            move_outs = item['Move Outs']
            occupancy = item['Occupancy']

            # Simple format: Week | Ins/Outs/Occupancy
            table_rows += f"""
            <div class="metric-row">
                <span class="metric-label">{week}</span>
                <span class="metric-value">{move_ins}/{move_outs}/{occupancy}</span>
            </div>
            """

        st.markdown(table_rows, unsafe_allow_html=True)

    # Footer
    st.markdown("""
        <div class="schedule-footer">
            *6-week forecast from Projected Occupancy report
        </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
