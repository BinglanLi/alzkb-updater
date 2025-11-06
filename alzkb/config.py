"""
Configuration file for AlzKB Updater
"""
import os

# Project paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")

# Data source URLs
DATA_SOURCES = {
    "uniprot": {
        "name": "UniProt",
        "url": "https://rest.uniprot.org/uniprotkb/stream",
        "description": "Universal Protein Resource",
        "enabled": True
    },
    "drugcentral": {
        "name": "DrugCentral",
        "url": "https://unmtid-shinyapps.net/download/",
        "description": "Online drug information resource",
        "enabled": True
    }
}

# Alzheimer's disease related query terms
ALZHEIMER_KEYWORDS = [
    "Alzheimer",
    "APOE",
    "APP",
    "PSEN1",
    "PSEN2",
    "MAPT",
    "amyloid beta",
    "tau protein"
]

# Output settings
OUTPUT_FORMAT = "csv"
INCLUDE_METADATA = True
