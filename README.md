# AlzKB Updater v2

Comprehensive pipeline for building and updating the Alzheimer's Knowledge Base (AlzKB).

## Overview

AlzKB v2 is a knowledge graph that integrates data from multiple biomedical sources to support Alzheimer's disease research. This repository provides tools to:

1. Retrieve data from various sources (APIs, databases, web)
2. Parse and transform data into standardized formats
3. Populate an OWL ontology using ista
4. Export to graph database formats (Memgraph/Neo4j)

## Features

### Data Sources

#### Core AlzKB Sources
- **AOP-DB**: Adverse Outcome Pathway Database (via MySQL)
- **DisGeNET**: Gene-disease associations (via API)
- **DrugBank**: Drug information (via web authentication)
- **NCBI Gene**: Gene annotations
- **DoRothEA**: Transcription Factor regulatory network (via OmniPath API)
  - TranscriptionFactor nodes
  - TF-gene interactions (transcriptionFactorRegulatesGene)

#### Hetionet Component Sources
The Hetionet knowledge graph is rebuilt from scratch using these component parsers:

| Parser | Data Source | Nodes | Edges |
|--------|-------------|-------|-------|
| Disease Ontology | disease-ontology.org | Disease | - |
| Gene Ontology | geneontology.org | BiologicalProcess, CellularComponent, MolecularFunction | Gene-GO associations |
| Uberon | obophenotype.org | Anatomy | - |
| MeSH | nlm.nih.gov | Symptom | - |
| GWAS Catalog | ebi.ac.uk | - | GaD (Gene-associates-Disease) |
| DrugCentral | drugcentral.org | PharmacologicClass | CtD (Compound-treats-Disease), CpD (Compound-palliates-Disease) |
| BindingDB | bindingdb.org | - | CbG (Compound-binds-Gene) |
| Bgee | bgee.org | - | AeG (Anatomy-expresses-Gene), AuG (Anatomy-underexpresses-Gene) |
| CTD | ctdbase.org | - | CuG (Compound-upregulates-Gene), CdG (Compound-downregulates-Gene) |
| SIDER | sideeffects.embl.de | SideEffect | CcSE (Compound-causes-SideEffect) |
| LINCS L1000 | clue.io | - | CuG, CdG, Gr>G (Gene-regulates-Gene) |
| MEDLINE Cooccurrence | hetio/medline | - | DpS (Disease-presents-Symptom), DlA (Disease-localizes-Anatomy), DrD (Disease-resembles-Disease) |
| Hetionet Precomputed | het.io | - | GcG (Gene-covaries-Gene), GiG (Gene-interacts-Gene) |
| PubTator | ncbi.nlm.nih.gov/research/pubtator | - | Literature-mined associations |

### Node Types

| Node Type | Source(s) |
|-----------|-----------|
| Gene | NCBI Gene |
| Disease | Disease Ontology, DisGeNET |
| Compound/Drug | DrugBank, DrugCentral |
| BiologicalProcess | Gene Ontology |
| CellularComponent | Gene Ontology |
| MolecularFunction | Gene Ontology |
| Anatomy | Uberon |
| Symptom | MeSH |
| SideEffect | SIDER |
| PharmacologicClass | DrugCentral |
| TranscriptionFactor | DoRothEA |

### Edge Types

| Edge Abbreviation | Relationship | Source(s) |
|-------------------|--------------|-----------|
| GaD | Gene-associates-Disease | DisGeNET, GWAS |
| CtD | Compound-treats-Disease | DrugCentral |
| CpD | Compound-palliates-Disease | DrugCentral |
| CbG | Compound-binds-Gene | BindingDB |
| CuG | Compound-upregulates-Gene | CTD, LINCS |
| CdG | Compound-downregulates-Gene | CTD, LINCS |
| CcSE | Compound-causes-SideEffect | SIDER |
| AeG | Anatomy-expresses-Gene | Bgee |
| AuG | Anatomy-underexpresses-Gene | Bgee |
| GcG | Gene-covaries-Gene | Hetionet Precomputed |
| GiG | Gene-interacts-Gene | Hetionet Precomputed |
| Gr>G | Gene-regulates-Gene | LINCS |
| DpS | Disease-presents-Symptom | MEDLINE |
| DlA | Disease-localizes-Anatomy | MEDLINE |
| DrD | Disease-resembles-Disease | MEDLINE |
| TFrG | TranscriptionFactor-regulates-Gene | DoRothEA |

