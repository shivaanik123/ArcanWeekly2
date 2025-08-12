"""
Sidebar component for week and property selection
"""

import streamlit as st
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional

def render_sidebar(available_data: Dict[str, List[str]]) -> Tuple[Optional[str], Optional[str]]:
    """
    Render sidebar with week and property selection.
    
    Returns:
        Tuple of (selected_week, selected_property)
    """
    
    # Simple sidebar title (like the working test)
    st.sidebar.title("🏠 ARCAN CLEAN")
    st.sidebar.markdown("---")
    
    # Week selection - simplified
    weeks = available_data.get('weeks', [])
    if not weeks:
        st.sidebar.error("No data weeks found")
        return None, None
    
    selected_week = st.sidebar.selectbox(
        "📅 Select Week",
        options=weeks,
        index=len(weeks) - 1 if weeks else 0  # Default to latest week
    )
    
    # Property selection - simplified
    properties = available_data.get('properties', [])
    if not properties:
        st.sidebar.error("No properties found")
        return selected_week, None
    
    selected_property = st.sidebar.selectbox(
        "🏠 Select Property",
        options=properties,
        index=0
    )
    
    # Show current selection
    if selected_week and selected_property:
        st.sidebar.markdown("---")
        st.sidebar.success(f"**Selected:** {selected_week} - {selected_property}")
    
    return selected_week, selected_property

def show_data_availability(file_availability: Dict[str, bool]):
    """Show which data files are available in the sidebar."""
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Available Data:**")
    
    file_labels = {
        'resanalytics_box_score': '📊 Box Score',
        'work_order_report': '🔧 Work Orders',
        'resanalytics_unit_availability': '🏠 Unit Availability',
        'pending_make_ready': '🔨 Make Ready',
        'resaranalytics_delinquency': '💰 Delinquency'
    }
    
    for file_type, available in file_availability.items():
        label = file_labels.get(file_type, file_type)
        if available:
            st.sidebar.markdown(f"✅ {label}")
        else:
            st.sidebar.markdown(f"❌ {label}")
