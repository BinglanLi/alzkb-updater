# Changelog - AlzKB v2

All notable changes to the AlzKB project for version 2.0.

## [2.0.0] - 2024 - AlzKB v2 Complete Rebuild

### Overview

Complete reimplementation of AlzKB based on the original BUILD.org specifications from the EpistasisLab/AlzKB repository. This version recreates the actual Alzheimer's Knowledge Base with proper ontology support and multiple data sources.

### Added

#### Ontology Infrastructure
- **OntologyManager**: Class for loading and managing OWL ontology
  - Load ontology from RDF file
  - Access classes, properties, and individuals
  - Save populated ontology
  - Print ontology statistics

- **OntologyPopulator**: Class for populating ontology with data
  - Add individuals from DataFrames
  - Add relationships between entities
  - Batch operations for efficiency
  - Statistics tracking

- **Ontology File**: AlzKB v2 OWL ontology (alzkb_v2.rdf)
  - Retrieved from original AlzKB repository
  - Defines classes for biomedical entities
  - Defines object properties for relationships
  - Defines data properties for attributes

#### Data Parsers

- **BaseParser**: Abstract base class for all parsers
  - Common download functionality
  - File extraction (gzip support)
  - TSV/CSV reading utilities
  - Data validation
  - Caching support

- **HetionetParser**: Parser for Hetionet knowledge graph
  - Downloads nodes and edges files
  - Parses multiple entity types
  - Filters for Alzheimer's-related entities
  - Supports 11 node types and 24 edge types

- **NCBIGeneParser**: Parser for NCBI Gene data
  - Downloads human gene information
  - Parses gene annotations
  - Extracts cross-references
  - Filters for Alzheimer's-related genes
  - Optional Bgee expression data support

- **DrugBankParser**: Parser for DrugBank data
  - Handles manually downloaded drug_links.csv
  - Extracts drug identifiers and cross-references
  - Filters for Alzheimer's drugs
  - Supports multiple database cross-references

- **DisGeNETParser**: Parser for DisGeNET data
  - Handles gene-disease associations
  - Parses disease mappings
  - Filters for Alzheimer's disease
  - Extracts association scores

- **AOPDBParser**: Parser for AOP-DB MySQL database
  - Connects to MySQL database
  - Extracts adverse outcome pathways
  - Queries key events, stressors, and genes
  - Handles large database efficiently

#### Pipeline Components

- **Updated main.py**: Complete pipeline orchestration
  - AlzKBBuilder class for managing build process
  - Command-line interface with multiple options
  - Step-by-step pipeline execution
  - Progress logging and error handling
  - Support for partial builds

- **Enhanced CSVExporter**: Improved export functionality
  - Exports data from all sources
  - Creates timestamped files
  - Generates summary reports
  - Maintains data provenance

#### Documentation

- **README_v2.md**: Comprehensive user guide
  - Architecture overview
  - Data source descriptions
  - Installation instructions
  - Usage examples
  - Troubleshooting guide

- **BUILD_GUIDE.md**: Detailed build instructions
  - Step-by-step build process
  - Manual download instructions
  - Verification procedures
  - Troubleshooting common issues
  - Performance optimization tips

- **CHANGELOG.md**: This file
  - Comprehensive change documentation
  - Version history
  - Migration guide

### Changed

#### From v1.0 to v2.0

**Data Sources**:
- **Removed**: UniProt retriever (not in original AlzKB)
- **Removed**: PubChem retriever (not in original AlzKB)
- **Added**: Hetionet (core multi-entity knowledge graph)
- **Added**: NCBI Gene (gene information)
- **Added**: DrugBank (drug information)
- **Added**: DisGeNET (disease-gene associations)
- **Added**: AOP-DB (adverse outcome pathways)

**Architecture**:
- **Before**: Simple retriever-integrator-exporter pattern
- **After**: Ontology-based knowledge graph construction
  - OWL ontology as schema
  - Data parsers map to ontology classes
  - Relationships defined by object properties
  - Proper knowledge engineering approach

**Data Processing**:
- **Before**: Basic data cleaning and CSV export
- **After**: Ontology population and multi-format export
  - Structured using OWL ontology
  - Support for graph database export
  - Maintains semantic relationships
  - Proper entity linking

**Build Process**:
- **Before**: Automated retrieval from APIs
- **After**: Mixed automated and manual process
  - Automated: Hetionet, NCBI Gene
  - Manual: DrugBank, DisGeNET (licensing)
  - Optional: AOP-DB (large MySQL database)

### Dependencies

#### Added
- `owlready2>=0.43` - OWL ontology handling
- `mysql-connector-python>=8.0.33` - MySQL database access
- `rdflib>=6.3.0` - RDF support

#### Retained
- `requests>=2.31.0` - HTTP requests
- `pandas>=2.0.0` - Data manipulation
- `biopython>=1.81` - Biological data
- `numpy>=1.24.0` - Numerical operations
- `tqdm>=4.65.0` - Progress bars
- `python-dateutil>=2.8.2` - Date handling

### Technical Details

#### Ontology Structure

The AlzKB v2 ontology defines:

