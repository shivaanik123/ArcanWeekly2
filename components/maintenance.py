"""
Maintenance section component
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

def render_maintenance(work_orders_count: int, make_ready_count: int):
    """Render the Maintenance card with dark blue styling."""
    
    # Prepare data for the table
    maintenance_data = [
        {"Metric": "Work Orders", "Value": work_orders_count},
        {"Metric": "Make Ready", "Value": "None" if make_ready_count == 0 else make_ready_count}
    ]
    
    # Create the dark blue card container
    st.markdown("""
    <div class="dashboard-card">
        <div class="dashboard-card-header">
            <h3>Maintenance</h3>
        </div>
        <div class="dashboard-card-content">
    """, unsafe_allow_html=True)
    
    # Generate table without header
    table_rows = ""
    for item in maintenance_data:
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
