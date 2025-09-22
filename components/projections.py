"""
Projections & Applications section component
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

def render_projections_applications(projection_percent: float, traffic_metrics: Dict[str, int]):
    """Render the Projections & Applications card with dark blue styling."""
    
    # Prepare data for the table
    projections_data = [
        {"Metric": "Total Traffic", "Value": traffic_metrics.get('total_traffic', 0)},
        {"Metric": "Total Applications", "Value": traffic_metrics.get('total_applications', 0)},
        {"Metric": "Approved", "Value": traffic_metrics.get('approved', 0)},
        {"Metric": "Cancelled", "Value": traffic_metrics.get('cancelled', 0)},
        {"Metric": "Denied", "Value": traffic_metrics.get('denied', 0)}
    ]
    
    # Create the dark blue card container
    st.markdown("""
    <div class="dashboard-card">
        <div class="dashboard-card-header">
            <h3>Applications</h3>
        </div>
        <div class="dashboard-card-content">
    """, unsafe_allow_html=True)
    
    # Generate table without header
    table_rows = ""
    for item in projections_data:
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
