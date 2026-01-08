"""
Sidebar component for week and property selection
"""

import streamlit as st
from typing import Dict, List, Tuple, Optional

def render_sidebar(available_data: Dict[str, List[str]]) -> Tuple[Optional[str], Optional[str]]:
    """
    Render sidebar with week and property selection.

    Returns:
        Tuple of (selected_week, selected_property)
    """

    st.sidebar.title("ARCAN CAPITAL")
    st.sidebar.markdown("---")

    weeks = available_data.get('weeks', [])
    if not weeks:
        st.sidebar.info("📂 No data found in S3")
        return None, None

    selected_week = st.sidebar.selectbox(
        "Select Week",
        options=weeks,
        index=len(weeks) - 1 if weeks else 0
    )

    properties = available_data.get('properties', [])
    if not properties:
        st.sidebar.info("No properties found")
        return selected_week, None

    selected_property = st.sidebar.selectbox(
        "Select Property",
        options=properties,
        index=0
    )

    if selected_week and selected_property:
        st.sidebar.markdown("---")
        st.sidebar.success(f"**{selected_week}** - {selected_property}")

    return selected_week, selected_property


