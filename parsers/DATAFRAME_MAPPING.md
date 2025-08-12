# Real Estate Data Parser - DataFrame Mapping Documentation

This document provides comprehensive mapping from Excel spreadsheet types to their output DataFrame structures, including sample data and usage examples.

## Overview

The parsing system recognizes Excel files based on `word_word` naming patterns and extracts data into structured pandas DataFrames. Each file type has a specific parser that handles its unique format and produces consistent output.

## File Type Patterns

| Pattern | File Example | Parser Type | Description |
|---------|-------------|-------------|-------------|
| `ResAnalytics_Box*` | `ResAnalytics_Box_Score_Summary_marbla.xlsx` | `resanalytics_box_score` | Property occupancy and unit type summary |
| `Work_Order*` | `Work_Order_Report_marbla.xlsx` | `work_order_report` | Active work orders and maintenance requests |
| `ResAnalytics_Unit*` | `ResAnalytics_Unit_Availability_Details_marbla.xlsx` | `resanalytics_unit_availability` | Detailed unit-by-unit availability status |
| `ResAnalytics_Market*` | `ResAnalytics_Market_Rent_Schedule_marbla.xlsx` | `resanalytics_market_rent` | Market rent pricing by property |
| `ResAnalytic_Lease*` | `ResAnalytic_Lease_Expiration_marbla.xlsx` | `resanalytic_lease_expiration` | Lease expiration summary |
| `Budget_Comparison*` | `Budget_Comparison(with_PTD)_marbla_Accrual^AJEs^Modified Accrual.xlsx` | `budget_comparison` | Budget vs actual financial data |
| `Pending_Make*` | `Pending_Make_Ready_Unit_Details._marbla.xlsx` | `pending_make_ready` | Units pending make-ready process |
| `ResARAnalytics_Delinquency*` | `ResARAnalytics_Delinquency_Summary_marbla.xlsx` | `resaranalytics_delinquency` | Delinquency and collections summary |

---

## 1. ResAnalytics Box Score Summary

**Pattern:** `ResAnalytics_Box*`  
**Parser:** `resanalytics_box_score`

### Data Structure
```python
{
    'metadata': {
        'property_name': 'Marbella',
        'property_code': 'marbla', 
        'date_range': '07/28/2025-08/03/2025'
    },
    'data_sections': {
        'availability': DataFrame  # Unit type availability summary
    }
}
```

### Sample DataFrame: `data_sections['availability']`
| Code | Name | Avg. Sq Ft. | Avg. Rent | Units | Occupied No Notice | Vacant Rented | % Occ |
|------|------|-------------|-----------|-------|-------------------|---------------|-------|
| 1117A1 | 1 bed 1 bath | 812 | 1345 | 24 | 21 | 3 | 87.5 |
| 1117B1 | 2 bed 2 bath | 982 | 1575 | 63 | 55 | 8 | 87.3 |

**Use Cases:**
- Occupancy rate analysis
- Unit type performance comparison
- Rent per square foot calculations

---

## 2. Work Order Report

**Pattern:** `Work_Order*`  
**Parser:** `work_order_report`

### Data Structure
```python
{
    'metadata': {
        'property_code': 'marbla',
        'status_filters': ['Call', 'In Progress', 'On Hold', 'Request Reassignment', 'Scheduled', 'Web'],
        'work_order_count': 2
    },
    'work_orders': DataFrame  # Single DataFrame with all work orders
}
```

### Sample DataFrame: `work_orders`
| WO# | Brief Desc | Unit | Caller Name | Caller Phone | Category | Status | Technician Notes |
|-----|------------|------|-------------|--------------|----------|--------|------------------|
| 4614466 | The air conditioner is not wor... | 208 | Angela Stephens | 2147085336 | HVAC | In Progress | AC unit replacement needed |
| 4613652 | There is a slow drip from the ... | 317 | Mackenzie Hyman | 2566330652 | Plumbing | Scheduled | Parts ordered |

**Use Cases:**
- Maintenance backlog tracking
- Category-based work order analysis
- Technician workload distribution

