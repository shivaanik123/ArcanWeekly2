"""Upload configuration with property list and file patterns"""

UPLOAD_PROPERTIES = [
    "55 Pharr",
    "Abbey Lake", 
    "Capella",
    "Colony Woods",
    "Emerson 1600",
    "Georgetown",
    "Hamptons at East Cobb",
    "Haven",
    "Kensington Place",
    "Longview",
    "Manchester at Weslyn",
    "Marbella",
    "Marsh Point",
    "Perry Heights",
    "Portico at Lanier",
    "Tall Oaks",
    "Tapestry Park",
    "The Hangar",
    "The Turn",
    "Woodland Commons"
]

REQUIRED_FILE_PATTERNS = {
    "ResAnalytics Box Score Summary": {
        "pattern": "ResAnalytics_Box_Score_Summary_*.xlsx",
        "description": "Box score summary report"
    },
    "Work Order Report": {
        "pattern": "Work_Order_Report_*.xlsx", 
        "description": "Work order maintenance report"
    },
    "ResAnalytics Unit Availability Details": {
        "pattern": "ResAnalytics_Unit_Availability_Details_*.xlsx",
        "description": "Unit availability details"
    },
    "ResAnalytics Market Rent Schedule": {
        "pattern": "ResAnalytics_Market_Rent_Schedule_*.xlsx",
        "description": "Market rent pricing schedule"
    },
    "ResAnalytic Lease Expiration": {
        "pattern": "ResAnalytic_Lease_Expiration_*.xlsx",
        "description": "Lease expiration report"
    },
    "ResARAnalytics Delinquency Summary": {
        "pattern": "ResARAnalytics_Delinquency_Summary_*.xlsx",
        "description": "Delinquency and collections report"
    },
    "Pending Make Ready Unit Details": {
        "pattern": "Pending_Make_Ready_Unit_Details._*.xlsx",
        "description": "Make ready unit status"
    },
    "Residents on Notice": {
        "pattern": "Residents_on_Notice_*.xlsx",
        "description": "Residents on notice report"
    },
    "Projected Occupancy": {
        "pattern": "Projected_Occupancy_*.xlsx",
        "description": "6-week occupancy forecast (ETL report)"
    },
    "Budget Comparison": {
        "pattern": "Budget_Comparison_*.xlsx",
        "description": "Budget vs actual comparison"
    },
    "Weekly Report": {
        "pattern": "*Weekly Report*.xlsx",
        "description": "Weekly comprehensive property report (any file containing 'Weekly Report')"
    }
}

def get_upload_properties():
    """Get list of properties available for upload"""
    return sorted(UPLOAD_PROPERTIES)

def get_file_patterns():
    """Get dictionary of required file patterns"""
    return REQUIRED_FILE_PATTERNS

def validate_filename(filename):
    """
    Validate if filename matches any required pattern
    Returns (is_valid, report_type, error_message)
    """
    import fnmatch
    
    for report_type, config in REQUIRED_FILE_PATTERNS.items():
        pattern = config["pattern"]
        if fnmatch.fnmatch(filename, pattern):
            return True, report_type, None
    
    # If no pattern matches, create helpful error message
    pattern_examples = []
    for report_type, config in REQUIRED_FILE_PATTERNS.items():
        pattern_examples.append(f"• {config['pattern']} - {config['description']}")
    
    error_msg = f"Filename '{filename}' doesn't match any required pattern.\n\nAccepted patterns:\n" + "\n".join(pattern_examples)
    
    return False, None, error_msg