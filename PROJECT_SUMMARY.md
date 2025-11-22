# alzkb-updater Project Summary

## Project Overview

This project provides an automated system for creating and updating the Alzheimer's Knowledge Base (AlzKB) by integrating data from multiple biomedical databases.

## Architecture

### Core Components

1. **Data Retrievers** (`src/retrievers/`)
   - `BaseRetriever`: Abstract base class with rate limiting and error handling
   - `UniProtRetriever`: Retrieves protein data from UniProt
   - `PubChemRetriever`: Retrieves compound data from PubChem

2. **Data Integration** (`src/integrators/`)
   - `DataCleaner`: Standardizes and cleans data
   - `DataIntegrator`: Combines data from multiple sources

3. **Export** (`src/csv_exporter.py`)
   - `CSVExporter`: Exports integrated data to CSV files

4. **Main Application** (`src/main.py`)
   - Command-line interface
   - Orchestrates the entire pipeline

### Data Sources

#### UniProt
- **Purpose**: Protein information and disease associations
- **API**: REST API (https://rest.uniprot.org)
- **Rate Limit**: 2 requests/second
- **Output Schema**:
  - uniprot_id
  - protein_name
  - gene_name
  - organism
  - function
  - subcellular_location
  - disease_association

#### PubChem
- **Purpose**: Chemical compound information
- **API**: PUG REST (https://pubchem.ncbi.nlm.nih.gov/rest/pug)
- **Rate Limit**: 5 requests/second
- **Output Schema**:
  - pubchem_cid
  - compound_name
  - molecular_formula
  - molecular_weight
  - smiles
  - inchi
  - description

## Workflow

```
1. Data Retrieval
   ├── UniProt API → Protein data
   └── PubChem API → Compound data
          ↓
2. Data Cleaning
   ├── Remove duplicates
   ├── Standardize text
   └── Handle missing values
          ↓
3. Data Integration
   ├── Add metadata
   └── Create knowledge base
          ↓
4. CSV Export
   ├── alzkb_uniprot_YYYYMMDD.csv
   ├── alzkb_pubchem_YYYYMMDD.csv
   ├── alzkb_summary_YYYYMMDD.csv
   └── alzkb_metadata_YYYYMMDD.csv
```

## Automation

### GitHub Actions Workflow

**File**: `.github/workflows/update-alzkb.yml`

**Schedule**: Every Monday at 00:00 UTC (configurable)

**Steps**:
1. Checkout repository
2. Set up Python environment
3. Install dependencies
4. Run AlzKB updater
5. Commit and push updated CSV files
6. Create summary report
7. Upload artifacts

**Manual Trigger**: Available via GitHub Actions UI

## Key Features

### Error Handling
- Graceful handling of API failures
- Comprehensive logging
- Rate limiting to respect API guidelines
- Returns empty DataFrames with proper schema on errors

### Extensibility
- Easy to add new data sources
- Modular architecture
- Clear separation of concerns

### Simplicity
- Minimal dependencies
- No complex configuration
- Single command execution
- Clear documentation

## File Structure

```
alzkb-updater/
├── src/
│   ├── retrievers/              # Data source modules
│   │   ├── base_retriever.py    # Abstract base class
│   │   ├── uniprot_retriever.py # UniProt implementation
│   │   └── pubchem_retriever.py # PubChem implementation
│   ├── integrators/             # Data processing
│   │   ├── data_cleaner.py      # Cleaning utilities
│   │   └── data_integrator.py   # Integration logic
│   ├── csv_exporter.py          # CSV export
│   └── main.py                  # Application entry point
├── data/
│   ├── raw/                     # Cached raw data (gitignored)
│   └── processed/               # Final CSV outputs
├── .github/workflows/           # GitHub Actions
├── requirements.txt             # Python dependencies
├── run.sh                       # Linux/Mac runner
├── run.bat                      # Windows runner
├── README.md                    # Full documentation
├── QUICKSTART.md                # Quick start guide
└── .gitignore                   # Git ignore rules

```

## Dependencies

- **requests**: HTTP requests to APIs
- **pandas**: Data manipulation and CSV export
- **biopython**: Biological data handling
- **numpy**: Numerical operations
- **tqdm**: Progress bars
- **python-dateutil**: Date handling

## Usage Examples

### Basic Usage
```bash
./run.sh
```

### Custom Query
```bash
./run.sh --query "beta amyloid" --protein-limit 200
```

### Python Direct
```bash
cd src
python main.py --query "tau protein" --compound-limit 75
```

## Output Files

All files are timestamped (YYYYMMDD format):

1. **alzkb_uniprot_YYYYMMDD.csv**
   - Protein data from UniProt
   - Includes data_source and integration_date columns

2. **alzkb_pubchem_YYYYMMDD.csv**
   - Compound data from PubChem
   - Includes data_source and integration_date columns

3. **alzkb_summary_YYYYMMDD.csv**
   - Summary statistics per source
   - Record counts and data quality metrics

4. **alzkb_metadata_YYYYMMDD.csv**
   - Integration metadata
   - Sources, dates, and record counts

## Design Decisions

1. **Two Data Sources**: UniProt and PubChem chosen for:
   - Reliable APIs
   - Alzheimer's relevance
   - Good documentation
   - Free access

2. **CSV Format**: Simple, portable, easy to analyze

3. **No Test Cases**: Focus on core functionality per requirements

4. **Separate Files**: Each source gets its own CSV for:
   - Easier updates
   - Clear provenance
   - Flexible querying

5. **Error Tolerance**: System continues on failures:
   - Logs errors
   - Returns empty DataFrames
   - Doesn't crash

## Future Extensions

To add more data sources:

1. Create new retriever class inheriting from `BaseRetriever`
2. Implement `retrieve_data()` and `get_schema()`
3. Add to `main.py`
4. Update documentation

Example sources that could be added:
- DrugBank (drug information)
- STRING (protein interactions)
- DisGeNET (disease-gene associations)
- KEGG (pathways)

## References

- **PrimeKG**: https://github.com/mims-harvard/PrimeKG
  - Reference for multi-source biomedical knowledge graphs
  
- **AlzKB-updates**: https://github.com/EpistasisLab/AlzKB-updates
  - Reference for Alzheimer's-specific knowledge base

## Version History

- **v1.0.0** (Current)
  - Initial release
  - UniProt and PubChem integration
  - GitHub Actions automation
  - CSV export functionality
