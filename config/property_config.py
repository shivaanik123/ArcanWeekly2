"""
Property configuration and logo mapping
Maps property names to their codes/acronyms and logo files
"""

import os

# Property mapping with display names, codes, and logo filenames
PROPERTY_MAPPING = {
    # Longer Template Properties
    "Manchester at Weslyn": {
        "display_name": "Manchester at Weslyn",
        "property_code": "manwes",
        "logo_file": "Manchester Logo.png",
        "directory_names": ["Manchester", "Manchester at Weslyn", "manwes"]
    },
    "Tapestry Park": {
        "display_name": "Tapestry Park", 
        "property_code": "tapeprk",
        "logo_file": "Tapestry Logo.png",
        "directory_names": ["Tapestry", "Tapestry Park", "tapeprk"]
    },
    "Haven": {
        "display_name": "Haven",
        "property_code": "haven",
        "logo_file": "Haven Logo.jpg",
        "directory_names": ["Haven", "haven"]
    },
    "Hamptons at East Cobb": {
        "display_name": "Hamptons at East Cobb",
        "property_code": "hampec",
        "logo_file": "Hamptons Logo.png",
        "directory_names": ["Hamptons", "Hamptons at East Cobb", "hampec"]
    },
    "Tall Oaks": {
        "display_name": "Tall Oaks",
        "property_code": "talloak", 
        "logo_file": None,  # No logo file available for Tall Oaks
        "directory_names": ["Tall Oaks", "talloak"]
    },
    "Colony Woods": {
        "display_name": "Colony Woods",
        "property_code": "colwds",
        "logo_file": "Colony Woods Logo.png",
        "directory_names": ["Colony Woods", "colwds"]
    },
    "Marsh Point": {
        "display_name": "Marsh Point",
        "property_code": "marshp",
        "logo_file": "Marsh Point.jpg",
        "directory_names": ["Marsh Point", "marshp"]
    },
    "Capella": {
        "display_name": "Capella",
        "property_code": "capella2",
        "logo_file": "Capella Logo.png",
        "directory_names": ["Capella", "capella2"]
    },
    "55 Pharr": {
        "display_name": "55 Pharr",
        "property_code": "55pharr",
        "logo_file": "55Pharr Logo.jpg",
        "directory_names": ["55 Pharr", "55pharr", "55Pharr"]
    },
    "Emerson 1600": {
        "display_name": "Emerson 1600",
        "property_code": "emersn",
        "logo_file": "Emerson Logo.jpg",
        "directory_names": ["Emerson", "Emerson 1600", "emersn"]
    },
    
    # Shorter Template Properties (Arcan owned)
    "Woodland Commons": {
        "display_name": "Woodland Commons",
        "property_code": "wdlndcm",
        "logo_file": "Woodland Commons Logo.png",
        "directory_names": ["Woodland Commons", "wdlndcm"]
    },
    "The Turn": {
        "display_name": "The Turn",
        "property_code": "turn",
        "logo_file": "The Turn Logo.png",
        "directory_names": ["The Turn", "turn"]
    },
    "Portico at Lanier": {
        "display_name": "Portico at Lanier",
        "property_code": "portico",
        "logo_file": "Portico logo.png",
        "directory_names": ["Portico", "Portico at Lanier", "portico"]
    },
    "Georgetown": {
        "display_name": "Georgetown",
        "property_code": "georget",
        "logo_file": "Georgetown Logo.png",
        "directory_names": ["Georgetown", "georget"]
    },
    "Longview": {
        "display_name": "Longview",
        "property_code": "longvw",
        "logo_file": "Longview Logo.png",
        "directory_names": ["Longview", "longvw"]
    },
    "Kensington Place": {
        "display_name": "Kensington Place",
        "property_code": "kenplc",
        "logo_file": "Kensington Logo.jpg",
        "directory_names": ["Kensington", "Kensington Place", "kenplc"]
    },
    "Perry Heights": {
        "display_name": "Perry Heights",
        "property_code": "perryh",
        "logo_file": "Perry Heights Logo.png",
        "directory_names": ["Perry Heights", "perryh"]
    },
    "Abbey Lake": {
        "display_name": "Abbey Lake",
        "property_code": "abbeylk",
        "logo_file": "Abbey Lake Logo.jpg",
        "directory_names": ["Abbey Lake", "abbeylk"]
    },
    "Marbella": {
        "display_name": "Marbella",
        "property_code": "marbla",
        "logo_file": "Marbella Logo.png",
        "directory_names": ["Marbella", "marbla"]
    },
    "The Hangar": {
        "display_name": "The Hangar",
        "property_code": "hangar",
        "logo_file": "Hangar.png",
        "directory_names": ["Hangar", "The Hangar", "hangar"]
    }
}

