"""Main Streamlit Dashboard Application"""

import streamlit as st
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(__file__))
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

st.set_page_config(
    page_title="Real Estate Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main dashboard application."""
    
    st.markdown("""
    <style>
    .stApp { background: #0a0e1a !important; color: #ffffff; }
    .main { background: #0a0e1a !important; color: #ffffff; }
    .main h1, .main h2, .main h3, .main h4 { color: #ffffff !important; font-weight: 700 !important; }
    .main h3 { color: #3b82f6 !important; font-size: 1.4rem !important; text-transform: uppercase !important; 
               border-bottom: 2px solid #3b82f6 !important; padding-bottom: 8px !important; margin-bottom: 20px !important; }
    section[data-testid="stSidebar"], aside[data-testid="stSidebar"] { background: #1e293b !important; border-right: 1px solid #4a90e2 !important; }
    header[data-testid="stHeader"] { background: transparent; box-shadow: none; height: 3rem; }
    .dashboard-card-content { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(74, 144, 226, 0.3) !important; 
                             border-radius: 12px !important; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important; overflow: hidden !important; }
    .metric-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; 
                  border-bottom: 1px solid rgba(74, 144, 226, 0.15); min-height: 48px; }
    .metric-row:first-child { background: rgba(74, 144, 226, 0.1); border-bottom: 2px solid rgba(74, 144, 226, 0.3); font-weight: 600; }
    .metric-row:hover:not(:first-child) { background: rgba(74, 144, 226, 0.08); }
    .metric-label { color: #e2e8f0; font-size: 0.9rem; font-weight: 500; flex: 1; }
    .metric-value { color: #ffffff; font-size: 0.9rem; font-weight: 600; text-align: right; min-width: 60px; }
    </style>
    """, unsafe_allow_html=True)
    
    # Handle upload notifications
    if st.session_state.get('upload_complete', False):
        uploaded_properties = st.session_state.get('last_upload_properties', [])
        if uploaded_properties:
            st.success(f"Data updated for: {', '.join(uploaded_properties)}")
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
    # Load centralized historical data from S3
    comprehensive_historical_data = None
    full_comprehensive_data = None

    try:
        print(f"🔍 HISTORICAL: Loading centralized historical data for '{selected_property}'")

        from utils.s3_service import S3DataService
        from utils.historical_data_service import HistoricalDataService

        storage_service = S3DataService()
        historical_service = HistoricalDataService(storage_service)

        # Load centralized historical data
        historical_data = historical_service.load_historical_data(selected_property)

        if historical_data:
            print(f"✅ HISTORICAL: Centralized historical data loaded successfully")

            # Convert to format expected by render_graphs_section
            comprehensive_historical_data = {
                'weekly_occupancy_data': []
            }

            # Convert ISO date strings back to datetime objects and restructure for compatibility
            for record in historical_data.get('weekly_occupancy_data', []):
                # Convert date string to datetime if needed
                from datetime import datetime
                date_obj = datetime.fromisoformat(record['date']) if isinstance(record['date'], str) else record['date']

                comprehensive_historical_data['weekly_occupancy_data'].append({
                    'date': date_obj,
                    'occupancy_percentage': record.get('occupancy_percentage', 0.0),
                    'leased_percentage': record.get('leased_percentage', 0.0),
                    'projected_percentage': record.get('projected_percentage', 0.0),
                    'make_readies_count': record.get('make_readies_count', 0),
                    'work_orders_count': record.get('work_orders_count', 0)
                })

            print(f"✅ HISTORICAL: Found {len(comprehensive_historical_data['weekly_occupancy_data'])} weeks of occupancy data")

            # Create full comprehensive data structure for compatibility
            full_comprehensive_data = {
                'metadata': historical_data.get('metadata', {}),
                'historical_data': comprehensive_historical_data
            }

        else:
            print(f"❌ HISTORICAL: No centralized historical data found for {selected_property}")
            print(f"ℹ️  HISTORICAL: Upload weekly reports to build historical data")

    except Exception as e:
        print(f"❌ HISTORICAL: Exception occurred: {str(e)}")
        import traceback
        print(f"❌ HISTORICAL: Traceback: {traceback.format_exc()}")

    print(f"🔍 HISTORICAL: Final result - historical_data: {'Found' if comprehensive_historical_data else 'None'}")

    render_graphs_section(comprehensive_historical_data, selected_property, full_comprehensive_data)

if __name__ == "__main__":
    main()
