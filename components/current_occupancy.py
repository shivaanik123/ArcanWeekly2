"""
Current Occupancy section component
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

def render_current_occupancy(box_metrics: Dict[str, float], unit_counts: Dict[str, int], net_to_rent: int):
    """Render the Current Occupancy card with dark blue styling."""
    
    # Prepare data for the table
    occupied_units = box_metrics.get('occupied_units', 0)
    total_units = box_metrics.get('total_units', 0)
    occupancy_data = [
        {"Metric": "Occupied Units", "Value": f"{occupied_units}/{total_units}"},
        {"Metric": "Model/Down Units", "Value": box_metrics.get('model', 0) + box_metrics.get('down', 0)},
        {"Metric": "Vacant Rentable", "Value": unit_counts.get('vacant_rentable', 0)},
        {"Metric": "Leased Vacant", "Value": unit_counts.get('leased_vacant', 0)},
        {"Metric": "Notice Units", "Value": unit_counts.get('notice_units', 0)},
        {"Metric": "Under Eviction", "Value": unit_counts.get('under_eviction', 0)},
        {"Metric": "Pre-leased", "Value": unit_counts.get('pre_leased', 0)},
        {"Metric": "Net to Rent", "Value": net_to_rent}
    ]
    
    # Create the dark blue card container
    st.markdown("""
    <div class="dashboard-card">
        <div class="dashboard-card-header">
            <h3>Current Occupancy</h3>
        </div>
        <div class="dashboard-card-content">
    """, unsafe_allow_html=True)
    
    # Generate table without header
    table_rows = ""
    for item in occupancy_data:
        table_rows += f"""
        <div class="metric-row">
            <span class="metric-label">{item['Metric']}</span>
            <span class="metric-value">{item['Value']}</span>
        </div>
        """
    
    st.markdown(table_rows, unsafe_allow_html=True)
    
    # Close the card container
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)
