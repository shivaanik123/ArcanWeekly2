"""
Sidebar component for week and property selection
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Tuple, Optional

def render_sidebar(available_data: Dict[str, List[str]]) -> Tuple[Optional[str], Optional[str]]:
    """
    Render sidebar with week and property selection.
    
    Returns:
        Tuple of (selected_week, selected_property)
    """
    
    # Display Arcan logo in sidebar
    st.sidebar.image("/Users/shivaanikomanduri/ArcanClean/streamlit_dashboard/logos/arcan-logo.png", use_container_width=True)
    st.sidebar.markdown("---")
    
    # Week selection
    weeks = available_data.get('weeks', [])
    if not weeks:
        st.sidebar.error("No data weeks found")
        return None, None
    
    # Convert week strings to readable format for display
    week_options = {}
    for week in weeks:
        try:
            week_date = datetime.strptime(week, '%m_%d_%Y')
            readable = week_date.strftime('%B %d, %Y')
            week_options[readable] = week
        except ValueError:
            week_options[week] = week
    
    selected_week_readable = st.sidebar.selectbox(
        "📅 Select Week",
        options=list(week_options.keys()),
        index=len(week_options) - 1 if week_options else 0  # Default to latest week
    )
    
    selected_week = week_options.get(selected_week_readable) if selected_week_readable else None
    
    # Property selection
    properties = available_data.get('properties', [])
    if not properties:
        st.sidebar.error("No properties found")
        return selected_week, None
    
    selected_property = st.sidebar.selectbox(
        "🏠 Select Property",
        options=properties,
        index=0
    )
    
    # Show data availability info
    if selected_week and selected_property:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Data Selection:**")
        st.sidebar.markdown(f"📅 Week: {selected_week_readable}")
        st.sidebar.markdown(f"🏠 Property: {selected_property}")
    
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
