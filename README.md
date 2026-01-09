# AlzKB Updater v2.1

Comprehensive pipeline for building and updating the Alzheimer's Knowledge Base (AlzKB).

## Overview

AlzKB v2.1 is a knowledge graph that integrates data from multiple biomedical sources to support Alzheimer's disease research. This repository provides tools to:

1. Retrieve data from various sources (APIs, databases, web)
2. Parse and transform data into standardized formats
3. Populate an OWL ontology using ista
4. Export to graph database formats (Memgraph/Neo4j)

## Features

### Data Sources

- **AOP-DB**: Adverse Outcome Pathway Database (via MySQL)
- **DisGeNET**: Gene-disease associations (via API)
- **DrugBank**: Drug information (via web authentication)
- **NCBI Gene**: Gene annotations
- **Hetionet**: Integrated biomedical knowledge graph built from:
  - Disease Ontology
  - Gene Ontology
  - Uberon (Anatomy Ontology)
  - GWAS Catalog
  - MeSH
  - DrugCentral
  - BindingDB
  - Bgee (Gene Expression)
  - MEDLINE (planned)

### Key Improvements in v2.1

- ✅ Integrated **ista** for ontology population from tabular data
- ✅ Rebuilt Hetionet from scratch with updated data sources
- ✅ Improved error handling and logging
- ✅ Modular parser architecture
- ✅ Memgraph-compatible CSV export
- ✅ Comprehensive release notes generation

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
python src/main.py --use-ista
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
  --base-dir DIR      Base directory for the project (default: current directory)
  --use-ista          Use ista for ontology population (default: True)
  --no-ista           Use traditional ontology population method
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
│   ├── parsers/              # Data source parsers
│   │   ├── aopdb_parser.py
│   │   ├── disgenet_parser.py
│   │   ├── drugbank_parser.py
│   │   ├── ncbigene_parser.py
│   │   ├── hetionet_builder.py
│   │   └── base_parser.py
│   ├── ontology/             # Ontology management
│   │   ├── ontology_manager.py
│   │   ├── ontology_populator.py
│   │   └── ista_integrator.py
│   ├── integrators/          # Data integration
│   │   ├── data_integrator.py
│   │   └── data_cleaner.py
│   ├── csv_exporter.py       # Database export
│   └── main.py               # Main pipeline
├── data/
│   ├── raw/                  # Raw downloaded data
│   ├── processed/            # Processed TSV files
│   ├── ontology/             # Ontology files
│   │   └── alzkb_v2.rdf
│   └── output/               # Final outputs
├── .env                      # Environment variables (create this)
├── requirements.txt
└── README.md
```

## Output Files

After running the pipeline, you'll find:

- **RDF Files**: `data/output/alzkb_v2.1_populated.rdf`
- **CSV Files** (for Memgraph):
  - `data/output/alzkb_nodes.csv`
  - `data/output/alzkb_edges.csv`
- **Release Notes**: `data/output/RELEASE_NOTES_v2.1.md`
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

### Hetionet Components
Each component is downloaded and integrated:
- **Disease Ontology**: Human disease concepts
- **Gene Ontology**: Gene functions
- **GWAS Catalog**: Genetic associations
- **Bgee**: Gene expression data
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

2. Add ista configuration in `src/ontology/ista_integrator.py`

3. Update `src/main.py` to include the new parser

### Testing

Run the pipeline with verbose logging:
```bash
python src/main.py --use-ista 2>&1 | tee build.log
```

## References

- [AlzKB Original](https://github.com/EpistasisLab/AlzKB)
- [AlzKB Updates](https://github.com/EpistasisLab/AlzKB-updates)
- [ista](https://github.com/RomanoLab/ista)
- [Hetionet](https://het.io/)

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
- And all the data source providers

---

**Version**: 2.1  
**Last Updated**: 2024-01-20  
**Status**: Active Development