**Classes** (Entity Types):
- Gene
- Disease
- Drug/Chemical
- Protein
- Pathway
- Anatomy
- Biological Process
- And more...

**Object Properties** (Relationships):
- associates_with
- treats
- targets
- participates_in
- located_in
- And more...

**Data Properties** (Attributes):
- commonName
- geneSymbol
- xrefNCBIGene
- xrefDrugbank
- diseaseId
- And more...

#### Data Flow

```
Raw Data → Parser → DataFrame → Ontology Populator → OWL Ontology → Export
    ↓          ↓          ↓              ↓                  ↓           ↓
  Files    Extract   Structure      Map to           Populated     CSV/Neo4j
          Transform   Clean         Classes          Ontology      /Memgraph
```

#### File Organization

```
data/
├── ontology/
│   └── alzkb_v2.rdf              # Base ontology
├── raw/                           # Downloaded data (gitignored)
│   ├── hetionet/
│   │   ├── hetionet-v1.0-nodes.tsv
│   │   └── hetionet-v1.0-edges.sif
│   ├── ncbigene/
│   │   └── Homo_sapiens.gene_info
│   ├── drugbank/
│   │   └── drug_links.csv
│   ├── disgenet/
│   │   ├── curated_gene_disease_associations.tsv
│   │   └── disease_mappings.tsv
│   └── aopdb/                     # MySQL database
└── processed/                     # Output files
    ├── alzkb_hetionet_nodes_YYYYMMDD.csv
    ├── alzkb_hetionet_edges_YYYYMMDD.csv
    ├── alzkb_ncbigene_genes_YYYYMMDD.csv
    ├── alzkb_drugbank_drugs_YYYYMMDD.csv
    ├── alzkb_disgenet_associations_YYYYMMDD.csv
    └── alzkb_summary_YYYYMMDD.csv
```

### Migration Guide

#### From v1.0 to v2.0

**Breaking Changes**:
1. Complete API change - v1.0 code will not work with v2.0
2. Different data sources - UniProt and PubChem removed
3. Ontology required - must have alzkb_v2.rdf file
4. Manual downloads required for some sources

**Migration Steps**:

1. **Checkout new branch**:
```bash
git checkout alzkb-v2
```

2. **Install new dependencies**:
```bash
pip install -r requirements.txt
```

3. **Download ontology**:
```bash
# Already included in data/ontology/alzkb_v2.rdf
```

4. **Update usage**:
```bash
# Old (v1.0)
python main.py --query "alzheimer"

# New (v2.0)
python main.py --sources hetionet ncbigene
```

5. **Manual downloads**:
- Download DrugBank data (see BUILD_GUIDE.md)
- Download DisGeNET data (see BUILD_GUIDE.md)
- Optional: Set up AOP-DB MySQL database

**Data Compatibility**:
- v1.0 CSV files are not compatible with v2.0
- v2.0 uses different schema and structure
- Recommend rebuilding from scratch

### Known Issues

1. **Manual Downloads Required**:
   - DrugBank requires account approval (may take days)
   - DisGeNET requires account creation
   - Solution: Follow BUILD_GUIDE.md instructions

2. **Large File Sizes**:
   - AOP-DB: 7.2 GB compressed, 3+ GB uncompressed
   - Raw data total: ~10 GB
   - Solution: Ensure sufficient disk space

3. **MySQL Dependency**:
   - AOP-DB requires MySQL Server
   - Solution: AOP-DB is optional, can skip

4. **Data Fetching Errors**:
   - Some sources may be temporarily unavailable
   - Network timeouts possible for large files
   - Solution: Retry or use --no-download with cached data

### Future Enhancements

Planned for future releases:

- [ ] Neo4j graph database export
- [ ] Memgraph database export
- [ ] SPARQL query interface
- [ ] Web-based visualization
- [ ] Automated testing suite
- [ ] Docker containerization
- [ ] Additional data sources
- [ ] Relationship inference
- [ ] Data quality metrics
- [ ] Update scheduling

### Acknowledgments

- **Original AlzKB**: EpistasisLab/AlzKB repository
- **BUILD.org**: Comprehensive build documentation
- **Data Sources**: Hetionet, NCBI, DrugBank, DisGeNET, EPA
- **Tools**: owlready2, pandas, biopython

### References

- Original AlzKB: https://github.com/EpistasisLab/AlzKB
- BUILD.org: https://github.com/EpistasisLab/AlzKB/blob/master/BUILD.org
- Hetionet: https://het.io/
- NCBI Gene: https://www.ncbi.nlm.nih.gov/gene/
- DrugBank: https://go.drugbank.com/
- DisGeNET: https://www.disgenet.org/
- AOP-DB: https://aopdb.epa.gov/

---

## [1.0.0] - Previous Version

### Summary

Initial simplified version with UniProt and PubChem retrievers. Basic CSV export functionality. See PROJECT_SUMMARY.md for details.

### Features

- UniProt protein data retrieval
- PubChem compound data retrieval
- Basic data cleaning and integration
- CSV export
- GitHub Actions automation

### Limitations

- No ontology support
- Limited to 2 data sources
- No graph database export
- Not aligned with original AlzKB specifications
