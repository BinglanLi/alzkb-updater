# AlzKB v2.3 Release Notes

## Release Date
TBD

## Overview
Version 2.3 represents a major refactoring of the AlzKB ontology population system to properly use ista (Instance Store for Tabular Annotations) for all data sources. This release eliminates the `--no-ista` option and ensures consistent, standardized ontology population across all data sources.

## Major Changes

### 1. Unified ista-based Ontology Population
- **New**: `AlzKBOntologyPopulator` class provides a unified interface for ontology population using ista
- **Removed**: `--no-ista` and `--use-ista` command-line arguments
- **Changed**: All data sources now use ista for ontology population
- **Benefit**: Consistent, standardized approach to ontology population with better data quality

### 2. Hetionet Rebuild from Scratch
- **New**: Complete Hetionet builder that fetches and integrates data from multiple sources:
  - Disease Ontology (DO)
  - Gene Ontology (GO)
  - Uberon (anatomy ontology)
  - GWAS Catalog
  - MeSH (Medical Subject Headings)
  - DrugCentral
  - BindingDB
  - Bgee (gene expression)
  - MEDLINE co-occurrence
- **Changed**: Hetionet is now built dynamically instead of using pre-built version
- **Benefit**: Always up-to-date with latest data from source databases

### 3. RDF to CSV Conversion
- **New**: `RDFToCSVConverter` class for converting populated RDF ontology to Memgraph-compatible CSV
- **Changed**: Output format is now CSV for direct import into Memgraph graph database
- **Benefit**: Seamless integration with Memgraph for graph queries and analysis

### 4. Dynamic Version Management
- **New**: `VersionManager` class for managing AlzKB versions dynamically
- **New**: `VERSION` file in project root
- **Benefit**: Automated version tracking and release management

## Technical Improvements

### Code Organization
- Consolidated ontology population logic in `src/ontology/alzkb_populator.py`
- Removed obsolete `ontology_populator.py` (non-ista version)
- Improved separation of concerns between parsing and ontology population

### Data Source Integration
- All parsers now export data in ista-compatible formats (TSV/CSV)
- Standardized configuration format across all data sources
- Better error handling and logging

### Documentation
- Updated BUILD_GUIDE.md with new ontology population workflow
- Updated README.md with v2.3 features
- Created comprehensive release notes

## Breaking Changes

### Removed Features
- `--no-ista` command-line argument (ista is now always used)
- `--use-ista` command-line argument (redundant)
- Old `OntologyPopulator` class (replaced by `AlzKBOntologyPopulator`)

### Modified Behavior
- Hetionet is now built from scratch instead of downloaded pre-built
- All data sources must export to TSV/CSV for ista processing
- Ontology output is now converted to CSV for Memgraph

## Migration Guide

### For Users
If you were using `--no-ista` flag:
- Remove this flag from your commands
- The system will automatically use ista for all ontology population

### For Developers
If you were extending the old ontology population system:
- Update to use `AlzKBOntologyPopulator` instead of `OntologyPopulator`
- Ensure your parsers export data in TSV/CSV format
- Use the `populate_nodes()` and `populate_relationships()` methods

## Known Issues
- Some Hetionet data source parsers are still in development (OBO parsing, MeSH XML)
- MEDLINE co-occurrence requires additional implementation
- DrugCentral SQL dump parsing needs completion

## Future Plans
- Complete all Hetionet data source parsers
- Add automated testing for ontology population
- Implement incremental updates for large data sources
- Add data quality validation checks

## Dependencies
- ista (installed from source at .ista/)
- owlready2 >= 0.43
- rdflib >= 6.3.0
- pandas >= 2.0.0
- All other dependencies remain unchanged

## Contributors
- Development team

## References
- ista: https://github.com/RomanoLab/ista
- AlzKB: https://github.com/EpistasisLab/AlzKB
- Hetionet: https://github.com/hetio/hetionet
