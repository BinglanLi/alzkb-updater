"""
Configuration file for AlzKB updater
Defines data sources and Alzheimer's-related entities
"""

# Alzheimer's disease related keywords and identifiers
ALZHEIMERS_KEYWORDS = [
    "Alzheimer",
    "Alzheimer's disease",
    "AD",
    "amyloid beta",
    "tau protein",
    "neurodegeneration",
    "dementia"
]

# UniProt configuration
UNIPROT_CONFIG = {
    "base_url": "https://rest.uniprot.org/uniprotkb/search",
    "query": "(alzheimer) OR (amyloid beta) OR (tau protein) AND (reviewed:true)",
    "fields": "accession,id,gene_names,protein_name,organism_name,length,cc_function,cc_disease",
    "format": "tsv",
    "size": 500
}

# DrugBank configuration (using public API)
DRUGBANK_CONFIG = {
    "base_url": "https://go.drugbank.com/releases/latest/downloads/all-drugbank-vocabulary",
    "alzheimer_indication": "Alzheimer"
}

# Output configuration
OUTPUT_CONFIG = {
    "raw_data_dir": "data/raw",
    "processed_data_dir": "data/processed",
    "final_output": "data/processed/alzkb_integrated.csv"
}

# Integration settings
INTEGRATION_CONFIG = {
    "merge_on": ["gene_name", "protein_name"],
    "deduplicate": True
}
