# AlzKB v2.3 Implementation Summary

## Overview
This document summarizes the implementation changes in AlzKB v2.3, focusing on the migration to ista-based ontology population and the Hetionet rebuild.

## Architecture Changes

### 1. Ontology Population System

#### Old System (v2.2)
- Mixed approach with both ista and non-ista population methods
- `--no-ista` flag allowed bypassing ista
- Inconsistent data handling across sources
- Separate `OntologyPopulator` and `IstaIntegrator` classes

#### New System (v2.3)
- Unified `AlzKBOntologyPopulator` class
- Mandatory ista usage for all sources
- Consistent TSV/CSV export from all parsers
- Standardized configuration format

### 2. Module Structure

```
src/
├── ontology/
│   ├── alzkb_populator.py      # NEW: Unified ista-based populator
│   ├── rdf_to_csv.py            # NEW: RDF to CSV converter
│   └── ontology_manager.py      # Existing: Ontology management
├── parsers/
│   ├── base_parser.py           # Base parser class
│   ├── drugbank_parser.py       # DrugBank parser
│   ├── disgenet_parser.py       # DisGeNET parser
│   ├── ncbigene_parser.py       # NCBI Gene parser
│   ├── aopdb_parser.py          # AOPDB parser
│   └── hetionet_builder.py      # UPDATED: Hetionet builder
├── integrators/
│   ├── data_integrator.py       # Data integration
│   └── data_cleaner.py          # Data cleaning
├── version_manager.py           # NEW: Version management
├── csv_exporter.py              # CSV export utilities
└── main.py                      # UPDATED: Main entry point
```

### 3. Data Flow

```
┌─────────────────┐
│  Data Sources   │
│  (DrugBank,     │
│   DisGeNET,     │
│   Hetionet...)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Parsers      │
│  (Download &    │
│   Parse Data)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Export to TSV  │
│  (ista format)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ AlzKBOntology   │
│    Populator    │
│  (ista-based)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  RDF Ontology   │
│  (Populated)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ RDF to CSV      │
│   Converter     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  CSV Files      │
│  (Memgraph)     │
└─────────────────┘
```

## Key Components

### AlzKBOntologyPopulator

**Purpose**: Unified interface for ontology population using ista

**Key Methods**:
- `populate_nodes()`: Populate nodes from TSV/CSV data
- `populate_relationships()`: Populate relationships from data
- `save_ontology()`: Save populated ontology to RDF
- `get_ontology_stats()`: Get statistics about populated ontology

**Usage**:
```python
populator = AlzKBOntologyPopulator(
    ontology_path="data/ontology/alzkb_v2.rdf",
    data_dir="data/parsed"
)

populator.populate_nodes(
    source_name="drugbank",
    node_type="Drug",
    source_filename="drugs.tsv",
    fmt="tsv",
    parse_config={...}
)

populator.save_ontology("output/alzkb_populated.rdf")
```

### RDFToCSVConverter

**Purpose**: Convert RDF ontology to Memgraph-compatible CSV

**Key Methods**:
- `load_rdf()`: Load RDF file
- `extract_nodes()`: Extract nodes from RDF graph
- `extract_edges()`: Extract relationships from RDF graph
- `export_to_csv()`: Export to CSV files
- `convert()`: Full conversion pipeline

**Usage**:
```python
converter = RDFToCSVConverter(
    rdf_path="output/alzkb_populated.rdf",
    output_dir="output/csv"
)

nodes_path, edges_path = converter.convert()
```

### HetionetBuilder

**Purpose**: Build Hetionet from scratch using multiple data sources

**Data Sources**:
1. Disease Ontology (DO)
2. Gene Ontology (GO)
3. Uberon (anatomy)
4. GWAS Catalog
5. MeSH
6. DrugCentral
7. BindingDB
8. Bgee
9. MEDLINE co-occurrence

**Key Methods**:
- `download_data()`: Download all data sources
- `parse_data()`: Parse downloaded data
- `populate_ontology()`: Populate ontology using ista
- `export_to_tsv()`: Export to ista-compatible TSV

### VersionManager

**Purpose**: Manage AlzKB version information

**Key Methods**:
- `get_version()`: Get current version
- `bump_major()`: Increment major version
- `bump_minor()`: Increment minor version
- `bump_patch()`: Increment patch version
- `set_version()`: Set specific version

## Configuration Format

### ista Parse Config

All data sources use standardized ista parse configuration:

```python
parse_config = {
    # Node identification
    "iri_column_name": "id_column",
    
    # Data properties mapping
    "data_property_map": {
        "source_column": "ontology_property"
    },
    
    # Filtering
    "filter_column": "type_column",
    "filter_value": "desired_value",
    
    # Data transformations
    "data_transforms": {
        "column": lambda x: transform(x)
    },
    
    # Merging
    "merge_column": {
        "source_column_name": "column",
        "data_property": "property"
    },
    
    # File format
    "headers": True,
    "delimiter": "\t"
}
```

## Testing Strategy

### Unit Tests
- Test each parser independently
- Test ontology population with sample data
- Test RDF to CSV conversion

### Integration Tests
- Test full pipeline with small dataset
- Validate ontology consistency
- Check CSV format compatibility with Memgraph

### Validation
- Verify node and edge counts
- Check property completeness
- Validate cross-references

## Performance Considerations

### Memory Management
- Stream large files instead of loading entirely
- Use pandas chunking for large datasets
- Clear intermediate data after processing

### Optimization
- Parallel processing for independent sources
- Caching of downloaded data
- Incremental updates for large sources

## Error Handling

### Download Failures
- Retry with exponential backoff
- Log failed downloads
- Continue with available sources

### Parsing Errors
- Log problematic records
- Skip invalid data
- Report statistics on skipped records

### Ontology Population Errors
- Validate data before population
- Handle missing references gracefully
- Provide detailed error messages

## Migration Path

### From v2.2 to v2.3

1. **Remove --no-ista usage**
   - Update scripts to remove `--no-ista` flag
   - System now always uses ista

2. **Update custom parsers**
   - Implement `export_to_tsv()` method
   - Use standardized parse config format

3. **Update integration code**
   - Replace `OntologyPopulator` with `AlzKBOntologyPopulator`
   - Update import statements

4. **Update output handling**
   - Expect CSV output instead of direct RDF
   - Update Memgraph import scripts

## Future Enhancements

### Short Term
- Complete Hetionet data source parsers
- Add automated testing
- Improve error recovery

### Long Term
- Implement incremental updates
- Add data quality metrics
- Support multiple ontology formats
- Add visualization tools

## Dependencies

### Core
- owlready2 >= 0.43 (ontology handling)
- rdflib >= 6.3.0 (RDF processing)
- pandas >= 2.0.0 (data manipulation)

### ista
- Installed from source at `.ista/`
- Requires Python 3.8+

### Optional
- mysql-connector-python (for AOPDB)
- beautifulsoup4 (for web scraping)

## Maintenance

### Regular Updates
- Check for new versions of data sources
- Update download URLs as needed
- Validate data formats

### Monitoring
- Track build success rates
- Monitor data quality metrics
- Log performance statistics

## Support

For questions or issues:
- GitHub Issues: https://github.com/EpistasisLab/AlzKB/issues
- Documentation: https://github.com/EpistasisLab/AlzKB/wiki

## References

- ista: https://github.com/RomanoLab/ista
- AlzKB: https://github.com/EpistasisLab/AlzKB
- Hetionet: https://github.com/hetio/hetionet
- Disease Ontology: https://disease-ontology.org/
- Gene Ontology: http://geneontology.org/
