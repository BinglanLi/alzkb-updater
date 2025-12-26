# AlzKB Updater v2.2 - Parser Fixes

**Release Date:** 2025-12-26

## Overview
This release focuses on fixing parser errors and improving data source integration in the alzkb-updater repository. All fixes ensure compatibility with current data source APIs and formats.

## Bug Fixes

### Import Errors
- **Fixed:** Import error in `src/main.py` - HetionetBuilder now properly exported from parsers module
  - Added HetionetBuilder to `src/parsers/__init__.py` exports
  - Enables proper instantiation of HetionetBuilder class

### SQL Errors
- **Fixed:** SQL table name detection in `parsers/aopdb_parser.py`
  - Implemented dynamic table name detection with `_get_table_names()` method
  - Added table name mappings to handle schema variations (e.g., 'aop' vs 'aop_info')
  - Improved error handling for missing tables
  - Supports multiple table naming conventions across AOP-DB versions

### API Errors
- **Fixed:** DisGeNET API query in `parsers/disgenet_parser.py`
  - Changed from free text query 'alzheimer' to valid disease ID 'C0002395'
  - Added `_get_disease_associations_by_id()` method for direct ID-based queries
  - Uses UMLS CUI (C0002395) as the standard identifier for Alzheimer's Disease
  - Improves API response reliability and accuracy

### Client Errors
- **Fixed:** DrugBank login URL in `parsers/drugbank_parser.py`
  - Updated from `https://go.drugbank.com/login`
  - Updated to `https://go.drugbank.com/public_users/log_in`
  - Ensures successful authentication for data downloads

- **Fixed:** MeSH download URL in `parsers/hetionet_builder.py`
  - Changed from FTP: `ftp://nlmpubs.nlm.nih.gov/online/mesh/.asciimesh/d2024.bin`
  - Changed to HTTPS: `https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2025.xml`
  - Updated format from 'bin' to 'xml' for proper parsing
  - Uses current production year dynamically

- **Fixed:** DrugCentral download URL in `parsers/hetionet_builder.py`
  - Corrected domain from `unmtid-shinyapps.net` to `unmtid-dbs.net`
  - Updated URL format: `https://unmtid-dbs.net/download/drugcentral.dump.01012025.sql.gz`
  - Added note to check for latest version at https://unmtid-dbs.net/download/

### Integration Errors
- **Fixed:** MeSH symptoms integration in `parsers/hetionet_builder.py`
  - Added `_parse_mesh()` method to extract symptoms from MeSH XML
  - Filters for symptom nodes using MeSH tree number C23 (Pathological Conditions, Signs and Symptoms)
  - Extracts mesh_id, symptom_name, and definition from XML structure
  - Integrated into main parsing pipeline

- **Fixed:** MEDLINE cooccurrence edges integration in `parsers/hetionet_builder.py`
  - Added `_parse_medline_cooccurrence()` method for literature-based relationships
  - Implements fallback to download pre-computed cooccurrence data from Hetionet
  - Provides instructions for full MEDLINE processing using PubTator
  - Supports loading pre-computed cooccurrence files
  - Integrated into main parsing pipeline

## Technical Details

### Files Modified
- `src/parsers/__init__.py` - Added HetionetBuilder export
- `src/parsers/aopdb_parser.py` - Dynamic table name detection
- `src/parsers/disgenet_parser.py` - Disease ID-based API queries
- `src/parsers/drugbank_parser.py` - Corrected login URL
- `src/parsers/hetionet_builder.py` - Multiple fixes:
  - MeSH URL and format
  - DrugCentral URL and domain
  - MeSH symptoms parser
  - MEDLINE cooccurrence parser

### Data Sources Updated
- **MeSH:** Now uses HTTPS XML endpoint with current year
- **DrugCentral:** Corrected domain and URL format
- **DisGeNET:** Uses UMLS CUI for reliable API queries
- **DrugBank:** Updated authentication endpoint
- **AOP-DB:** Flexible table name handling

## Testing
All fixes have been validated:
- ✓ Import statements verified
- ✓ SQL query logic confirmed
- ✓ API endpoint URLs tested
- ✓ Integration methods implemented
- ✓ Code syntax validated

## Installation & Usage

### Prerequisites
```bash
# Install required packages
pip install mysql-connector-python  # For AOP-DB
pip install requests beautifulsoup4 lxml  # For web scraping
pip install pandas numpy  # For data processing
```

### Environment Setup
Create a `.env` file with credentials:
```
# DisGeNET API
DISGENET_API_KEY=your_api_key

# DrugBank
DRUGBANK_USERNAME=your_username
DRUGBANK_PASSWORD=your_password

# AOP-DB MySQL
AOPDB_HOST=localhost
AOPDB_USER=root
AOPDB_PASSWORD=your_password
AOPDB_DATABASE=aopdb
```

### Running Parsers
```python
from parsers import HetionetBuilder, DisGeNETParser, DrugBankParser, AOPDBParser

# Initialize parsers
hetionet = HetionetBuilder(data_dir='data/hetionet')
disgenet = DisGeNETParser(data_dir='data/disgenet', api_key='your_key')
drugbank = DrugBankParser(data_dir='data/drugbank', username='user', password='pass')
aopdb = AOPDBParser(data_dir='data/aopdb', mysql_config={'host': 'localhost', ...})

# Download and parse data
hetionet.download_data()
parsed_data = hetionet.parse_data()
```

## Known Limitations
- **AOP-DB:** Requires manual database download and MySQL import (7.2 GB compressed)
- **MEDLINE:** Full processing requires significant computational resources; fallback uses pre-computed data
- **DrugBank:** Requires account registration and credentials
- **DisGeNET:** API key needed for full access

## Migration Notes
If upgrading from previous versions:
1. Update `.env` file with any new credentials
2. Check data source URLs are current
3. Re-download data sources that had URL changes (MeSH, DrugCentral)
4. Test parsers individually before full integration

## Contributors
- Parser fixes and validation
- URL updates for 2025 data sources
- Integration enhancements

## References
- [AlzKB Repository](https://github.com/EpistasisLab/AlzKB)
- [Hetionet Repository](https://github.com/hetio/hetionet)
- [DisGeNET API Documentation](https://www.disgenet.org/api/)
- [DrugBank Downloads](https://go.drugbank.com/releases/latest)
- [MeSH Downloads](https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/)
- [DrugCentral Downloads](https://unmtid-dbs.net/download/)
- [AOP-DB Downloads](https://gaftp.epa.gov/EPADataCommons/ORD/AOP-DB/)

---

For issues or questions, please open an issue on the [GitHub repository](https://github.com/BinglanLi/alzkb-updater/issues).
