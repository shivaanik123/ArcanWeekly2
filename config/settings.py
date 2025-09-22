"""
Dashboard configuration settings
"""

# Dashboard settings
DASHBOARD_TITLE = "Real Estate Property Dashboard"
PAGE_ICON = "🏢"

# Data paths
DATA_BASE_PATH = "../data"

# CDN Configuration
# Set CDN_BASE_URL environment variable to use S3 bucket for logos
# Example: export CDN_BASE_URL="https://arcan-dashboard-data-dev-408312670144.s3.amazonaws.com/logos"
# Default fallback: "./logos" (local files)

# KPI thresholds
PROJECTION_THRESHOLDS = {
    'ALERT': 0.90,
    'GOOD': 0.95
}

# Styling
KPI_CARD_STYLE = """
<style>
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin: 0.5rem 0;
}
.metric-value {
    font-size: 2.5rem;
    font-weight: bold;
    margin: 0.5rem 0;
}
.metric-label {
    font-size: 0.9rem;
    opacity: 0.8;
}
.metric-change {
    font-size: 0.8rem;
    margin-top: 0.3rem;
}
.status-good { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
.status-watch { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.status-alert { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); }
</style>
"""

# Date format for move schedule
DATE_FORMAT = "%Y-%m-%d"
MOVE_SCHEDULE_DAYS = 7  # 7-day forecast

# Component display options
SHOW_DEBUG_INFO = False
MAX_ROWS_IN_TABLES = 20
