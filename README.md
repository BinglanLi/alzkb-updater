# AlzKB Updater

An automated system for updating the Alzheimer's Knowledge Base (AlzKB) by integrating data from multiple biomedical databases.

## Overview

AlzKB Updater retrieves, cleans, integrates, and exports Alzheimer's disease-related data from:
- **UniProt**: Protein information including disease associations
- **PubChem**: Chemical compound data

The system is designed to run automatically via GitHub Actions or manually on a local machine.

## Features

- 🔄 Automated data retrieval from biomedical databases
- 🧹 Data cleaning and standardization
- 🔗 Multi-source data integration
- 📊 CSV export for easy analysis
- 🤖 GitHub Actions for scheduled updates
- 📝 Comprehensive logging and error handling

## Project Structure

```
AlzKB-updater-mcp/
├── src/
│   ├── retrievers/           # Database-specific data retrievers
│   │   ├── base_retriever.py
│   │   ├── uniprot_retriever.py
│   │   └── pubchem_retriever.py
│   ├── integrators/          # Data cleaning and integration
│   │   ├── data_cleaner.py
│   │   └── data_integrator.py
│   ├── csv_exporter.py       # CSV export functionality
│   └── main.py               # Main application entry point
├── data/
│   ├── raw/                  # Raw data cache (gitignored)
│   └── processed/            # Cleaned and integrated CSV files
├── .github/
│   └── workflows/
│       └── update-alzkb.yml  # GitHub Actions workflow
├── requirements.txt
└── README.md
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd AlzKB-updater-mcp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Local Execution

Run the updater with default settings:
```bash
cd src
python main.py
```

### Command-Line Options

```bash
python main.py --help
```

Available options:
- `--query`: Search query for data retrieval (default: "alzheimer")
- `--protein-limit`: Maximum number of proteins to retrieve (default: 100)
- `--compound-limit`: Maximum number of compounds to retrieve (default: 50)
- `--output-dir`: Output directory for CSV files (default: "data/processed")

Example with custom parameters:
```bash
python main.py --query "alzheimer disease" --protein-limit 200 --compound-limit 100
```

### Automated Updates via GitHub Actions

The system includes a GitHub Actions workflow that automatically updates AlzKB:

- **Schedule**: Runs every Monday at 00:00 UTC
- **Manual trigger**: Can be triggered manually from the Actions tab

The workflow:
1. Retrieves data from UniProt and PubChem
2. Cleans and integrates the data
3. Exports to CSV files
4. Commits and pushes updated data to the repository
5. Creates artifacts for download

## Output Files

The system generates the following CSV files in `data/processed/`:

1. **alzkb_uniprot_YYYYMMDD.csv**: Protein data from UniProt
   - Columns: uniprot_id, protein_name, gene_name, organism, function, subcellular_location, disease_association, data_source, integration_date

2. **alzkb_pubchem_YYYYMMDD.csv**: Compound data from PubChem
   - Columns: pubchem_cid, compound_name, molecular_formula, molecular_weight, smiles, inchi, description, data_source, integration_date

3. **alzkb_summary_YYYYMMDD.csv**: Summary statistics
   - Columns: source, total_records, columns, non_null_records, null_records

4. **alzkb_metadata_YYYYMMDD.csv**: Integration metadata
   - Contains: sources, integration_date, record_counts

## Data Sources

### UniProt
- **URL**: https://www.uniprot.org/
- **API**: UniProt REST API
- **Rate Limit**: 2 requests per second
- **Data**: Protein sequences, functions, disease associations

### PubChem
- **URL**: https://pubchem.ncbi.nlm.nih.gov/
- **API**: PubChem PUG REST
- **Rate Limit**: 5 requests per second
- **Data**: Chemical compounds, molecular properties

## Error Handling

The system is designed to handle errors gracefully:
- Network failures are logged and do not crash the application
- Missing data returns empty DataFrames with proper schema
- Rate limiting is enforced to respect API guidelines
- All errors are logged with detailed messages

## Development

### Adding New Data Sources

1. Create a new retriever in `src/retrievers/`:
```python
from .base_retriever import BaseRetriever

class NewRetriever(BaseRetriever):
    def __init__(self):
        super().__init__(name="NewSource", base_url="https://api.example.com")
    
    def get_schema(self):
        return ["column1", "column2", ...]
    
    def retrieve_data(self, **kwargs):
        # Implementation
        pass
```

2. Update `src/retrievers/__init__.py` to export the new retriever

3. Add the retriever to `src/main.py`:
```python
from retrievers import NewRetriever

new_retriever = NewRetriever()
data = new_retriever.retrieve_data()
integrator.add_source_data("NewSource", data)
```

## Contributing

This project focuses on core functionality:
- Data retrieval from biomedical databases
- Data cleaning and standardization
- Data integration and export

## References

- PrimeKG: https://github.com/mims-harvard/PrimeKG
- AlzKB-updates: https://github.com/EpistasisLab/AlzKB-updates

## Support

For issues or questions:
1. Check the logs in the console output
2. Review error messages for specific API failures
3. Verify network connectivity and API availability
4. Check rate limits are not exceeded

## Version

Current version: 1.0.0
