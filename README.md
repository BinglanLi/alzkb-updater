# AlzKB Updater MCP

Alzheimer's KnowledgeBase (AlzKB) Updater - An automated tool for integrating Alzheimer's disease data from multiple biomedical databases.

## Overview

**AlzKB Updater MCP** is a Python-based automated tool for integrating Alzheimer's disease data from multiple biomedical databases. It provides a simple, extensible framework for researchers to maintain an up-to-date knowledge base.

### Key Features

- **Automated Data Retrieval**: Fetches data from multiple biomedical databases
- **Data Cleaning & Standardization**: Processes raw data into consistent CSV format
- **CSV Export**: Outputs clean, structured CSV files
- **GitHub Actions Integration**: Automatically updates data on a schedule
- **Extensible Architecture**: Easy to add new data sources
- **Local & Cloud Execution**: Run on any machine with Python or via GitHub Actions

### Current Data Sources

1. **UniProt**: Protein information for Alzheimer's-related proteins (genes, functions, disease associations)
2. **DrugCentral**: Drug information for Alzheimer's treatments (indications, mechanisms, approvals)

### Design Principles

1. **Simplicity**: Easy to understand and modify
2. **Modularity**: Each source is independent
3. **Extensibility**: Simple to add new sources
4. **Automation**: Runs without manual intervention
5. **Transparency**: Clear logs and outputs

## Quick Start

Get started with AlzKB Updater in 5 minutes!

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd AlzKB-updater-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Your First Update

```bash
# Run the demo with limited keywords
python demo.py
```

This will:
- Fetch Alzheimer's-related proteins from UniProt
- Fetch Alzheimer's drugs from DrugCentral
- Clean and standardize the data
- Create integrated CSV files in `data/processed/`

### 3. Check the Results

```bash
# View the summary
cat data/processed/alzkb_summary.txt

# View integrated data
head data/processed/alzkb_integrated.csv
```

### 4. Run Full Update

```bash
# Run with all default keywords
python main.py
```

### 5. Customize Your Update

```bash
# Use custom keywords
python main.py --keywords Alzheimer APOE APP PSEN1 tau

# Use custom output directory
python main.py --output-dir /path/to/my/data
```

## Project Structure

```
AlzKB-updater-mcp/
├── alzkb/                      # Main package
│   ├── __init__.py
│   ├── config.py              # Configuration settings
│   ├── integrator.py          # Main integration logic
│   └── sources/               # Data source implementations
│       ├── __init__.py
│       ├── base.py           # Base class for data sources
│       ├── uniprot.py        # UniProt data source
│       └── drugcentral.py    # DrugCentral data source
├── data/                      # Data directory
│   ├── raw/                  # Raw data from sources
│   └── processed/            # Cleaned and integrated data
├── .github/
│   └── workflows/
│       └── update-alzkb.yml  # GitHub Actions workflow
├── main.py                   # Main entry point
├── demo.py                   # Demo script
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── CONTRIBUTING.md          # Contribution guidelines
└── ARCHITECTURE.md          # Technical architecture documentation
```

## Core Components

### 1. Data Sources (`alzkb/sources/`)

**Base Class** (`base.py`):
- Abstract interface for all data sources
- Implements common workflow: fetch → clean → save
- Handles file I/O and logging

**UniProt Source** (`uniprot.py`):
- Queries UniProt REST API
- Fetches Alzheimer's-related proteins
- Extracts gene names, functions, disease associations

**DrugCentral Source** (`drugcentral.py`):
- Fetches drug information
- Filters for Alzheimer's-related drugs
- Extracts indications and mechanisms

### 2. Integration (`alzkb/integrator.py`)

**AlzKBIntegrator**:
- Coordinates all data sources
- Manages update workflow
- Combines data into unified format
- Generates summary statistics

### 3. Configuration (`alzkb/config.py`)

Customize the following:
- Data source URLs and settings
- Alzheimer's disease keywords
- Output paths and formats
- Enable/disable specific data sources

Example configuration:
```python
ALZHEIMER_KEYWORDS = [
    "Alzheimer",
    "APOE",
    "APP",
    "PSEN1",
    "PSEN2",
    "MAPT"
]

DATA_SOURCES = {
    "uniprot": {
        "enabled": True,
        "url": "https://rest.uniprot.org/uniprotkb/stream"
    }
}
```

### 4. Automation (`.github/workflows/`)

**GitHub Actions Workflow**:
- Runs weekly (Mondays at 00:00 UTC)
- Can be triggered manually
- Auto-commits updated data
- Uploads artifacts

## Data Flow

```
1. Fetch Data
   ├── UniProt API → Raw protein data
   └── DrugCentral → Raw drug data

2. Clean Data
   ├── Standardize column names
   ├── Filter for Alzheimer's relevance
   ├── Remove duplicates
   └── Add metadata

3. Integrate
   ├── Combine all sources
   ├── Add integration timestamps
   └── Generate summary

4. Export
   ├── Save CSV files
   ├── Create summary report
   └── Commit to repository (if automated)
```

