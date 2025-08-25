"""
Sidebar component for week and property selection
"""

import streamlit as st
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from utils.upload_handler import render_upload_interface

def render_sidebar(available_data: Dict[str, List[str]]) -> Tuple[Optional[str], Optional[str]]:
    """
    Render sidebar with week and property selection.
    
    Returns:
        Tuple of (selected_week, selected_property)
    """
    
    # Arcan Capital logo in sidebar
    logo_path = "/Users/shivaanikomanduri/ArcanClean/streamlit_dashboard/logos/arcan-logo.png"
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, use_container_width=True)
    else:
        st.sidebar.title("🏠 ARCAN CAPITAL")
    st.sidebar.markdown("---")
    
    # Week selection - simplified
    weeks = available_data.get('weeks', [])
    if not weeks:
        st.sidebar.error("No data weeks found")
        return None, None
    
    selected_week = st.sidebar.selectbox(
        "Select Week",
        options=weeks,
        index=len(weeks) - 1 if weeks else 0  # Default to latest week
    )
    
    # Property selection - simplified
    properties = available_data.get('properties', [])
    if not properties:
        st.sidebar.error("No properties found")
        return selected_week, None
    
    selected_property = st.sidebar.selectbox(
        "Select Property",
        options=properties,
        index=0
    )
    
    # Enhanced bulk upload interface
    st.sidebar.markdown("---")
    render_upload_interface()
    
    # Show current selection
    if selected_week and selected_property:
        st.sidebar.markdown("---")
        st.sidebar.success(f"**Selected:** {selected_week} - {selected_property}")
    
    return selected_week, selected_property


