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
    
    # Arcan Capital title (logo removed for S3-only deployment)
    st.sidebar.title("🏠 ARCAN CAPITAL")
    st.sidebar.markdown("---")
    
    # Week selection - simplified
    weeks = available_data.get('weeks', [])
    if not weeks:
        st.sidebar.info("📂 No data weeks found - Upload files to get started!")
        # Show upload interface when no data
        st.sidebar.markdown("---")
        render_upload_interface()
        return None, None
    
    selected_week = st.sidebar.selectbox(
        "Select Week",
        options=weeks,
        index=len(weeks) - 1 if weeks else 0  # Default to latest week
    )
    
    # Property selection - simplified
    properties = available_data.get('properties', [])
    if not properties:
        st.sidebar.info("📂 No properties found - Upload files to get started!")
        # Show upload interface when no properties
        st.sidebar.markdown("---")
        render_upload_interface()
        return selected_week, None
    
    selected_property = st.sidebar.selectbox(
        "Select Property",
        options=properties,
        index=0
    )
    
    # Show current selection
    if selected_week and selected_property:
        st.sidebar.markdown("---")
        st.sidebar.success(f"**Selected:** {selected_week} - {selected_property}")
    
    # Enhanced bulk upload interface - always show at bottom
    st.sidebar.markdown("---")
    render_upload_interface()
    
    return selected_week, selected_property