### Key Improvements in v2

- Integrated **ista** for ontology population from tabular data
- Rebuilt Hetionet from scratch with updated data sources
- Added DoRothEA for transcription factor regulatory networks
- Added SIDER for drug side effects
- Added LINCS L1000 for gene expression perturbation data
- Added MEDLINE cooccurrence for literature-mined edges
- Improved error handling and logging
- Modular parser architecture
- Memgraph-compatible CSV export
- Comprehensive release notes generation

## Installation

### Prerequisites

- Python 3.8+
- MySQL (for AOP-DB)
- Git

### Setup

1. **Clone the repository**:
   ```bash
   cd ~/GitHub
   git clone https://github.com/BinglanLi/alzkb-updater.git
   cd alzkb-updater
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install ista**:
   ```bash
   git clone https://github.com/RomanoLab/ista.git .ista
   pip install -e .ista
   ```

5. **Configure environment variables**:
   Create a `.env` file with your credentials:
   ```bash
   # DisGeNET API
   DISGENET_API_KEY=your_api_key_here

   # DrugBank credentials
   DRUGBANK_USERNAME=your_username
   DRUGBANK_PASSWORD=your_password

   # MySQL (for AOP-DB)
   MYSQL_USERNAME=your_mysql_user
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DB_NAME=aopdb
   ```

## Usage

### Running the Complete Pipeline

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the pipeline
python src/main.py
```

### Pipeline Steps

The pipeline executes the following steps:

1. **Data Retrieval**: Downloads/retrieves data from all sources
2. **Data Parsing**: Parses and transforms data into standard formats
3. **TSV Export**: Exports data to TSV files for ista processing
4. **Ontology Population**: Uses ista to populate the ontology
5. **Database Building**: Creates Memgraph-compatible CSV files
6. **Release Notes**: Generates comprehensive release documentation

### Command-Line Options

```bash
python src/main.py [options]

Options:
  --base-dir DIR        Base directory for the project (default: current directory)
  --log-level LEVEL     Set logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                        Default: INFO. Can also be set via ALZKB_LOG_LEVEL environment variable.
```

### Running Individual Components

You can also run individual parsers:

```python
from src.parsers import DisGeNETParser
import os

# Initialize parser
parser = DisGeNETParser(
    data_dir="data/raw/disgenet",
    api_key=os.getenv('DISGENET_API_KEY')
)

# Download and parse
parser.download_data()
data = parser.parse_data()
```

## Project Structure

```
alzkb-updater/
├── src/
│   ├── parsers/                          # Data source parsers
│   │   ├── __init__.py
│   │   ├── base_parser.py                # Base class for all parsers
│   │   ├── aopdb_parser.py               # AOP-DB parser
│   │   ├── disgenet_parser.py            # DisGeNET parser
│   │   ├── drugbank_parser.py            # DrugBank parser
│   │   ├── ncbigene_parser.py            # NCBI Gene parser
│   │   ├── dorothea_parser.py            # DoRothEA TF parser
│   │   └── hetionet_components/          # Hetionet component parsers
│   │       ├── __init__.py
│   │       ├── disease_ontology_parser.py
│   │       ├── gene_ontology_parser.py
│   │       ├── uberon_parser.py
│   │       ├── mesh_parser.py
│   │       ├── gwas_parser.py
│   │       ├── drugcentral_parser.py
│   │       ├── bindingdb_parser.py
│   │       ├── bgee_parser.py
│   │       ├── ctd_parser.py
│   │       ├── sider_parser.py
│   │       ├── lincs_parser.py
│   │       ├── medline_cooccurrence_parser.py
│   │       ├── hetionet_precomputed_parser.py
│   │       └── pubtator_parser.py
│   ├── ontology/                         # Ontology populator
│   │   ├── __init__.py
│   │   └── alzkb_populator.py
│   ├── ontology_configs.py               # ista configuration definitions
│   ├── __init__.py
│   └── main.py                           # Main pipeline
├── data/
│   ├── raw/                              # Raw downloaded data
│   ├── processed/                        # Processed TSV files
│   ├── ontology/                         # Ontology files
│   │   └── alzkb_v2.rdf
│   └── output/                           # Final outputs
├── .env                                  # Environment variables (create this)
├── requirements.txt
└── README.md
```

