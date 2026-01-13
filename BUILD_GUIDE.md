# AlzKB Build Guide

## Version 2.3

This guide explains how to build AlzKB from scratch using the updated v2.3 system.

## Overview

AlzKB v2.3 uses ista (Instance Store for Tabular Annotations) to populate the ontology from various data sources. The build process consists of:

1. **Data Fetching**: Download data from source databases
2. **Data Parsing**: Parse and standardize data formats
3. **Ontology Population**: Use ista to populate the AlzKB ontology
4. **Export**: Convert RDF to CSV for Memgraph import

## Prerequisites

### System Requirements
- Python 3.8 or higher
- 20GB+ free disk space
- Internet connection for data downloads
- MySQL server (optional, for AOPDB)

### Python Dependencies
Install required packages:
```bash
pip install -r requirements.txt
```

### ista Installation
ista is included in the repository at `.ista/`. It should be automatically detected and used.

## Quick Start

Build AlzKB with default settings:
```bash
python -m src.main --sources all --output-dir ./output
```

## Detailed Build Process

### 1. Data Source Selection

Choose which data sources to include:

```bash
# Build with specific sources
python -m src.main --sources drugbank disgenet ncbigene hetionet

# Build with all sources
python -m src.main --sources all

# Build with all except specific sources
python -m src.main --sources all --exclude aopdb
```

Available data sources:
- `drugbank`: DrugBank drug information
- `disgenet`: DisGeNET gene-disease associations
- `ncbigene`: NCBI Gene information
- `aopdb`: Adverse Outcome Pathway Database
- `hetionet`: Hetionet biomedical knowledge graph

### 2. Ontology Population with ista

The system automatically uses ista to populate the ontology. The process:

1. **Export to TSV**: Each parser exports data to TSV format
2. **ista Processing**: ista reads TSV and populates ontology
3. **RDF Generation**: ista generates populated RDF file
4. **CSV Conversion**: RDF is converted to CSV for Memgraph

Configuration example:
```python
from src.ontology.alzkb_populator import AlzKBOntologyPopulator

# Initialize populator
populator = AlzKBOntologyPopulator(
    ontology_path="data/ontology/alzkb_v2.rdf",
    data_dir="data/parsed",
    mysql_config=mysql_config  # Optional
)

# Populate nodes
populator.populate_nodes(
    source_name="drugbank",
    node_type="Drug",
    source_filename="drug_links.csv",
    fmt="csv",
    parse_config={
        "iri_column_name": "DrugBank ID",
        "headers": True,
        "data_property_map": {
            "DrugBank ID": "xrefDrugbank",
            "Name": "commonName",
        }
    },
    merge=False,
    skip=False
)

# Save ontology
populator.save_ontology("output/alzkb_populated.rdf")
```

### 3. Hetionet Build

Hetionet is built from scratch using multiple data sources:

```bash
python -m src.main --sources hetionet --rebuild-hetionet
```

This downloads and integrates:
- Disease Ontology
- Gene Ontology
- Uberon (anatomy)
- GWAS Catalog
- MeSH
- DrugCentral
- BindingDB
- Bgee
- MEDLINE co-occurrence

### 4. Output Formats

The build process generates:

1. **RDF File**: `alzkb_v2.3.rdf` - Populated ontology in RDF/XML format
2. **CSV Files**: 
   - `nodes.csv` - All nodes with properties
   - `edges.csv` - All relationships
3. **Statistics**: `build_stats.json` - Build statistics and metadata

### 5. Memgraph Import

Import CSV files into Memgraph:

```cypher
// Import nodes
LOAD CSV FROM "/path/to/nodes.csv" WITH HEADER AS row
CREATE (n)
SET n = row;

// Import edges
LOAD CSV FROM "/path/to/edges.csv" WITH HEADER AS row
MATCH (source {id: row.source})
MATCH (target {id: row.target})
CREATE (source)-[r:RELATES_TO]->(target)
SET r.type = row.type;
```

## Configuration

### Data Directories

Configure data directories in `.env`:
```bash
DATA_DIR=./data
OUTPUT_DIR=./output
ONTOLOGY_PATH=./data/ontology/alzkb_v2.rdf
```

### MySQL Configuration (for AOPDB)

If using AOPDB:
```bash
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=aopdb
```

### API Keys

Some sources require API keys:
```bash
DRUGBANK_USERNAME=your_username
DRUGBANK_PASSWORD=your_password
```

## Troubleshooting

### ista Not Found
If ista is not detected:
```bash
cd .ista
pip install -e .
```

### Memory Issues
For large datasets, increase memory:
```bash
export PYTHONHASHSEED=0
ulimit -s unlimited
```

### Download Failures
If downloads fail, retry with:
```bash
python -m src.main --sources <source> --force-download
```

## Advanced Usage

### Custom Ontology Population

Create custom population scripts:

```python
from src.ontology.alzkb_populator import AlzKBOntologyPopulator

populator = AlzKBOntologyPopulator(
    ontology_path="my_ontology.rdf",
    data_dir="my_data"
)

# Custom node population
populator.populate_nodes(
    source_name="custom_source",
    node_type="CustomType",
    source_filename="custom_data.tsv",
    fmt="tsv",
    parse_config={...}
)
```

### Incremental Updates

Update specific sources without rebuilding:
```bash
python -m src.main --sources drugbank --incremental
```

## Performance Tips

1. **Parallel Processing**: Use `--parallel` flag for multi-core processing
2. **Caching**: Enable caching with `--cache` to avoid re-downloading
3. **Selective Building**: Only build needed sources

## Validation

Validate the built knowledge graph:
```bash
python -m src.validation.validate_kg --input output/alzkb_v2.3.rdf
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/EpistasisLab/AlzKB/issues
- Documentation: https://github.com/EpistasisLab/AlzKB/wiki

## References

- AlzKB: https://github.com/EpistasisLab/AlzKB
- ista: https://github.com/RomanoLab/ista
- Hetionet: https://github.com/hetio/hetionet