---

## 3. ResAnalytics Unit Availability Details

**Pattern:** `ResAnalytics_Unit*`  
**Parser:** `resanalytics_unit_availability`

### Data Structure
```python
{
    'metadata': {
        'property_name': 'Marbella',
        'property_code': 'marbla',
        'as_of_date': '08/03/2025',
        'showing_pre_leased': True,
        'showing_occupied': True,
        'group_by': 'UnitType',
        'sections_found': ['Marbella (marbla) - Notice Rented', ...],
        'total_units': 32
    },
    'data_sections': {
        'Marbella (marbla) - Notice Rented': DataFrame,
        'Marbella (marbla) - Notice Unrented': DataFrame,
        'Marbella (marbla) - Occupied No Notice': DataFrame,
        'Marbella (marbla) - Vacant Rented Ready': DataFrame,
        'Marbella (marbla) - Vacant Unrented Not Ready': DataFrame,
        'Marbella (marbla) - Vacant Unrented Ready': DataFrame
    }
}
```

### Sample DataFrame: `data_sections['Marbella (marbla) - Vacant Rented Ready']`
| Unit | Resident | Name | Resident Rent | Unit Rent | Status | Days Vacant | Move In | Lease From | Lease To |
|------|----------|------|---------------|-----------|--------|-------------|---------|------------|----------|
| 101 | John Smith | | 1345 | 1345 | Ready | 5 | 08/15/2025 | 08/15/2025 | 08/14/2026 |
| 205 | Jane Doe | | 1575 | 1575 | Ready | 2 | 08/10/2025 | 08/10/2025 | 08/09/2026 |

**Use Cases:**
- Unit-level occupancy tracking
- Lease renewal analysis
- Revenue optimization by unit status

---

## 4. ResAnalytics Market Rent Schedule

**Pattern:** `ResAnalytics_Market*`  
**Parser:** `resanalytics_market_rent`

### Data Structure
```python
{
    'metadata': {
        'property_name': 'Marbella',
        'property_code': 'marbla',
        'as_of_date': '08/03/2025',
        'total_properties': 1
    },
    'market_rent_data': DataFrame  # Single DataFrame with market rent data
}
```

### Sample DataFrame: `market_rent_data`
| Property | Name | Units | Average Unit Type Rent |
|----------|------|-------|------------------------|
| marbla | Marbella | 96 | 1518.75 |

**Use Cases:**
- Market rent analysis
- Portfolio-wide rent comparison
- Rent growth tracking

---

## 5. ResAnalytic Lease Expiration

**Pattern:** `ResAnalytic_Lease*`  
**Parser:** `resanalytic_lease_expiration`

### Data Structure
```python
{
    'metadata': {
        'property_name': 'Marbella',
        'property_code': 'marbla',
        'month_year': '08/2025',
        'total_properties': 1,
        'total_units': 96,
        'total_mtm': 1
    },
    'lease_expiration_data': DataFrame  # Single DataFrame with lease expiration data
}
```

### Sample DataFrame: `lease_expiration_data`
| Property | Address | Units | MTM |
|----------|---------|-------|-----|
| marbla | Marbella (marbla) | 96 | 1 |

**Use Cases:**
- Lease renewal planning
- Revenue retention analysis
- Month-to-month tracking

---

## 6. Budget Comparison

**Pattern:** `Budget_Comparison*`  
**Parser:** `budget_comparison`

### Data Structure
```python
{
    'metadata': {
        'property_name': 'Marbella',
        'property_code': 'marbla',
        'report_type': 'BudCompPTD',
        'period': 'Aug 2025',
        'books': ['Accrual', 'Modified Accrual', 'AJEs'],
        'tree': 'arcan_isdet',
        'budget_line_items': 150
    },
    'budget_data': DataFrame  # Single DataFrame with budget vs actual data
}
```

