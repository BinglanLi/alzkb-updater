# AlzKB v2 - Alzheimer's Knowledge Base

A comprehensive knowledge graph for Alzheimer's disease research, integrating data from multiple biomedical databases and structured using an OWL ontology.

## Overview

AlzKB v2 is a complete reimplementation based on the original [AlzKB](https://github.com/EpistasisLab/AlzKB) build process. It creates a knowledge graph by:

1. **Collecting data** from multiple authoritative biomedical databases
2. **Structuring data** using an OWL 2 ontology
3. **Populating** the ontology with entities and relationships
4. **Exporting** to various formats (CSV, graph databases)

## Architecture

### Data Sources

AlzKB v2 integrates data from the following sources:

| Source | Type | Content | Status |
|--------|------|---------|--------|
| **Hetionet** | Flat files | Multi-entity biomedical knowledge graph | ✓ Implemented |
| **NCBI Gene** | Flat files | Human gene information | ✓ Implemented |
| **DrugBank** | Flat files | Drug information and targets | ✓ Implemented |
| **DisGeNET** | Flat files | Disease-gene associations | ✓ Implemented |
| **AOP-DB** | MySQL | Adverse Outcome Pathways | ✓ Implemented |

### Components

```
alzkb-updater/
├── src/
│   ├── ontology/              # OWL ontology management
│   │   ├── ontology_manager.py
│   │   └── ontology_populator.py
│   ├── parsers/               # Data source parsers
│   │   ├── base_parser.py
│   │   ├── hetionet_parser.py
│   │   ├── ncbigene_parser.py
│   │   ├── drugbank_parser.py
│   │   ├── disgenet_parser.py
│   │   └── aopdb_parser.py
│   ├── integrators/           # Data integration
│   ├── csv_exporter.py        # CSV export
│   └── main.py                # Main pipeline
├── data/
│   ├── ontology/              # OWL ontology file
│   │   └── alzkb_v2.rdf
│   ├── raw/                   # Downloaded data (gitignored)
│   └── processed/             # Processed outputs
└── requirements.txt
```

## Installation

### Prerequisites

- Python 3.8 or higher
- MySQL Server (optional, for AOP-DB)
- 10+ GB disk space for data files

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd alzkb-updater
git checkout alzkb-v2
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Install and configure MySQL for AOP-DB:
```bash
# Install MySQL Server
# Import AOP-DB database (see Data Sources section)
```

## Data Sources Setup

### Automated Downloads

The following sources can be downloaded automatically:

- **Hetionet**: Automatically downloaded from GitHub
- **NCBI Gene**: Automatically downloaded from NCBI FTP

### Manual Downloads

The following sources require manual download due to licensing:

#### DrugBank

1. Create free account at https://go.drugbank.com/
2. Navigate to Downloads → Academic Download → External Links
3. Download "All" external drug links (drug_links.csv)
4. Place in `data/raw/drugbank/drug_links.csv`

#### DisGeNET

1. Create free account at https://www.disgenet.org/
2. Navigate to Downloads page
3. Download:
   - `curated_gene_disease_associations.tsv`
   - `disease_mappings.tsv`
4. Place in `data/raw/disgenet/`

#### AOP-DB (Optional)

1. Download from https://gaftp.epa.gov/EPADataCommons/ORD/AOP-DB/
   - File: `AOP-DB_v2.zip` (7.2 GB)
2. Extract and import into MySQL:
```bash
mysql -u username -p aopdb < aopdb_no-orthoscores.sql
```

## Usage

### Basic Usage

Build AlzKB with all available data sources:

```bash
cd src
python main.py
```

### Advanced Usage

#### Build with specific sources only:
```bash
python main.py --sources hetionet ncbigene
```

#### Skip download (use cached data):
```bash
python main.py --no-download
```

#### Include AOP-DB with MySQL configuration:
```bash
python main.py \
  --mysql-host localhost \
  --mysql-user root \
  --mysql-password yourpassword \
  --mysql-db aopdb
```

#### Full pipeline with all options:
```bash
python main.py \
  --sources hetionet ncbigene drugbank disgenet aopdb \
  --mysql-host localhost \
  --mysql-user root \
  --mysql-password pass \
  --data-dir /path/to/data
```

### Command-Line Options

```
--data-dir PATH          Directory for data files
--sources SOURCE [...]   Specific sources to process
--no-download           Skip download step
--no-parse              Skip parsing step
--no-export             Skip CSV export
--mysql-host HOST       MySQL host for AOP-DB
--mysql-user USER       MySQL username
--mysql-password PASS   MySQL password
--mysql-db DATABASE     MySQL database name
```

## Output Files

All output files are timestamped (YYYYMMDD format):

### CSV Files

- `alzkb_hetionet_nodes_YYYYMMDD.csv` - Hetionet entities
- `alzkb_hetionet_edges_YYYYMMDD.csv` - Hetionet relationships
- `alzkb_ncbigene_genes_YYYYMMDD.csv` - Gene information
- `alzkb_drugbank_drugs_YYYYMMDD.csv` - Drug information
- `alzkb_disgenet_associations_YYYYMMDD.csv` - Gene-disease associations
- `alzkb_summary_YYYYMMDD.csv` - Build summary

### Ontology Files

- `data/ontology/alzkb_v2.rdf` - Base ontology
- `data/ontology/alzkb_v2_populated.rdf` - Populated ontology (future)

## Data Schema

### Hetionet

**Nodes:**
- `id`: Unique identifier
- `name`: Entity name
- `kind`: Entity type (Gene, Disease, Compound, etc.)

**Edges:**
- `source`: Source node ID
- `metaedge`: Relationship type
- `target`: Target node ID

### NCBI Gene

- `GeneID`: NCBI Gene ID
- `Symbol`: Gene symbol
- `description`: Gene description
- `type_of_gene`: Gene type
- `chromosome`: Chromosome location
- `dbXrefs`: Cross-references

### DrugBank

- `drugbank_id`: DrugBank identifier
- `drug_name`: Drug name
- `cas_number`: CAS Registry Number
- `pubchem_cid`: PubChem Compound ID
- Additional cross-references

### DisGeNET

- `geneId`: NCBI Gene ID
- `geneSymbol`: Gene symbol
- `diseaseId`: Disease identifier (UMLS CUI)
- `diseaseName`: Disease name
- `score`: Association score
- `source`: Data source

## Development

### Project Structure

The project follows a modular architecture:

- **Parsers**: Each data source has a dedicated parser inheriting from `BaseParser`
- **Ontology**: Manages OWL ontology loading and population
- **Integrators**: Handle data cleaning and integration
- **Exporters**: Export to various formats

### Adding New Data Sources

1. Create a new parser in `src/parsers/`:
```python
from .base_parser import BaseParser

class NewSourceParser(BaseParser):
    def download_data(self):
        # Implementation
        pass
    
    def parse_data(self):
        # Implementation
        pass
    
    def get_schema(self):
        # Implementation
        pass
```

2. Register in `src/parsers/__init__.py`
3. Add to `main.py` initialization

## Ontology

AlzKB v2 uses an OWL 2 ontology (`alzkb_v2.rdf`) that defines:

- **Classes**: Entity types (Gene, Disease, Drug, etc.)
- **Object Properties**: Relationships between entities
- **Data Properties**: Attributes of entities
- **Individuals**: Specific instances

The ontology serves as a schema for the knowledge graph and ensures consistency across data sources.

## Comparison with Original AlzKB

| Feature | Original AlzKB | AlzKB v2 |
|---------|----------------|----------|
| Data Sources | 5+ sources | 5 sources implemented |
| Ontology | OWL 2 | OWL 2 (same) |
| Population Tool | ista | Custom implementation |
| Graph DB | Neo4j | Planned |
| Export Format | Neo4j, CSV | CSV (Neo4j planned) |
| Automation | Manual | Semi-automated |

## Known Limitations

1. **Manual Downloads**: DrugBank and DisGeNET require manual download due to licensing
2. **AOP-DB Size**: 7.2 GB compressed, requires significant disk space
3. **MySQL Requirement**: AOP-DB requires MySQL Server installation
4. **Data Fetching Errors**: Some sources may be temporarily unavailable

## Troubleshooting

### owlready2 not found
```bash
pip install owlready2
```

### MySQL connection errors
- Ensure MySQL Server is running
- Verify credentials and database name
- Check that AOP-DB is properly imported

### Download failures
- Check internet connection
- Verify source URLs are accessible
- Some sources may require VPN or institutional access

## References

- **Original AlzKB**: https://github.com/EpistasisLab/AlzKB
- **BUILD.org**: https://github.com/EpistasisLab/AlzKB/blob/master/BUILD.org
- **Hetionet**: https://het.io/
- **NCBI Gene**: https://www.ncbi.nlm.nih.gov/gene/
- **DrugBank**: https://go.drugbank.com/
- **DisGeNET**: https://www.disgenet.org/
- **AOP-DB**: https://aopdb.epa.gov/

## License

This project follows the licensing requirements of all integrated data sources. Please review individual source licenses before use.

## Citation

If you use AlzKB v2 in your research, please cite:

```
[Citation information to be added]
```

## Contact

For questions or issues, please open an issue on GitHub.