def get_property_logo_path(property_key: str) -> str:
    """Get CDN URL for property logo."""
    if property_key not in PROPERTY_MAPPING:
        return None
    
    # Get CDN URL from environment variable or use relative path for local development
    CDN_BASE_URL = os.environ.get('CDN_BASE_URL', './logos')
    logo_file = PROPERTY_MAPPING[property_key].get("logo_file")
    
    if logo_file and logo_file is not None:
        return f"{CDN_BASE_URL}/Apartment Logos/{logo_file}"
    return None

def get_arcan_logo_path() -> str:
    """Get CDN URL for Arcan logo."""
    # Get CDN URL from environment variable or use relative path for local development
    CDN_BASE_URL = os.environ.get('CDN_BASE_URL', './logos')
    return f"{CDN_BASE_URL}/arcan-logo.png"

def get_all_properties() -> list:
    """Get list of all available properties."""
    return list(PROPERTY_MAPPING.keys())

def get_property_display_name(property_key: str) -> str:
    """Get the display name for a property."""
    if property_key in PROPERTY_MAPPING:
        return PROPERTY_MAPPING[property_key]["display_name"]
    return property_key

def get_property_code(property_key: str) -> str:
    """Get the property code/acronym for a property."""
    if property_key in PROPERTY_MAPPING:
        return PROPERTY_MAPPING[property_key]["property_code"]
    return property_key

def find_property_by_directory_name(directory_name: str) -> str:
    """Find property key by matching directory name (case insensitive)."""
    directory_lower = directory_name.lower().strip()
    
    for prop_key, prop_info in PROPERTY_MAPPING.items():
        # Check all possible directory names for this property
        for dir_name in prop_info["directory_names"]:
            if dir_name.lower() == directory_lower:
                return prop_key
        
        # Check if directory contains the property code
        if prop_info["property_code"].lower() in directory_lower:
            return prop_key
        
        # Check if directory starts with property name (handles "Marbella 8:11" -> "Marbella")
        prop_name_lower = prop_key.lower()
        if directory_lower.startswith(prop_name_lower + " ") or directory_lower.startswith(prop_name_lower + "/"):
            return prop_key
        
        # Check if any configured directory name is a prefix of the actual directory
        for dir_name in prop_info["directory_names"]:
            dir_name_lower = dir_name.lower()
            if directory_lower.startswith(dir_name_lower + " ") or directory_lower.startswith(dir_name_lower + "/"):
                return prop_key
    
    return directory_name  # Return original if no match found

def find_property_by_code(property_code: str) -> str:
    """Find property key by property code."""
    code_lower = property_code.lower().strip()
    
    for prop_key, prop_info in PROPERTY_MAPPING.items():
        if prop_info["property_code"].lower() == code_lower:
            return prop_key
    
    return property_code  # Return original if no match found

def get_arcan_owned_properties() -> list:
    """Get list of Arcan-owned properties (shorter template)."""
    arcan_properties = [
        "Woodland Commons", "The Turn", "Portico at Lanier", "Georgetown",
        "Longview", "Kensington Place", "Perry Heights", "Abbey Lake", "Marbella"
    ]
    return arcan_properties

def get_managed_properties() -> list:
    """Get list of managed properties (longer template)."""
    managed_properties = [
        "Manchester at Weslyn", "Tapestry Park", "Haven", "Hamptons at East Cobb",
        "Tall Oaks", "Colony Woods", "Marsh Point", "Capella", "55 Pharr", "Emerson 1600"
    ]
    return managed_properties

def is_arcan_owned(property_key: str) -> bool:
    """Check if property is Arcan-owned (shorter template)."""
    return property_key in get_arcan_owned_properties()