### Sample DataFrame: `budget_data`
| Column_0 | Column_1 | MTD Actual | MTD Budget | MTD Variance | YTD Actual | YTD Budget |
|----------|----------|------------|------------|--------------|------------|------------|
| 40000 | INCOME | 0 | 0 | 0 | 125000 | 120000 |
| 40010 | Rental Income | 95000 | 92000 | 3000 | 850000 | 820000 |
| 50000 | EXPENSES | 0 | 0 | 0 | 65000 | 68000 |

**Use Cases:**
- Budget variance analysis
- Financial performance tracking
- Expense category monitoring

---

## 7. Pending Make Ready Unit Details

**Pattern:** `Pending_Make*`  
**Parser:** `pending_make_ready`

### Data Structure
```python
{
    'metadata': {
        'property_code': 'marbla',
        'till_date': '08/04/2025',
        'pending_units': 12,
        'bedroom_breakdown': {2: 8, 1: 4}
    },
    'make_ready_data': DataFrame  # Single DataFrame with pending make-ready units
}
```

### Sample DataFrame: `make_ready_data`
| Property Code | Date Ready | Unit Code | Bedrooms |
|---------------|------------|-----------|----------|
| marbla | 2025-07-25 | 211 | 2 |
| marbla | 2025-08-07 | 213 | 1 |
| marbla | 2025-08-10 | 105 | 2 |

**Use Cases:**
- Make-ready workflow management
- Unit turnover tracking
- Maintenance scheduling

---

## 8. ResARAnalytics Delinquency Summary

**Pattern:** `ResARAnalytics_Delinquency*`  
**Parser:** `resaranalytics_delinquency`

### Data Structure
```python
{
    'metadata': {
        'report_title': 'Delinquency',
        'as_of_date': '8/4/2025',
        'account_scope': 'All Selected Accounts',
        'property_count': 2,
        'total_charges': 79794.13,
        'user_id': 'oibre_live',
        'report_date': '8/4/2025',
        'report_time': '5:03 AM'
    },
    'delinquency_data': DataFrame  # Single DataFrame with delinquency summary
}
```

### Sample DataFrame: `delinquency_data`
| Property Unit | Total Charges | Future Charges | 0-30 Owed | 31-60 Owed | 61-90 Owed |
|---------------|---------------|----------------|-----------|-----------|-----------|
| Total marbla - Marbella | 79794.13 | 0 | 76308.35 | 2500.00 | 985.78 |

**Use Cases:**
- Collections management
- Delinquency trend analysis
- Financial risk assessment

---

## Usage Examples

### Basic File Parsing
```python
from parsers.file_parser import parse_file

# Parse a single file
result = parse_file('path/to/ResAnalytics_Box_Score_Summary_marbla.xlsx')
print(f"Parser type: {result['parser_type']}")
print(f"Metadata: {result['metadata']}")

# Access dataframes
if 'data_sections' in result:
    for section_name, df in result['data_sections'].items():
        print(f"{section_name}: {df.shape}")
```

### Directory Parsing
```python
from parsers.file_parser import parse_directory

# Parse all files in a directory
results = parse_directory('data/08_04_2025/Marbella/', property_filter='marbla')
print(f"Successfully parsed: {results['summary']['files_successfully_parsed']}")
print(f"File types found: {results['summary']['file_types_found']}")
```

### Dashboard Integration
```python
import streamlit as st
from parsers.file_parser import parse_file

# Example Streamlit usage
uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx'])
if uploaded_file:
    result = parse_file(uploaded_file)
    
    # Display metadata
    st.json(result['metadata'])
    
    # Display dataframes based on parser type
    if result['parser_type'] == 'work_order_report':
        st.dataframe(result['work_orders'])
    elif 'data_sections' in result:
        for section_name, df in result['data_sections'].items():
            st.subheader(section_name)
            st.dataframe(df)
```

## File Naming Convention

All files follow the pattern: `{ReportType}_{Property}_{Additional}.xlsx`

- **ReportType**: Matches one of the patterns above (e.g., `ResAnalytics_Box`)
- **Property**: Property identifier (e.g., `marbla`)
- **Additional**: Optional additional identifiers or dates

The parser automatically identifies file types using regex pattern matching and routes to the appropriate specialized parser.