## Output Files

After running the pipeline, you'll find:

- **RDF Files**: `data/output/alzkb_v2_populated.rdf`
- **CSV Files** (for Memgraph):
  - `data/output/alzkb_nodes.csv`
  - `data/output/alzkb_edges.csv`
- **Release Notes**: `data/output/RELEASE_NOTES_v2.md`
- **Logs**: `alzkb_build.log`

## Data Source Details

### AOP-DB
- **Source**: Local MySQL database
- **Access**: Requires MySQL credentials
- **Content**: Adverse outcome pathways

### DisGeNET
- **Source**: API (https://www.disgenet.org/api)
- **Access**: Requires API key
- **Content**: Gene-disease associations

### DrugBank
- **Source**: Web (https://go.drugbank.com)
- **Access**: Requires username and password
- **Content**: Drug information and interactions

### NCBI Gene
- **Source**: NCBI FTP
- **Access**: Public
- **Content**: Gene annotations

### DoRothEA
- **Source**: OmniPath API (https://omnipathdb.org)
- **Access**: Public
- **Content**: Transcription factor-gene regulatory interactions
- **Confidence Levels**: A (highest), B, C, D, E (lowest)

### Hetionet Components
Each component is downloaded and integrated:
- **Disease Ontology**: Human disease concepts
- **Gene Ontology**: Gene functions (BP, CC, MF)
- **GWAS Catalog**: Genetic associations
- **Bgee**: Gene expression data
- **SIDER**: Drug side effects
- **LINCS L1000**: Gene expression perturbations
- **MEDLINE**: Literature-mined co-occurrences
- **CTD**: Chemical-gene expression interactions
- **DrugCentral**: Drug-disease relationships
- And more...

## Troubleshooting

### Common Issues

1. **ista not found**:
   ```bash
   # Make sure ista is installed in the virtual environment
   pip install -e .ista
   ```

2. **MySQL connection failed**:
   - Verify MySQL is running
   - Check credentials in `.env`
   - Ensure AOP-DB database is imported

3. **API authentication failed**:
   - Verify API keys/credentials in `.env`
   - Check if API services are accessible

4. **Download failures**:
   - Some sources may require manual download
   - Check logs for specific error messages
   - Verify internet connectivity

## Development

### Adding a New Data Source

1. Create a new parser in `src/parsers/`:
   ```python
   from .base_parser import BaseParser

   class NewSourceParser(BaseParser):
       def download_data(self):
           # Implement download logic
           pass

       def parse_data(self):
           # Implement parsing logic
           pass
   ```

2. Add ista configuration in `src/ontology_configs.py`:
   ```python
   ONTOLOGY_CONFIGS = {
       # ... existing configs ...
       'newsource.nodes': {
           'data_type': 'node',
           'node_type': 'NewNodeType',
           'source_file': 'newsource/nodes.tsv',
           'id_column': 'id',
           'label_column': 'name',
       },
   }
   ```

3. Update `src/main.py` to include the new parser in the pipeline

### Testing

Run the pipeline with verbose logging:
```bash
python src/main.py --log-level DEBUG 2>&1 | tee build.log
```

## References

- [AlzKB Original](https://github.com/EpistasisLab/AlzKB)
- [AlzKB Updates](https://github.com/EpistasisLab/AlzKB-updates)
- [ista](https://github.com/RomanoLab/ista)
- [Hetionet](https://het.io/)
- [OmniPath](https://omnipathdb.org/)

## Citation

If you use AlzKB in your research, please cite:

```
[Citation to be added]
```

## License

[License information to be added]

## Contact

For questions or issues:
- Open an issue on GitHub
- Contact: [Contact information]

## Acknowledgments

This project builds upon:
- The original AlzKB by the Epistasis Lab
- ista by the Romano Lab
- Hetionet by the Himmelstein Lab
- OmniPath/DoRothEA for TF regulatory data
- And all the data source providers

---

**Version**: 2
**Last Updated**: 2026-01-26
**Status**: Active Development