## Output Files

After running, check these files:

| File | Description |
|------|-------------|
| `data/processed/alzkb_integrated.csv` | All data combined from all sources |
| `data/processed/uniprot_processed.csv` | Cleaned protein data |
| `data/processed/drugcentral_processed.csv` | Cleaned drug data |
| `data/processed/alzkb_summary.txt` | Summary statistics |
| `data/raw/uniprot_raw.csv` | Raw UniProt data (before cleaning) |
| `data/raw/drugcentral_raw.csv` | Raw DrugCentral data (before cleaning) |

### Integrated CSV Format

The integrated CSV file (`alzkb_integrated.csv`) contains:

**Common columns:**
- `source`: Data source name
- `source_type`: Type of entity (protein, drug, etc.)
- `last_updated`: Timestamp of last update
- `integration_date`: Date of integration

**UniProt-specific columns:**
- `protein_id`: UniProt accession
- `protein_name`: Protein name
- `gene_names`: Associated gene names
- `organism`: Source organism
- `function`: Protein function
- `disease_involvement`: Disease associations

**DrugCentral-specific columns:**
- `drug_id`: Drug identifier
- `drug_name`: Drug name
- `indication`: Medical indication
- `mechanism_of_action`: How the drug works
- `approval_year`: FDA approval year

## Automated Updates with GitHub Actions

The project includes a GitHub Actions workflow that automatically updates the data:

- **Schedule**: Runs weekly on Mondays at 00:00 UTC
- **Manual Trigger**: Can be triggered manually from the Actions tab
- **Auto-commit**: Automatically commits updated data to the repository

### Setting Up Automated Updates

1. Push the repository to GitHub
2. Enable GitHub Actions in your repository settings
3. The workflow will run automatically according to the schedule
4. View results in the "Actions" tab

## Adding New Data Sources

To add a new data source, see the detailed guide in [ARCHITECTURE.md](ARCHITECTURE.md). Quick overview:

1. **Create source class** in `alzkb/sources/newsource.py`:

```python
from alzkb.sources.base import DataSource

class NewSource(DataSource):
    def fetch_data(self):
        # Implement data fetching logic
        pass
    
    def clean_data(self, df):
        # Implement data cleaning logic
        pass
```

2. **Register the source** in `alzkb/integrator.py`:

```python
from alzkb.sources.newsource import NewSource

# In _initialize_sources method:
if DATA_SOURCES["newsource"]["enabled"]:
    self.sources.append(NewSource(self.output_dir, self.keywords))
```

3. **Add configuration** in `alzkb/config.py`:

```python
DATA_SOURCES["newsource"] = {
    "name": "New Source",
    "url": "https://api.example.com",
    "enabled": True
}
```

## Troubleshooting

### Import errors

```bash
# Solution: Make sure you're in the project directory
cd AlzKB-updater-mcp
python main.py
```

### No data fetched

```bash
# Solution: Check your internet connection
# The scripts need to access external APIs
```

### Rate limiting errors

```bash
# Solution: The scripts include delays, but you can:
# - Run with fewer keywords
# - Wait and try again later
```

### API errors

If you encounter API-related errors, the application will log detailed information. Check the console output for:
- Data fetching progress
- Number of records processed
- Specific error messages

## Technical Details

### Prerequisites

- Python 3.10 or higher
- pip package manager
- Internet connection (for API access)

### Dependencies

- **pandas**: Data manipulation
- **requests**: HTTP requests
- **numpy**: Numerical operations
- **python-dateutil**: Date handling
- **tqdm**: Progress bars

### API Rate Limiting

- Built-in delays between requests
- Respects API guidelines
- Handles errors gracefully

## Future Enhancements

Potential additions:

- [ ] More data sources (PubMed, ClinicalTrials.gov, etc.)
- [ ] Data validation and quality checks
- [ ] Relationship extraction between entities
- [ ] Graph database export (Neo4j)
- [ ] Web interface for browsing data
- [ ] Automated testing suite
- [ ] Docker containerization

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on:

- How to report issues
- Adding new data sources
- Code style guidelines
- Pull request process

## Architecture

For detailed technical documentation about the system architecture, design patterns, and implementation details, see [ARCHITECTURE.md](ARCHITECTURE.md).

## References

This project was inspired by:

- [PrimeKG](https://github.com/mims-harvard/PrimeKG) - Precision Medicine Knowledge Graph
- [AlzKB-updates](https://github.com/EpistasisLab/AlzKB-updates) - Alzheimer's Knowledge Base updates

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

## Changelog

### Version 0.1.0 (Initial Release)

- Basic data integration from UniProt and DrugCentral
- CSV export functionality
- GitHub Actions automation
- Local execution support

## License

To be determined.
