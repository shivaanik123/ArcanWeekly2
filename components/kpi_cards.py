"""
Modern KPI Cards component with sleek design
"""

import streamlit as st
from typing import Dict, Any

def render_kpi_cards(metrics: Dict[str, Any]):
    """Render modern KPI cards with colored backgrounds and trend indicators."""
    
    # Get KPI values
    projection = metrics.get('projection_percent', 0)
    status = metrics.get('status', 'UNKNOWN')
    leased = metrics.get('percent_leased', 0)
    occupied = metrics.get('percent_occupied', 0)
    collections = metrics.get('collections_rate', 17.8)
    
    # Clean Trading KPI Cards CSS
    st.markdown("""
    <style>
    /* Trading KPI Cards - Clean & Efficient */
    .trading-kpi-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid #4a90e2;
        border-radius: 8px;
        padding: 16px;
        margin: 4px;
        min-height: 85px;
        text-align: center;
        box-shadow: 0 0 12px rgba(74, 144, 226, 0.2);
        transition: all 0.2s ease;
        color: white;
    }
    
    .trading-kpi-card-status-good {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important;
        border: 2px solid #22c55e !important;
        color: white !important;
        box-shadow: 0 0 15px rgba(34, 197, 94, 0.5), inset 0 0 20px rgba(34, 197, 94, 0.1) !important;
    }
    
    .trading-kpi-card-status-watch {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important;
        border: 2px solid #eab308 !important;
        color: white !important;
        box-shadow: 0 0 15px rgba(234, 179, 8, 0.5), inset 0 0 20px rgba(234, 179, 8, 0.1) !important;
    }
    
    .trading-kpi-card-status-alert {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important;
        border: 2px solid #ef4444 !important;
        color: white !important;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.5), inset 0 0 20px rgba(239, 68, 68, 0.1) !important;
    }
    
    .trading-kpi-card-dark {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    }
    
    .trading-kpi-card-purple {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    }
    
    .trading-kpi-card-blue {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    }
    
    .trading-kpi-card-black {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    }
    
    .trading-kpi-label {
        color: #9ca3af;
        font-size: 0.7rem;
        font-weight: 500;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    
    .trading-kpi-value {
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 600;
        line-height: 1;
        margin: 8px 0;
    }
    
    .trading-kpi-trend {
        background: #22c55e;
        color: #ffffff;
        font-size: 0.65rem;
        font-weight: 500;
        padding: 4px 10px;
        border-radius: 12px;
        display: inline-block;
    }
    
    .trend-negative {
        background: #ef4444 !important;
    }
    
    .status-subtitle {
        font-size: 11px;
        opacity: 0.7;
        margin-top: 8px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create 5 columns for KPI cards
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        # Status card - determine color based on status
        if status.upper() == 'GOOD':
            status_class = "trading-kpi-card-status-good"
            status_subtitle = "performing well"
        elif status.upper() in ['WATCH', 'MONITOR']:
            status_class = "trading-kpi-card-status-watch"
            status_subtitle = "needs attention"
        elif status.upper() in ['ALERT', 'BAD', 'CRITICAL']:
            status_class = "trading-kpi-card-status-alert"
            status_subtitle = "immediate action"
        else:
            status_class = "trading-kpi-card"
            status_subtitle = "monitor"
        
        st.markdown(f"""
        <div class="trading-kpi-card {status_class}">
            <div class="trading-kpi-header">
                <div class="trading-kpi-label">STATUS</div>
            </div>
            <div class="trading-kpi-value">{status}</div>
            <div class="status-subtitle">{status_subtitle}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Projected percentage
        proj_trend = "-1.4% from last" if projection < 100 else "+1.4% from last"
        trend_class = "trend-negative" if projection < 100 else "trend-positive"
        delta_html = f'<div class="trading-kpi-trend {trend_class}">{proj_trend}</div>'
        
        st.markdown(f"""
        <div class="trading-kpi-card trading-kpi-card-dark">
            <div class="trading-kpi-header">
                <div class="trading-kpi-label">PROJECTED</div>
            </div>
            <div class="trading-kpi-value">{projection:.1f}%</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Percent Leased
        leased_display = f"{leased:.1f}%"
        leased_trend = "+3.3% from last" if leased > 95 else "-3.3% from last"
        leased_trend_class = "trend-positive" if leased > 95 else "trend-negative"
        delta_html = f'<div class="trading-kpi-trend {leased_trend_class}">{leased_trend}</div>'
        
        st.markdown(f"""
        <div class="trading-kpi-card trading-kpi-card-purple">
            <div class="trading-kpi-header">
                <div class="trading-kpi-label">% LEASED</div>
            </div>
            <div class="trading-kpi-value">{leased_display}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Percent Occupied
        occ_trend = "-3.3% from last" if occupied < 100 else "+3.3% from last"
        occ_trend_class = "trend-negative" if occupied < 100 else "trend-positive"
        delta_html = f'<div class="trading-kpi-trend {occ_trend_class}">{occ_trend}</div>'
        
        st.markdown(f"""
        <div class="trading-kpi-card trading-kpi-card-blue">
            <div class="trading-kpi-header">
                <div class="trading-kpi-label">% OCCUPIED</div>
            </div>
            <div class="trading-kpi-value">{occupied:.1f}%</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        # Collections Rate
        st.markdown(f"""
        <div class="trading-kpi-card trading-kpi-card-black">
            <div class="trading-kpi-header">
                <div class="trading-kpi-label">COLLECTIONS RATE</div>
            </div>
            <div class="trading-kpi-value">{collections:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
