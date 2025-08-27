"""
Main Streamlit Dashboard Application
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# Import components and utilities
from data.loader import get_available_weeks_and_properties, load_property_data
from utils.calculations import (
    get_box_score_metrics, get_move_schedule, get_unit_counts,
    calculate_projection, calculate_net_to_rent, calculate_collections_rate,
    get_traffic_metrics, get_residents_on_notice_metrics, calculate_notice_units
)
from components.sidebar import render_sidebar
from components.kpi_cards import render_kpi_cards
from components.current_occupancy import render_current_occupancy
from components.projections import render_projections_applications
from components.maintenance import render_maintenance
from components.move_schedule import render_move_schedule
from components.graphs import render_graphs_section
from config.property_config import get_property_logo_path, get_property_display_name, find_property_by_directory_name

# Page config - Force sidebar to be visible
st.set_page_config(
    page_title="Real Estate Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main dashboard application."""
    
    # Clean Trading Dashboard CSS
    st.markdown("""
    <style>
    /* Global Dark Theme */
    .stApp {
        background: #0a0e1a !important;
        color: #ffffff;
    }
    
    .main {
        background: #0a0e1a !important;
        color: #ffffff;
    }
    
    /* Headers */
    .main h1, .main h2, .main h3, .main h4 {
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    
    .main h3 {
        color: #3b82f6 !important;
        font-size: 1.4rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        border-bottom: 2px solid #3b82f6 !important;
        padding-bottom: 8px !important;
        margin-bottom: 20px !important;
    }
    
    /* Tables */
    .table {
        width: 100%;
        border-collapse: collapse;
        background: #1e293b !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    
    .table th {
        background: #0f172a !important;
        color: #3b82f6 !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        padding: 12px !important;
        border-bottom: 2px solid #3b82f6 !important;
    }
    
    .table td {
        background: #1e293b !important;
        color: #ffffff !important;
        padding: 10px 12px !important;
        border-bottom: 1px solid #475569 !important;
    }
    
    .table-striped tbody tr:nth-of-type(odd) td {
        background: #334155 !important;
    }
    
    /* Robust sidebar selector for current Streamlit builds */
    section[data-testid="stSidebar"], aside[data-testid="stSidebar"] {
        background: #1e293b !important;
        border-right: 1px solid #4a90e2 !important;
    }
    
    /* Ensure text doesn't wrap weirdly in sidebar when expanded */
    .stSidebar .stSelectbox label,
    .stSidebar .stMarkdown,
    .stSidebar h1,
    .stSidebar h2,
    .stSidebar h3 {
        white-space: normal;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    
    /* Main content spacing */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Keep header so the sidebar toggle is visible */
    header[data-testid="stHeader"] {
        background: transparent;
        box-shadow: none;
        height: 3rem;        /* slim it down instead of hiding */
    }
    
    /* Dashboard Cards - Content outlined, headers plain */
    .dashboard-card {
        background: transparent;
        border: none;
        padding: 0;
        margin: 8px 0;
    }
    
    .dashboard-card-header h3 {
        color: #ffffff !important;
        font-size: 1.1rem !important;
        margin: 0 0 8px 0 !important;
        padding: 0 !important;
        border: none !important;
        text-transform: none !important;
        letter-spacing: normal !important;
        background: transparent !important;
    }
    
    .dashboard-card-content {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(74, 144, 226, 0.3) !important;
        border-radius: 12px !important;
        padding: 0 !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
        color: #ffffff !important;
        overflow: hidden !important;
    }
    
    .metric-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 20px;
        border-bottom: 1px solid rgba(74, 144, 226, 0.15);
        transition: background-color 0.2s ease;
        min-height: 48px;
    }
    
    .metric-row:first-child {
        background: rgba(74, 144, 226, 0.1);
        border-bottom: 2px solid rgba(74, 144, 226, 0.3);
        font-weight: 600;
    }
    
    .metric-row:last-child {
        border-bottom: none;
    }
    
    .metric-row:hover:not(:first-child) {
        background: rgba(74, 144, 226, 0.08);
    }
    
    .metric-label {
        color: #e2e8f0;
        font-size: 0.9rem;
        font-weight: 500;
        flex: 1;
    }
    
    .metric-row:first-child .metric-label {
        color: #ffffff;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        color: #ffffff;
        font-size: 0.9rem;
        font-weight: 600;
        text-align: right;
        min-width: 60px;
    }
    
    .metric-row:first-child .metric-value {
        color: #ffffff;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 0.5px;
    }
    
    /* Schedule Table Styling - Matching other tables */
    .schedule-table {
        width: 100%;
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(74, 144, 226, 0.3) !important;
        border-radius: 12px !important;
        padding: 0 !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
        color: #ffffff !important;
        overflow: hidden !important;
    }
    
    .schedule-header {
        display: flex;
        background: rgba(74, 144, 226, 0.1);
        padding: 12px 20px;
        border-bottom: 2px solid rgba(74, 144, 226, 0.3);
        font-weight: 600;
        min-height: 48px;
        align-items: center;
    }
    
    .schedule-row {
        display: flex;
        padding: 12px 20px;
        border-bottom: 1px solid rgba(74, 144, 226, 0.15);
        transition: background-color 0.2s ease;
        min-height: 48px;
        align-items: center;
    }
    
    .schedule-row:last-child {
        border-bottom: none;
    }
    
    .schedule-row:hover {
        background: rgba(74, 144, 226, 0.08);
    }
    
    /* Schedule table - simplified grid layout */
    .schedule-header-row,
    .schedule-data-row {
        display: grid !important;
        grid-template-columns: 1fr 1fr 1fr 1fr 1fr;
        gap: 8px;
        align-items: center;
        padding: 12px 16px !important;
        min-height: 48px;
        width: 100%;
        box-sizing: border-box;
    }
    
    .schedule-header-row {
        background: rgba(74, 144, 226, 0.1) !important;
        border-bottom: 2px solid rgba(74, 144, 226, 0.3) !important;
        font-weight: 600;
    }
    
    .schedule-data-row {
        border-bottom: 1px solid rgba(74, 144, 226, 0.15) !important;
        transition: background-color 0.2s ease;
    }
    
    .schedule-data-row:hover {
        background: rgba(74, 144, 226, 0.08) !important;
    }
    
    .schedule-data-row:last-child {
        border-bottom: none !important;
    }
    
    .schedule-col {
        text-align: center;
        color: #ffffff;
        font-size: 0.8rem;
        font-weight: 500;
        padding: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        min-width: 0;
    }
    
    .schedule-header-row .schedule-col {
        color: #ffffff !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 0.5px;
    }
    
    /* Simple Schedule Table */
    .simple-schedule-table {
        width: 100%;
        display: table;
        border-collapse: collapse;
    }
    
    .simple-row {
        display: table-row;
    }
    
    .simple-cell {
        display: table-cell;
        padding: 12px 8px;
        text-align: center;
        color: #ffffff;
        font-size: 0.85rem;
        font-weight: 500;
        border-bottom: 1px solid rgba(74, 144, 226, 0.15);
        vertical-align: middle;
        width: 20%;
    }
    
    .simple-header {
        background: rgba(74, 144, 226, 0.1) !important;
    }
    
    .simple-header .simple-cell {
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 0.5px;
        border-bottom: 2px solid rgba(74, 144, 226, 0.3);
        color: #ffffff;
    }
    
    .simple-row:hover .simple-cell {
        background: rgba(74, 144, 226, 0.08);
    }
    
    .simple-row:last-child .simple-cell {
        border-bottom: none;
    }
    
    /* Scrollable Schedule Container */
    .scrollable-schedule-container {
        overflow-x: auto;
        max-width: 100%;
    }
    
    .scrollable-schedule-container .metric-row {
        display: flex;
        min-width: 500px; /* Minimum width to ensure all columns are visible */
        align-items: center;
        padding: 12px 20px;
        border-bottom: 1px solid rgba(74, 144, 226, 0.15);
        transition: background-color 0.2s ease;
        min-height: 48px;
    }
    
    .scrollable-schedule-container .metric-row:first-child {
        background: rgba(74, 144, 226, 0.1) !important;
        border-bottom: 2px solid rgba(74, 144, 226, 0.3) !important;
        font-weight: 600;
    }
    
    .scrollable-schedule-container .metric-row:hover:not(:first-child) {
        background: rgba(74, 144, 226, 0.08) !important;
    }
    
    .scrollable-schedule-container .metric-row:last-child {
        border-bottom: none !important;
    }
    
    .scrollable-schedule-container .metric-label,
    .scrollable-schedule-container .metric-value {
        flex: 1;
        text-align: center;
        min-width: 80px;
        padding: 0 8px;
        white-space: nowrap;
    }
    
    .scrollable-schedule-container .metric-row:first-child .metric-label {
        color: #ffffff !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        font-size: 0.8rem !important;
        letter-spacing: 0.5px !important;
    }
    
    .schedule-footer {
        margin: 8px 20px 12px 20px;
        color: #9ca3af;
        font-size: 0.75rem;
        font-style: italic;
        text-align: center;
        padding-bottom: 8px;
    }
    
    /* Legend styling */
    .schedule-legend {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin: 12px 20px 8px 20px;
        padding: 8px 0;
        border-top: 1px solid rgba(74, 144, 226, 0.1);
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        gap: 4px;
        color: #e2e8f0;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .legend-symbol {
        color: #74b9ff;
        font-weight: 600;
        font-size: 1rem;
    }
    
    .legend-text {
        color: #e2e8f0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Handle upload notifications
    if st.session_state.get('upload_complete', False):
        uploaded_properties = st.session_state.get('last_upload_properties', [])
        if uploaded_properties:
            st.success(f"✅ Data updated for: {', '.join(uploaded_properties)}")
        # Clear the notification
        st.session_state.upload_complete = False
    
    # Load available weeks and properties (S3 only)
    available_data = get_available_weeks_and_properties()
    
    # Use the proper render_sidebar function
    selected_week, selected_property = render_sidebar(available_data)
    
    

    
    # Main content area - show property logo or default title
    if selected_property:
        # Map directory name to property key
        property_key = find_property_by_directory_name(selected_property)
        # Use property name as title (logos removed for S3-only deployment)
        display_name = get_property_display_name(property_key)
        st.title(f"{display_name} Dashboard")
    else:
        st.title("Real Estate Property Dashboard")
    
    if not selected_week or not selected_property:
        st.error("Please select a week and property from the sidebar")
        return
    
    # Load data for selected week/property
    with st.spinner("Loading data..."):
        # Force cache clear if this property was recently uploaded to
        if (st.session_state.get('last_upload_properties', []) and 
            selected_property in st.session_state.get('last_upload_properties', [])):
            st.cache_data.clear()
        
        print(f"🔍 DEBUG: selected_week = '{selected_week}', selected_property = '{selected_property}'")
        data = load_property_data(selected_week, selected_property)
    
    # If weekly data is missing, continue with empty data (graphs will still work with comprehensive reports)
    if 'error' in data:
        st.warning(f"Weekly data not available: {data['error']}")
        st.info("📊 Showing historical analytics from comprehensive reports only")
        data = {'raw_data': {}}  # Empty data, but continue to show graphs
    

    
    # Check data availability
    raw_data = data.get('raw_data', {})
    file_availability = {
        'resanalytics_box_score': 'resanalytics_box_score' in raw_data,
        'work_order_report': 'work_order_report' in raw_data,
        'resanalytics_unit_availability': 'resanalytics_unit_availability' in raw_data,
        'pending_make_ready': 'pending_make_ready' in raw_data,
        'resaranalytics_delinquency': 'resaranalytics_delinquency' in raw_data,
        'residents_on_notice': 'residents_on_notice' in raw_data
    }
    

    
    # Calculate metrics
    box_metrics = {}
    unit_counts = {}
    residents_metrics = {}
    move_metrics = {}
    projection_data = {}
    
    # Get week start date for move calculations
    try:
        week_start = datetime.strptime(selected_week, '%m_%d_%Y')
    except ValueError:
        week_start = datetime.now()
    
    # Process Box Score data
    if file_availability['resanalytics_box_score']:
        box_metrics = get_box_score_metrics(raw_data['resanalytics_box_score'])
    
    # Process Residents on Notice data (NEW - for accurate eviction data)
    eviction_count = 0
    if file_availability['residents_on_notice']:
        residents_metrics = get_residents_on_notice_metrics(raw_data['residents_on_notice'])
        eviction_count = residents_metrics.get('under_eviction', 0)
        # Only set eviction count, notice_units will be calculated from Box Score
        unit_counts.update({
            'under_eviction': eviction_count
        })
    
    # Add Box Score metrics to unit_counts for consistent data
    if box_metrics:
        # Calculate Notice Units using new formula: Notice Rented + Notice Unrented - Evictions
        calculated_notice_units = calculate_notice_units(box_metrics, eviction_count)
        
        unit_counts.update({
            'vacant_rentable': box_metrics.get('vacant_unrented', 0),
            'leased_vacant': box_metrics.get('vacant_rented', 0),
            'pre_leased': box_metrics.get('notice_rented', 0),
            'notice_units': calculated_notice_units  # NEW FORMULA
        })
    
    # Process Unit Availability data
    if file_availability['resanalytics_unit_availability']:
        unit_availability_counts = get_unit_counts(raw_data['resanalytics_unit_availability'])
        # Don't override eviction data if we have residents data
        if not file_availability['residents_on_notice']:
            unit_counts.update(unit_availability_counts)
        move_metrics = get_move_schedule(raw_data['resanalytics_unit_availability'], week_start)
        
        # Set base occupied for move schedule
        move_metrics['base_occupied'] = box_metrics.get('occupied_units', 0)
        
        # Update weekly schedule with proper occupancy calculations
        total_units = box_metrics.get('total_units', 0)
        base_occupied = box_metrics.get('occupied_units', 0)
        
        for i, day in enumerate(move_metrics.get('weekly_schedule', [])):
            # Calculate cumulative moves up to this day
            cumulative_moves = sum([
                d['move_ins'] - d['move_outs'] 
                for d in move_metrics['weekly_schedule'][:i+1]
            ])
            day['units'] = base_occupied + cumulative_moves
            
            if total_units > 0:
                day['occupancy'] = f"{(day['units'] / total_units * 100):.0f}%"
    
    # Calculate projections
    if box_metrics and move_metrics:
        projection_data = calculate_projection(box_metrics, move_metrics)
    
    # Calculate Net to Rent
    net_to_rent = calculate_net_to_rent(box_metrics, unit_counts)
    
    # Count work orders and make ready
    work_orders_count = 0
    make_ready_count = 0
    
    if file_availability['work_order_report']:
        work_orders_data = raw_data['work_order_report'].get('work_orders')
        if work_orders_data is not None and not work_orders_data.empty:
            work_orders_count = len(work_orders_data)
    
    if file_availability['pending_make_ready']:
        make_ready_data = raw_data['pending_make_ready'].get('make_ready_data')
        if make_ready_data is not None and not make_ready_data.empty:
            make_ready_count = len(make_ready_data)
    
    # Calculate collections rate
    collections_rate = 0.0
    if file_availability['resaranalytics_delinquency']:
        collections_rate = calculate_collections_rate(raw_data['resaranalytics_delinquency'], box_metrics)
    
    # Get traffic metrics
    traffic_metrics = get_traffic_metrics(raw_data.get('resanalytics_box_score', {}))
    
    # Render dashboard sections
    
    # 1. KPI Cards
    st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
    kpi_metrics = {
        'projection_percent': projection_data.get('projection_percent', 0),
        'status': projection_data.get('status', 'UNKNOWN'),
        'percent_leased': box_metrics.get('percent_leased', 0),
        'percent_occupied': box_metrics.get('percent_occupied', 0),
        'collections_rate': collections_rate
    }
    render_kpi_cards(kpi_metrics)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 2. Main content in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        render_current_occupancy(box_metrics, unit_counts, net_to_rent)
    
    with col2:
        render_projections_applications(
            projection_data.get('projection_percent', 0), 
            traffic_metrics
        )
    
    with col3:
        render_maintenance(work_orders_count, make_ready_count)
    
    with col4:
        # Pass raw unit availability data instead of processed move_metrics
        unit_availability_data = raw_data.get('resanalytics_unit_availability', {})
        current_occupied = box_metrics.get('occupied_units', 0)
        total_property_units = box_metrics.get('total_units', 0)
        render_move_schedule(unit_availability_data, total_property_units, current_occupied)
    
    # 3. Historical Analytics & Graphs Section
    # Load comprehensive report data for historical analysis
    comprehensive_historical_data = None
    full_comprehensive_data = None
    matching_report = None
    debug_info = []
    
    try:
        print(f"🔍 COMPREHENSIVE: Looking for Weekly Report for '{selected_property}' in week '{selected_week}'")
        
        # Look for comprehensive report (Weekly Report) for this property in same week/property folder
        from utils.s3_service import S3DataService
        storage_service = S3DataService()
        
        # List all files in the current week/property folder
        folder_path = f"{selected_week}/{selected_property}"
        all_files = storage_service.list_files(folder_path)
        
        print(f"🔍 COMPREHENSIVE: All files in {folder_path}: {all_files}")
        
        # Filter for files containing "Weekly Report"
        excel_files = [f for f in all_files if 'weekly report' in f.lower() and f.endswith('.xlsx') and not f.startswith('~$')]
        
        print(f"🔍 COMPREHENSIVE: Weekly Report files found: {excel_files}")
        
        # Use first Weekly Report file found
        matching_report = None
        if excel_files:
            filename = excel_files[0]
            matching_report = f"{selected_week}/{selected_property}/{filename}"
            print(f"🔍 COMPREHENSIVE: Using Weekly Report: {filename}")
            print(f"🔍 COMPREHENSIVE: Full S3 path: {matching_report}")
        else:
            print(f"🔍 COMPREHENSIVE: No Weekly Report files found in {folder_path}")
            print(f"🔍 COMPREHENSIVE: Files need to contain 'weekly report' (case insensitive)")
        
        if matching_report:
            print(f"🔍 COMPREHENSIVE: Downloading and parsing: {matching_report}")
            
            # Download file from S3 to temp location preserving original filename
            import tempfile, os
            temp_dir = tempfile.mkdtemp()
            original_filename = matching_report.split('/')[-1]  # Get just the filename
            temp_file_path = os.path.join(temp_dir, original_filename)
            
            # Read file from S3 and write to temp file with original name
            file_content = storage_service.read_file(matching_report)
            print(f"🔍 COMPREHENSIVE: Downloaded {len(file_content)} bytes from S3")
            print(f"🔍 COMPREHENSIVE: Temp file: {temp_file_path}")
            
            with open(temp_file_path, 'wb') as f:
                f.write(file_content)
            
            # Now use the original parse_file() with preserved filename
            from parsers.file_parser import parse_file
            comprehensive_data = parse_file(temp_file_path)
            
            # Clean up temp directory
            import shutil
            shutil.rmtree(temp_dir)
            
            print(f"🔍 COMPREHENSIVE: Parse result type: {type(comprehensive_data)}")
            if isinstance(comprehensive_data, dict):
                print(f"🔍 COMPREHENSIVE: Parse result keys: {list(comprehensive_data.keys())}")
                
                if 'error' in comprehensive_data:
                    print(f"❌ COMPREHENSIVE: Parse error: {comprehensive_data['error']}")
                elif 'historical_data' in comprehensive_data:
                    comprehensive_historical_data = comprehensive_data['historical_data']
                    full_comprehensive_data = comprehensive_data
                    print(f"✅ COMPREHENSIVE: Historical data loaded successfully")
                    print(f"🔍 COMPREHENSIVE: Historical data keys: {list(comprehensive_historical_data.keys())}")
                    if 'weekly_occupancy_data' in comprehensive_historical_data:
                        print(f"✅ COMPREHENSIVE: Found {len(comprehensive_historical_data['weekly_occupancy_data'])} weeks of occupancy data")
                    else:
                        print(f"❌ COMPREHENSIVE: No 'weekly_occupancy_data' key found")
                else:
                    print(f"❌ COMPREHENSIVE: No 'historical_data' key in parsed data")
            else:
                print(f"❌ COMPREHENSIVE: Parse result is not a dictionary")
        else:
            print(f"❌ COMPREHENSIVE: No Weekly Report found for {selected_property}")
                
    except Exception as e:
        print(f"❌ COMPREHENSIVE: Exception occurred: {str(e)}")
        import traceback
        print(f"❌ COMPREHENSIVE: Traceback: {traceback.format_exc()}")
    
    print(f"🔍 COMPREHENSIVE: Final result - historical_data: {'Found' if comprehensive_historical_data else 'None'}")
    
    render_graphs_section(comprehensive_historical_data, selected_property, full_comprehensive_data)


if __name__ == "__main__":
    main()
