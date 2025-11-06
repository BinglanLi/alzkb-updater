"""
Example configuration file for AlzKB Updater

Copy this file to config_local.py and customize as needed.
The application will use config_local.py if it exists, otherwise defaults from config.py
"""

# Custom data directory (optional)
# DATA_DIR = "/path/to/your/data"

# Custom keywords for Alzheimer's disease search
ALZHEIMER_KEYWORDS = [
    "Alzheimer",
    "Alzheimer's disease",
    "APOE",
    "APP",
    "PSEN1",
    "PSEN2",
    "MAPT",
    "amyloid beta",
    "tau protein",
    "neurofibrillary tangles",
    "senile plaques"
]

# Enable/disable specific data sources
DATA_SOURCES = {
    "uniprot": {
        "name": "UniProt",
        "url": "https://rest.uniprot.org/uniprotkb/stream",
        "description": "Universal Protein Resource",
        "enabled": True  # Set to False to disable
    },
    "drugcentral": {
        "name": "DrugCentral",
        "url": "https://unmtid-shinyapps.net/download/",
        "description": "Online drug information resource",
        "enabled": True  # Set to False to disable
    }
}

# API request settings
REQUEST_TIMEOUT = 30  # seconds
REQUEST_DELAY = 1     # seconds between requests (be nice to APIs)

# Data processing settings
REMOVE_DUPLICATES = True
FILL_MISSING_VALUES = True
MISSING_VALUE_FILL = ""

# Output settings
OUTPUT_FORMAT = "csv"
INCLUDE_METADATA = True
INCLUDE_TIMESTAMPS = True
