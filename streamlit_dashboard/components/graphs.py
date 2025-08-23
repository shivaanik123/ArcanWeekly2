"""
Graphs section component for historical data visualization
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

def render_graphs_section(historical_data: Dict[str, Any], property_name: str = "Property", comprehensive_data: Dict[str, Any] = None):
    """
    Render graphs section with historical trends and analytics.
    
    Args:
        historical_data: Dictionary containing historical data from comprehensive reports
        property_name: Name of the property for titles
    """
    
    
    # Check if we have historical data
    if not historical_data or 'weekly_occupancy_data' not in historical_data:
        st.warning("📈 No historical data available for graphs. Load comprehensive reports to see trends.")
        return
    
    weekly_data = historical_data['weekly_occupancy_data']
    
    if not weekly_data:
        st.warning("📊 No weekly historical data found.")
        return
    
    # Convert to DataFrame for easier plotting
    df = pd.DataFrame(weekly_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Filter out invalid data points
    df = df[df['occupancy_percent'] > 0]  # Remove 0% occupancy (likely data gaps)
    
    if df.empty:
        st.warning("📊 No valid historical data points found after filtering.")
        return
    
    st.write(f"**Displaying {len(df)} weeks of historical data for {property_name}**")
    st.write(f"**Date range**: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Occupancy Trends")
        render_occupancy_trends(df, property_name)
    
    with col2:
        st.markdown("### Lease Expirations")
        render_lease_expirations_chart(df, property_name)
    
    # Second row: Performance Summary and Monthly Overview side by side
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("### Revenue vs Expenses")
        render_revenue_expenses_chart(comprehensive_data, property_name)
    
    with col4:
        st.markdown("### Rent Trends")
        render_rent_trends_chart(comprehensive_data, property_name)
    
    # Third row: Collections and Maintenance Analytics side by side
    col5, col6 = st.columns(2)
    
    with col5:
        st.markdown("### Collections Performance")
        render_collections_chart(comprehensive_data, property_name)
    
    with col6:
        st.markdown("### Maintenance Analytics")
        render_interactive_maintenance_chart(comprehensive_data, property_name)


def render_occupancy_trends(df: pd.DataFrame, property_name: str):
    """Render occupancy trend charts as 2D area line graph with blue shades."""
    
    # Create the figure
    fig = go.Figure()
    
    # Define three shades of blue (light to dark)
    blue_colors = {
        'projected': '#93c5fd',    # Light blue for projected
        'leased': '#3b82f6',       # Medium blue for leased  
        'occupancy': '#1e40af'     # Dark blue for occupancy
    }
    
    # Add projection area (lightest blue, bottom layer)
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['projection_percent'] * 100,
            name="Projected %",
            fill='tozeroy',
            fillcolor='rgba(147, 197, 253, 0.3)',  # Light blue with transparency
            line=dict(color=blue_colors['projected'], width=2),
            mode='lines',
            hovertemplate='<b>Projected</b><br>Date: %{x}<br>Percentage: %{y:.1f}%<extra></extra>'
        )
    )
    
    # Add leased area (medium blue, middle layer)
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['leased_percent'] * 100,
            name="Leased %",
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.4)',  # Medium blue with transparency
            line=dict(color=blue_colors['leased'], width=2),
            mode='lines',
            hovertemplate='<b>Leased</b><br>Date: %{x}<br>Percentage: %{y:.1f}%<extra></extra>'
        )
    )
    
    # Add occupancy area (darkest blue, top layer)
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['occupancy_percent'] * 100,
            name="Occupancy %",
            fill='tozeroy',
            fillcolor='rgba(30, 64, 175, 0.5)',  # Dark blue with transparency
            line=dict(color=blue_colors['occupancy'], width=3),
            mode='lines',
            hovertemplate='<b>Occupancy</b><br>Date: %{x}<br>Percentage: %{y:.1f}%<extra></extra>'
        )
    )
    
    # Update layout for dark theme and proper scaling
    fig.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        legend=dict(
            bgcolor='rgba(30, 41, 59, 0.8)',
            bordercolor='rgba(74, 144, 226, 0.3)',
            borderwidth=1,
            font=dict(color='white', size=12)
        ),
        xaxis=dict(
            gridcolor='rgba(74, 144, 226, 0.2)',
            color='white',
            title="Date",
            title_font=dict(size=14),
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            gridcolor='rgba(74, 144, 226, 0.2)',
            color='white',
            title="Percentage (%)",
            title_font=dict(size=14),
            tickfont=dict(size=12),
            range=[0, 100],  # Set y-axis from 0 to 100%
            tickmode='linear',
            dtick=10  # Show ticks every 10%
        ),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)



def render_lease_expirations_chart(df: pd.DataFrame, property_name: str):
    """Render lease expirations bar chart with gradient blue design using real data."""
    
    # Load actual lease expiration data
    lease_file_path = "/Users/shivaanikomanduri/ArcanClean/data/08_04_2025/Marbella /ResAnalytic_Lease_Expiration_marbla.xlsx"
    
    months = []
    expirations = []
    
    try:
        # Import the lease parser
        import os
        import sys
        sys.path.append('/Users/shivaanikomanduri/ArcanClean')
        from parsers.resanalytic_lease_parser import parse_resanalytic_lease_expiration
        
        # Parse the lease expiration file
        if os.path.exists(lease_file_path):
            lease_data = parse_resanalytic_lease_expiration(lease_file_path)
            
            if 'lease_expiration_data' in lease_data and not lease_data['lease_expiration_data'].empty:
                lease_df = lease_data['lease_expiration_data']
                
                # Get the first row (actual property data, not the total row)
                property_row = lease_df.iloc[0]
                
                # Extract monthly expiration data from the actual columns
                month_columns = ['Aug 2025', 'Sep 2025', 'Oct 2025', 'Nov 2025', 'Dec 2025', 
                               'Jan 2026', 'Feb 2026', 'Mar 2026', 'Apr 2026', 'May 2026', 'Jun 2026', 'Jul 2026']
                
                # Create display month names
                month_names = ['Aug 25', 'Sep 25', 'Oct 25', 'Nov 25', 'Dec 25', 
                              'Jan 26', 'Feb 26', 'Mar 26', 'Apr 26', 'May 26', 'Jun 26', 'Jul 26']
                
                # Extract actual expiration counts
                expiration_counts = []
                for col in month_columns:
                    if col in lease_df.columns:
                        # Get value from property row, handle any data type issues
                        value = property_row[col]
                        if pd.isna(value) or value == '':
                            expiration_counts.append(0)
                        else:
                            try:
                                expiration_counts.append(int(float(str(value))))
                            except (ValueError, TypeError):
                                expiration_counts.append(0)
                    else:
                        expiration_counts.append(0)
                
                months = month_names
                expirations = expiration_counts
            else:
                # Fallback if no data available
                raise Exception("No lease expiration data found")
                
        else:
            raise Exception(f"Lease file not found: {lease_file_path}")
            
    except Exception as e:
        # Fallback to sample data if real data can't be loaded
        st.caption(f"⚠️ Using sample data (could not load: {str(e)[:50]}...)")
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        sample_expirations = [6, 5, 8, 7, 9, 11, 10, 10, 8, 9, 7, 6]
        months = month_names
        expirations = sample_expirations
    
    # Create gradient blue colors for bars (12 months)
    gradient_colors = [
        '#e3f2fd',  # Very light blue - Aug 25
        '#bbdefb',  # Light blue - Sep 25
        '#90caf9',  # Lighter blue - Oct 25
        '#64b5f6',  # Light-medium blue - Nov 25
        '#42a5f5',  # Medium blue - Dec 25
        '#2196f3',  # Standard blue - Jan 26
        '#1e88e5',  # Medium-dark blue - Feb 26
        '#1976d2',  # Dark blue - Mar 26
        '#1565c0',  # Darker blue - Apr 26
        '#0d47a1',  # Very dark blue - May 26
        '#1565c0',  # Darker blue - Jun 26
        '#1976d2'   # Dark blue - Jul 26
    ]
    
    # Create the bar chart
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            x=months,
            y=expirations,
            name="Lease Expirations",
            marker=dict(
                color=gradient_colors,
                line=dict(color='rgba(255,255,255,0.2)', width=1)
            ),
            hovertemplate='<b>%{x}</b><br>Expirations: %{y}<extra></extra>'
        )
    )
    
    # Update layout for dark theme
    fig.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(
            gridcolor='rgba(74, 144, 226, 0.2)',
            color='white',
            title="Month",
            title_font=dict(size=14),
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            gridcolor='rgba(74, 144, 226, 0.2)',
            color='white',
            title="Number of Expirations",
            title_font=dict(size=14),
            tickfont=dict(size=12)
        ),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)



def render_rent_trends_chart(comprehensive_data: Dict[str, Any], property_name: str):
    """Render rent trends line chart showing market rent vs occupied rent over time."""
    
    # Parse rent data directly from the comprehensive report file (same approach as occupancy trends)
    import pandas as pd
    import os
    
    file_path = "/Users/shivaanikomanduri/ArcanClean/data/Comprehensive Reports/Comprehensive Reports/Marbella Weekly Report.xlsx"
    
    if not os.path.exists(file_path):
        st.warning("📈 Comprehensive report file not found.")
        return
    
    try:
        # Read the Financial sheet directly (same as occupancy reads from Occupancy sheet)
        df = pd.read_excel(file_path, sheet_name='Financial', header=None)
        
        # Extract rent data from columns 12 (date), 13 (market rent), 14 (occupied rent)
        rent_data = []
        
        for i in range(2, len(df)):  # Start from row 2
            try:
                # Get date from column 12
                date_cell = df.iloc[i, 12] if df.shape[1] > 12 else None
                if pd.notna(date_cell) and hasattr(date_cell, 'year'):
                    # Get rent values from columns 13 and 14
                    market_rent = df.iloc[i, 13] if df.shape[1] > 13 and not pd.isna(df.iloc[i, 13]) else 0
                    occupied_rent = df.iloc[i, 14] if df.shape[1] > 14 and not pd.isna(df.iloc[i, 14]) else 0
                    
                    # Convert to float
                    try:
                        market_rent = float(str(market_rent).replace(',', '').replace('$', ''))
                        occupied_rent = float(str(occupied_rent).replace(',', '').replace('$', ''))
                    except (ValueError, TypeError):
                        continue
                    
                    rent_data.append({
                        'date': date_cell,
                        'market_rent': market_rent,
                        'occupied_rent': occupied_rent
                    })
            except Exception:
                continue
        
        if not rent_data:
            st.warning("📈 No rent data found in Financial sheet.")
            return
            
    except Exception as e:
        st.error(f"Error reading Financial sheet: {str(e)}")
        return
    
    # Convert to DataFrame for easier plotting
    df_rent = pd.DataFrame(rent_data)
    df_rent['date'] = pd.to_datetime(df_rent['date'])
    df_rent = df_rent.sort_values('date')
    
    # Create the line chart
    fig = go.Figure()
    
    # Add Market Rent line (lighter blue)
    fig.add_trace(
        go.Scatter(
            x=df_rent['date'],
            y=df_rent['market_rent'],
            name="Market Rent",
            line=dict(color='#60a5fa', width=3),
            mode='lines+markers',
            marker=dict(size=4),
            hovertemplate='<b>Market Rent</b><br>Date: %{x}<br>Amount: $%{y:.2f}<extra></extra>'
        )
    )
    
    # Add Occupied Rent line (darker blue)
    fig.add_trace(
        go.Scatter(
            x=df_rent['date'],
            y=df_rent['occupied_rent'],
            name="Occupied Rent",
            line=dict(color='#1d4ed8', width=3),
            mode='lines+markers',
            marker=dict(size=4),
            hovertemplate='<b>Occupied Rent</b><br>Date: %{x}<br>Amount: $%{y:.2f}<extra></extra>'
        )
    )
    
    # Update layout for dark theme (matching lease expirations chart)
    fig.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(
            gridcolor='rgba(74, 144, 226, 0.2)',
            color='white',
            title="Date",
            title_font=dict(size=14),
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            gridcolor='rgba(74, 144, 226, 0.2)',
            color='white',
            title="Rent Amount ($)",
            title_font=dict(size=14),
            tickfont=dict(size=12),
            tickformat='$,.0f'
        ),
        hovermode='x unified',
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)



def render_maintenance_analytics(df: pd.DataFrame, property_name: str):
    """Render maintenance and work order analytics."""
    
    # Create subplots for work orders and make ready
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=[
            "Work Orders Over Time",
            "Make Ready Units Over Time"
        ],
        vertical_spacing=0.15
    )
    
    # Work orders chart
    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['work_orders_count'],
            name="Work Orders",
            marker_color="#ef4444",
            opacity=0.8
        ),
        row=1, col=1
    )
    
    # Make ready units chart
    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['make_readies_count'],
            name="Make Ready Units",
            marker_color="#f59e0b",
            opacity=0.8
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        showlegend=False
    )
    
    fig.update_xaxes(gridcolor='rgba(74, 144, 226, 0.2)', color='white')
    fig.update_yaxes(gridcolor='rgba(74, 144, 226, 0.2)', color='white')
    
    st.plotly_chart(fig, use_container_width=True)



def render_performance_summary(df: pd.DataFrame, property_name: str):
    """Render performance summary with correlation analysis."""
    
    # Performance correlation heatmap
    correlation_data = df[['occupancy_percent', 'leased_percent', 'projection_percent', 'work_orders_count', 'make_readies_count']].corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=correlation_data.values,
        x=correlation_data.columns,
        y=correlation_data.columns,
        colorscale='RdBu',
        zmid=0,
        text=correlation_data.round(2).values,
        texttemplate="%{text}",
        textfont={"size":12, "color":"white"},
        colorbar=dict(title="Correlation")
    ))
    
    fig.update_layout(
        title="Performance Metrics Correlation",
        height=350,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        title_font=dict(color='white', size=16)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_interactive_maintenance_chart(comprehensive_data: Dict[str, Any], property_name: str):
    """Render interactive maintenance analytics with time period selection."""
    
    # Get historical data from the parsed comprehensive reports
    if not comprehensive_data or 'historical_data' not in comprehensive_data:
        st.warning("No historical data available for maintenance analytics.")
        return
    
    historical_data = comprehensive_data['historical_data']
    if 'weekly_occupancy_data' not in historical_data:
        st.warning("No weekly occupancy data available for maintenance analytics.")
        return
    
    weekly_data = historical_data['weekly_occupancy_data']
    if not weekly_data:
        st.warning("No maintenance data found in historical records.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(weekly_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Filter out invalid data
    df = df[df['work_orders_count'].notna() | df['make_readies_count'].notna()]
    
    if df.empty:
        st.warning("No valid maintenance data found.")
        return
    
    # Time period selection
    col1, col2 = st.columns([1, 3])
    
    with col1:
        time_period = st.selectbox(
            "Select Time Period:",
            options=["3 Months", "6 Months", "12 Months"],
            index=0  # Default to 3 months
        )
    
    # Filter data based on selected time period
    end_date = df['date'].max()
    if time_period == "3 Months":
        start_date = end_date - pd.DateOffset(months=3)
    elif time_period == "6 Months":
        start_date = end_date - pd.DateOffset(months=6)
    else:  # 12 Months
        start_date = end_date - pd.DateOffset(months=12)
    
    filtered_df = df[df['date'] >= start_date].copy()
    
    if filtered_df.empty:
        st.warning(f"No data available for the selected {time_period.lower()} period.")
        return
    
    # Create the maintenance chart
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=[
            f"Work Orders - Last {time_period}",
            f"Make Ready Units - Last {time_period}"
        ],
        vertical_spacing=0.15
    )
    
    # Work orders chart (blue bars)
    fig.add_trace(
        go.Bar(
            x=filtered_df['date'],
            y=filtered_df['work_orders_count'],
            name="Work Orders",
            marker_color="#3b82f6",
            opacity=0.8,
            hovertemplate='<b>Work Orders</b><br>Date: %{x}<br>Count: %{y}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Make ready units chart (light blue bars)
    fig.add_trace(
        go.Bar(
            x=filtered_df['date'],
            y=filtered_df['make_readies_count'],
            name="Make Ready Units",
            marker_color="#60a5fa",
            opacity=0.8,
            hovertemplate='<b>Make Ready Units</b><br>Date: %{x}<br>Count: %{y}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=500,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        showlegend=False
    )
    
    # Update x-axes
    fig.update_xaxes(
        gridcolor='rgba(74, 144, 226, 0.2)',
        color='white',
        title="Date",
        title_font=dict(size=12),
        tickfont=dict(size=10)
    )
    
    # Update y-axes
    fig.update_yaxes(
        gridcolor='rgba(74, 144, 226, 0.2)',
        color='white',
        title="Count",
        title_font=dict(size=12),
        tickfont=dict(size=10)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show summary statistics for the selected period
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_work_orders = filtered_df['work_orders_count'].mean()
        st.metric("Avg Work Orders", f"{avg_work_orders:.1f}")
    
    with col2:
        total_work_orders = filtered_df['work_orders_count'].sum()
        st.metric("Total Work Orders", f"{int(total_work_orders)}")
    
    with col3:
        avg_make_ready = filtered_df['make_readies_count'].mean()
        st.metric("Avg Make Ready", f"{avg_make_ready:.1f}")
    
    with col4:
        total_make_ready = filtered_df['make_readies_count'].sum()
        st.metric("Total Make Ready", f"{int(total_make_ready)}")
    
    # Recent vs historical comparison
    recent_weeks = 12  # Last 3 months
    if len(df) > recent_weeks:
        recent_df = df.tail(recent_weeks)
        historical_df = df.head(-recent_weeks)
        
        st.markdown("### 📊 Recent vs Historical Performance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Recent 12 Weeks**")
            recent_occ = recent_df['occupancy_percent'].mean() * 100
            recent_wo = recent_df['work_orders_count'].mean()
            recent_mr = recent_df['make_readies_count'].mean()
            
            st.write(f"• Avg Occupancy: {recent_occ:.1f}%")
            st.write(f"• Avg Work Orders: {recent_wo:.1f}/week")
            st.write(f"• Avg Make Ready: {recent_mr:.1f}/week")
        
        with col2:
            st.markdown("**Historical Average**")
            hist_occ = historical_df['occupancy_percent'].mean() * 100
            hist_wo = historical_df['work_orders_count'].mean()
            hist_mr = historical_df['make_readies_count'].mean()
            
            st.write(f"• Avg Occupancy: {hist_occ:.1f}%")
            st.write(f"• Avg Work Orders: {hist_wo:.1f}/week")
            st.write(f"• Avg Make Ready: {hist_mr:.1f}/week")


def render_monthly_overview(df: pd.DataFrame, property_name: str):
    """Render monthly aggregated overview."""
    
    # Group by month
    df_monthly = df.copy()
    df_monthly['year_month'] = df_monthly['date'].dt.to_period('M')
    
    monthly_stats = df_monthly.groupby('year_month').agg({
        'occupancy_percent': 'mean',
        'leased_percent': 'mean',
        'work_orders_count': 'sum',
        'make_readies_count': 'mean'
    }).reset_index()
    
    monthly_stats['year_month_str'] = monthly_stats['year_month'].astype(str)
    
    # Create monthly overview chart
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "Monthly Average Occupancy",
            "Monthly Total Work Orders",
            "Monthly Average Leased %",
            "Monthly Average Make Ready"
        ],
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Occupancy
    fig.add_trace(
        go.Bar(x=monthly_stats['year_month_str'], 
               y=monthly_stats['occupancy_percent'] * 100,
               name="Occupancy %", marker_color="#3b82f6"),
        row=1, col=1
    )
    
    # Work Orders
    fig.add_trace(
        go.Bar(x=monthly_stats['year_month_str'], 
               y=monthly_stats['work_orders_count'],
               name="Work Orders", marker_color="#ef4444"),
        row=1, col=2
    )
    
    # Leased %
    fig.add_trace(
        go.Bar(x=monthly_stats['year_month_str'], 
               y=monthly_stats['leased_percent'] * 100,
               name="Leased %", marker_color="#22c55e"),
        row=2, col=1
    )
    
    # Make Ready
    fig.add_trace(
        go.Bar(x=monthly_stats['year_month_str'], 
               y=monthly_stats['make_readies_count'],
               name="Make Ready", marker_color="#f59e0b"),
        row=2, col=2
    )
    
    fig.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        showlegend=False
    )
    
    fig.update_xaxes(gridcolor='rgba(74, 144, 226, 0.2)', color='white')
    fig.update_yaxes(gridcolor='rgba(74, 144, 226, 0.2)', color='white')
    
    st.plotly_chart(fig, use_container_width=True)


def render_interactive_maintenance_chart(comprehensive_data: Dict[str, Any], property_name: str):
    """Render interactive maintenance analytics with time period selection."""
    
    # Get historical data from the parsed comprehensive reports
    if not comprehensive_data or 'historical_data' not in comprehensive_data:
        st.warning("No historical data available for maintenance analytics.")
        return
    
    historical_data = comprehensive_data['historical_data']
    if 'weekly_occupancy_data' not in historical_data:
        st.warning("No weekly occupancy data available for maintenance analytics.")
        return
    
    weekly_data = historical_data['weekly_occupancy_data']
    if not weekly_data:
        st.warning("No maintenance data found in historical records.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(weekly_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Filter out invalid data
    df = df[df['work_orders_count'].notna() | df['make_readies_count'].notna()]
    
    if df.empty:
        st.warning("No valid maintenance data found.")
        return
    
    # Time period selection
    col1, col2 = st.columns([1, 3])
    
    with col1:
        time_period = st.selectbox(
            "Select Time Period:",
            options=["3 Months", "6 Months", "12 Months"],
            index=0  # Default to 3 months
        )
    
    # Filter data based on selected time period
    end_date = df['date'].max()
    if time_period == "3 Months":
        start_date = end_date - pd.DateOffset(months=3)
    elif time_period == "6 Months":
        start_date = end_date - pd.DateOffset(months=6)
    else:  # 12 Months
        start_date = end_date - pd.DateOffset(months=12)
    
    filtered_df = df[df['date'] >= start_date].copy()
    
    if filtered_df.empty:
        st.warning(f"No data available for the selected {time_period.lower()} period.")
        return
    
    # Create the maintenance chart
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=[
            f"Work Orders - Last {time_period}",
            f"Make Ready Units - Last {time_period}"
        ],
        vertical_spacing=0.15
    )
    
    # Work orders chart (blue bars)
    fig.add_trace(
        go.Bar(
            x=filtered_df['date'],
            y=filtered_df['work_orders_count'],
            name="Work Orders",
            marker_color="#3b82f6",
            opacity=0.8,
            hovertemplate='<b>Work Orders</b><br>Date: %{x}<br>Count: %{y}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Make ready units chart (light blue bars)
    fig.add_trace(
        go.Bar(
            x=filtered_df['date'],
            y=filtered_df['make_readies_count'],
            name="Make Ready Units",
            marker_color="#60a5fa",
            opacity=0.8,
            hovertemplate='<b>Make Ready Units</b><br>Date: %{x}<br>Count: %{y}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=500,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        showlegend=False
    )
    
    # Update x-axes
    fig.update_xaxes(
        gridcolor='rgba(74, 144, 226, 0.2)',
        color='white',
        title="Date",
        title_font=dict(size=12),
        tickfont=dict(size=10)
    )
    
    # Update y-axes
    fig.update_yaxes(
        gridcolor='rgba(74, 144, 226, 0.2)',
        color='white',
        title="Count",
        title_font=dict(size=12),
        tickfont=dict(size=10)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show summary statistics for the selected period
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_work_orders = filtered_df['work_orders_count'].mean()
        st.metric("Avg Work Orders", f"{avg_work_orders:.1f}")
    
    with col2:
        total_work_orders = filtered_df['work_orders_count'].sum()
        st.metric("Total Work Orders", f"{int(total_work_orders)}")
    
    with col3:
        avg_make_ready = filtered_df['make_readies_count'].mean()
        st.metric("Avg Make Ready", f"{avg_make_ready:.1f}")
    
    with col4:
        total_make_ready = filtered_df['make_readies_count'].sum()
        st.metric("Total Make Ready", f"{int(total_make_ready)}")
    
    # Monthly data table
    if not monthly_stats.empty:
        st.markdown("### 📅 Monthly Summary Table")
        
        display_df = monthly_stats.copy()
        display_df['Occupancy %'] = (display_df['occupancy_percent'] * 100).round(1)
        display_df['Leased %'] = (display_df['leased_percent'] * 100).round(1)
        display_df['Work Orders'] = display_df['work_orders_count'].astype(int)
        display_df['Make Ready'] = display_df['make_readies_count'].round(1)
        
        table_df = display_df[['year_month_str', 'Occupancy %', 'Leased %', 'Work Orders', 'Make Ready']]
        table_df.columns = ['Month', 'Occupancy %', 'Leased %', 'Work Orders', 'Avg Make Ready']
        
        st.dataframe(table_df, use_container_width=True)


def render_revenue_expenses_chart(comprehensive_data: Dict[str, Any], property_name: str):
    """Render revenue vs expenses bar chart showing financial performance over time."""
    
    # Parse financial data directly from the comprehensive report file (same approach as rent trends)
    import pandas as pd
    import os
    
    file_path = "/Users/shivaanikomanduri/ArcanClean/data/Comprehensive Reports/Comprehensive Reports/Marbella Weekly Report.xlsx"
    
    if not os.path.exists(file_path):
        st.warning("Comprehensive report file not found.")
        return
    
    try:
        # Read the Financial sheet directly
        df = pd.read_excel(file_path, sheet_name='Financial', header=None)
        
        # Extract financial data from columns 12 (date), 15 (revenue), 16 (expenses)
        financial_data = []
        
        for i in range(2, len(df)):  # Start from row 2
            try:
                # Get date from column 12
                date_cell = df.iloc[i, 12] if df.shape[1] > 12 else None
                if pd.notna(date_cell) and hasattr(date_cell, 'year'):
                    # Get financial values from columns 15 and 16
                    revenue = df.iloc[i, 15] if df.shape[1] > 15 and not pd.isna(df.iloc[i, 15]) else 0
                    expenses = df.iloc[i, 16] if df.shape[1] > 16 and not pd.isna(df.iloc[i, 16]) else 0
                    
                    # Convert to float
                    try:
                        revenue = float(str(revenue).replace(',', '').replace('$', ''))
                        expenses = float(str(expenses).replace(',', '').replace('$', ''))
                    except (ValueError, TypeError):
                        continue
                    
                    financial_data.append({
                        'date': date_cell,
                        'revenue': revenue,
                        'expenses': expenses,
                        'net_income': revenue - expenses
                    })
            except Exception:
                continue
        
        if not financial_data:
            st.warning("No financial data found in Financial sheet.")
            return
            
    except Exception as e:
        st.error(f"Error reading Financial sheet: {str(e)}")
        return
    
    # Convert to DataFrame for easier plotting
    df_financial = pd.DataFrame(financial_data)
    df_financial['date'] = pd.to_datetime(df_financial['date'])
    df_financial = df_financial.sort_values('date')
    
    # Create the bar chart
    fig = go.Figure()
    
    # Add Revenue bars (dark blue)
    fig.add_trace(go.Bar(
        x=df_financial['date'],
        y=df_financial['revenue'],
        name='Revenue',
        marker_color='#1d4ed8',
        opacity=0.8,
        hovertemplate='<b>Revenue</b><br>Date: %{x}<br>Amount: $%{y:,.0f}<extra></extra>'
    ))
    
    # Add Expenses bars (light blue)
    fig.add_trace(go.Bar(
        x=df_financial['date'],
        y=df_financial['expenses'],
        name='Expenses',
        marker_color='#60a5fa',
        opacity=0.8,
        hovertemplate='<b>Expenses</b><br>Date: %{x}<br>Amount: $%{y:,.0f}<extra></extra>'
    ))
    
    # Update layout for dark theme
    fig.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(
            gridcolor='rgba(74, 144, 226, 0.2)',
            color='white',
            title="Date",
            title_font=dict(size=14),
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            gridcolor='rgba(74, 144, 226, 0.2)',
            color='white',
            title="Amount ($)",
            title_font=dict(size=14),
            tickfont=dict(size=12),
            tickformat='$,.0f'
        ),
        barmode='group',  # Group bars side by side
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            bgcolor='rgba(30, 41, 59, 0.8)',
            bordercolor='rgba(74, 144, 226, 0.3)',
            borderwidth=1,
            font=dict(color='white', size=12)
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)



def render_collections_chart(comprehensive_data: Dict[str, Any], property_name: str):
    """Render collections performance line chart showing collection rates over time."""
    
    # Parse collections data directly from the comprehensive report file (same approach as other charts)
    import pandas as pd
    import os
    
    file_path = "/Users/shivaanikomanduri/ArcanClean/data/Comprehensive Reports/Comprehensive Reports/Marbella Weekly Report.xlsx"
    
    if not os.path.exists(file_path):
        st.warning("Comprehensive report file not found.")
        return
    
    try:
        # Read the Financial sheet directly
        df = pd.read_excel(file_path, sheet_name='Financial', header=None)
        
        # Extract collections data from columns 12 (date), 19 (collections)
        collections_data = []
        
        for i in range(2, len(df)):  # Start from row 2
            try:
                # Get date from column 12
                date_cell = df.iloc[i, 12] if df.shape[1] > 12 else None
                if pd.notna(date_cell) and hasattr(date_cell, 'year'):
                    # Get collections value from column 19
                    collections = df.iloc[i, 19] if df.shape[1] > 19 and not pd.isna(df.iloc[i, 19]) else 0
                    
                    # Convert to float and percentage
                    try:
                        collections_rate = float(str(collections).replace(',', '').replace('%', ''))
                        # Convert to percentage if it's a decimal (0.99 -> 99%)
                        if collections_rate <= 1.0:
                            collections_rate = collections_rate * 100
                    except (ValueError, TypeError):
                        continue
                    
                    collections_data.append({
                        'date': date_cell,
                        'collections_rate': collections_rate
                    })
            except Exception:
                continue
        
        if not collections_data:
            st.warning("No collections data found in Financial sheet.")
            return
            
    except Exception as e:
        st.error(f"Error reading Financial sheet: {str(e)}")
        return
    
    # Convert to DataFrame for easier plotting
    df_collections = pd.DataFrame(collections_data)
    df_collections['date'] = pd.to_datetime(df_collections['date'])
    df_collections = df_collections.sort_values('date')
    
    # Create the line chart
    fig = go.Figure()
    
    # Add Collections line (blue)
    fig.add_trace(go.Scatter(
        x=df_collections['date'],
        y=df_collections['collections_rate'],
        mode='lines+markers',
        name='Collections Rate',
        line=dict(color='#3b82f6', width=3),
        marker=dict(size=6, color='#3b82f6'),
        hovertemplate='<b>Collections Rate</b><br>Date: %{x}<br>Rate: %{y:.2f}%<extra></extra>'
    ))
    
    # Update layout for dark theme
    fig.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(
            gridcolor='rgba(74, 144, 226, 0.2)',
            color='white',
            title="Date",
            title_font=dict(size=14),
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            gridcolor='rgba(74, 144, 226, 0.2)',
            color='white',
            title="Collections Rate (%)",
            title_font=dict(size=14),
            tickfont=dict(size=12),
            tickformat='.1f',
            range=[95, 100.5]  # Focus on the relevant range
        ),
        hovermode='x unified',
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_interactive_maintenance_chart(comprehensive_data: Dict[str, Any], property_name: str):
    """Render interactive maintenance analytics with time period selection."""
    
    # Get historical data from the parsed comprehensive reports
    if not comprehensive_data or 'historical_data' not in comprehensive_data:
        st.warning("No historical data available for maintenance analytics.")
        return
    
    historical_data = comprehensive_data['historical_data']
    if 'weekly_occupancy_data' not in historical_data:
        st.warning("No weekly occupancy data available for maintenance analytics.")
        return
    
    weekly_data = historical_data['weekly_occupancy_data']
    if not weekly_data:
        st.warning("No maintenance data found in historical records.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(weekly_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Filter out invalid data
    df = df[df['work_orders_count'].notna() | df['make_readies_count'].notna()]
    
    if df.empty:
        st.warning("No valid maintenance data found.")
        return
    
    # Time period selection
    col1, col2 = st.columns([1, 3])
    
    with col1:
        time_period = st.selectbox(
            "Select Time Period:",
            options=["3 Months", "6 Months", "12 Months"],
            index=0  # Default to 3 months
        )
    
    # Filter data based on selected time period
    end_date = df['date'].max()
    if time_period == "3 Months":
        start_date = end_date - pd.DateOffset(months=3)
    elif time_period == "6 Months":
        start_date = end_date - pd.DateOffset(months=6)
    else:  # 12 Months
        start_date = end_date - pd.DateOffset(months=12)
    
    filtered_df = df[df['date'] >= start_date].copy()
    
    if filtered_df.empty:
        st.warning(f"No data available for the selected {time_period.lower()} period.")
        return
    
    # Create the maintenance chart
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=[
            f"Work Orders - Last {time_period}",
            f"Make Ready Units - Last {time_period}"
        ],
        vertical_spacing=0.15
    )
    
    # Work orders chart (blue bars)
    fig.add_trace(
        go.Bar(
            x=filtered_df['date'],
            y=filtered_df['work_orders_count'],
            name="Work Orders",
            marker_color="#3b82f6",
            opacity=0.8,
            hovertemplate='<b>Work Orders</b><br>Date: %{x}<br>Count: %{y}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Make ready units chart (light blue bars)
    fig.add_trace(
        go.Bar(
            x=filtered_df['date'],
            y=filtered_df['make_readies_count'],
            name="Make Ready Units",
            marker_color="#60a5fa",
            opacity=0.8,
            hovertemplate='<b>Make Ready Units</b><br>Date: %{x}<br>Count: %{y}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=500,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        showlegend=False
    )
    
    # Update x-axes
    fig.update_xaxes(
        gridcolor='rgba(74, 144, 226, 0.2)',
        color='white',
        title="Date",
        title_font=dict(size=12),
        tickfont=dict(size=10)
    )
    
    # Update y-axes
    fig.update_yaxes(
        gridcolor='rgba(74, 144, 226, 0.2)',
        color='white',
        title="Count",
        title_font=dict(size=12),
        tickfont=dict(size=10)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show summary statistics for the selected period
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_work_orders = filtered_df['work_orders_count'].mean()
        st.metric("Avg Work Orders", f"{avg_work_orders:.1f}")
    
    with col2:
        total_work_orders = filtered_df['work_orders_count'].sum()
        st.metric("Total Work Orders", f"{int(total_work_orders)}")
    
    with col3:
        avg_make_ready = filtered_df['make_readies_count'].mean()
        st.metric("Avg Make Ready", f"{avg_make_ready:.1f}")
    
    with col4:
        total_make_ready = filtered_df['make_readies_count'].sum()
        st.metric("Total Make Ready", f"{int(total_make_ready)}")
def render_interactive_maintenance_chart(comprehensive_data: Dict[str, Any], property_name: str):
    """Render interactive maintenance analytics with time period selection."""
    
    # Get historical data from the parsed comprehensive reports
    if not comprehensive_data or 'historical_data' not in comprehensive_data:
        st.warning("No historical data available for maintenance analytics.")
        return
    
    historical_data = comprehensive_data['historical_data']
    if 'weekly_occupancy_data' not in historical_data:
        st.warning("No weekly occupancy data available for maintenance analytics.")
        return
    
    weekly_data = historical_data['weekly_occupancy_data']
    if not weekly_data:
        st.warning("No maintenance data found in historical records.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(weekly_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Filter out invalid data
    df = df[df['work_orders_count'].notna() | df['make_readies_count'].notna()]
    
    if df.empty:
        st.warning("No valid maintenance data found.")
        return
    
    # Time period selection at the top (legend-style)
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col4:  # Position in top-right like a legend
        time_period = st.selectbox(
            "Time Period:",
            options=["3 Months", "6 Months", "12 Months"],
            index=0,  # Default to 3 months
            label_visibility="collapsed"  # Hide the label for cleaner look
        )
    
    # Filter data based on selected time period
    end_date = df['date'].max()
    if time_period == "3 Months":
        start_date = end_date - pd.DateOffset(months=3)
    elif time_period == "6 Months":
        start_date = end_date - pd.DateOffset(months=6)
    else:  # 12 Months
        start_date = end_date - pd.DateOffset(months=12)
    
    filtered_df = df[df['date'] >= start_date].copy()
    
    if filtered_df.empty:
        st.warning(f"No data available for the selected {time_period.lower()} period.")
        return
    
    # Create the maintenance chart (both as 2D area graphs)
    fig = go.Figure()
    
    # Work orders as 2D area graph (dark blue)
    fig.add_trace(go.Scatter(
        x=filtered_df['date'],
        y=filtered_df['work_orders_count'],
        name='Work Orders',
        fill='tozeroy',
        fillcolor='rgba(29, 78, 216, 0.3)',  # Dark blue with transparency
        line=dict(color='#1d4ed8', width=2),
        mode='lines',
        hovertemplate='<b>Work Orders</b><br>Date: %{x}<br>Count: %{y}<extra></extra>'
    ))
    
    # Make ready units as 2D area graph (light blue)
    fig.add_trace(go.Scatter(
        x=filtered_df['date'],
        y=filtered_df['make_readies_count'],
        name='Make Ready Units',
        fill='tozeroy',
        fillcolor='rgba(96, 165, 250, 0.3)',  # Light blue with transparency
        line=dict(color='#60a5fa', width=2),
        mode='lines',
        hovertemplate='<b>Make Ready Units</b><br>Date: %{x}<br>Count: %{y}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        height=400,  # Match other charts
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        barmode='group',  # Group bars side by side
        xaxis=dict(
            gridcolor='rgba(74, 144, 226, 0.2)',
            color='white',
            title="Date",
            title_font=dict(size=14),
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            gridcolor='rgba(74, 144, 226, 0.2)',
            color='white',
            title="Count",
            title_font=dict(size=14),
            tickfont=dict(size=12)
        ),
        hovermode='x unified',
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
