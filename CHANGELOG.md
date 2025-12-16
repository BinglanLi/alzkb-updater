# Changelog

All notable changes to the AlzKB Updater project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2024-01-20

### Added

#### Core Features
- **ista Integration**: Complete integration with ista for ontology population from tabular data
  - New `ista_integrator.py` module with comprehensive API
  - Support for TSV to RDF conversion using csv2rdf
  - Default configurations for all data sources
  - RDF file merging capabilities

- **Improved Hetionet Builder**: Complete rebuild from multiple sources
  - Disease Ontology parser
  - Gene Ontology parser
  - Uberon (Anatomy) parser
  - GWAS Catalog integration
  - DrugCentral support
  - BindingDB integration
  - Bgee gene expression data
  - MEDLINE support (planned)

- **Enhanced Data Parsers**:
  - DisGeNET: Full API support with authentication
  - DrugBank: Web authentication and scraping
  - AOP-DB: MySQL database integration
  - NCBI Gene: Improved data retrieval
  - All parsers now support ista export format

#### Pipeline Improvements
- Complete pipeline orchestration in `main.py`
- Step-by-step execution with progress tracking
- Comprehensive error handling and recovery
- Real-time logging to file and console
- Statistics collection and reporting
- Automatic release notes generation

#### Documentation
- Comprehensive README with installation and usage
- Detailed BUILD_GUIDE with step-by-step instructions
- Troubleshooting section
- API documentation for all modules
- Type hints throughout codebase

#### Database Export
- Memgraph-compatible CSV export
- Node and edge extraction from RDF
- Optimized format for graph database import
- Support for large-scale data

### Changed

- **Parser Architecture**: Refactored to use base class with consistent interface
- **Configuration Management**: Moved to environment variables with python-dotenv
- **Logging**: Enhanced with structured logging and log files
- **Error Handling**: Improved with specific error types and recovery strategies
- **Data Formats**: Standardized TSV format for intermediate data

### Fixed

- MySQL connection handling in AOP-DB parser
- API authentication in DisGeNET parser
- Web scraping in DrugBank parser
- Memory issues with large datasets
- File path handling across platforms

### Dependencies

#### Added
- `python-dotenv>=1.0.0` - Environment variable management
- `beautifulsoup4>=4.12.0` - Web scraping
- `lxml>=4.9.0` - XML parsing
- `rich>=13.0.0` - Enhanced console output
- ista from source (https://github.com/RomanoLab/ista)

#### Updated
- `rdflib>=6.3.0` - RDF handling
- `pandas>=2.0.0` - Data manipulation
- `requests>=2.31.0` - HTTP requests

### Performance

- Optimized data parsing with chunking for large files
- Reduced memory footprint with streaming
- Parallel processing support for multiple sources
- Efficient RDF merging algorithm

### Security

- Credentials now stored in `.env` file
- No hardcoded passwords or API keys
- Secure MySQL connection handling
- HTTPS for all API calls

## [2.0.0] - 2024-11-21

### Added
- Initial implementation of AlzKB v2
- Basic parsers for major data sources
- Ontology management with owlready2
- CSV export functionality
- Integration framework

### Changed
- Migrated from AlzKB v1 architecture
- Updated to Python 3.8+
- New ontology structure

## [1.0.0] - Previous

### Added
- Original AlzKB implementation
- Basic data source integration
- Neo4j database support

---

## Version History

- **2.1.0** (2024-01-20): ista integration and comprehensive improvements
- **2.0.0** (2024-11-21): Major refactoring and modernization
- **1.0.0** (Previous): Original implementation

## Upgrade Guide

### From 2.0.0 to 2.1.0

1. **Install ista**:
   ```bash
   git clone https://github.com/RomanoLab/ista.git .ista
   pip install -e .ista
   ```

2. **Update dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create .env file**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Run new pipeline**:
   ```bash
   python src/main.py --use-ista
   ```

### From 1.0.0 to 2.1.0

This is a major upgrade. Please follow the complete installation guide in BUILD_GUIDE.md.

## Planned Features

### Version 2.2.0 (Planned)

- [ ] MEDLINE full integration
- [ ] Additional Hetionet sources
- [ ] GraphQL API
- [ ] Web interface for querying
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Automated testing suite
- [ ] Performance benchmarks

### Version 3.0.0 (Future)

- [ ] Real-time data updates
- [ ] Machine learning integration
- [ ] Advanced query capabilities
- [ ] Visualization tools
- [ ] Multi-database support
- [ ] Cloud deployment options

## Contributing

We welcome contributions! Please see CONTRIBUTING.md for guidelines.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For questions or issues:
- Check the [BUILD_GUIDE.md](BUILD_GUIDE.md)
- Search [existing issues](https://github.com/BinglanLi/alzkb-updater/issues)
- Open a [new issue](https://github.com/BinglanLi/alzkb-updater/issues/new)

## License

[License information to be added]

## Acknowledgments

- Epistasis Lab for the original AlzKB
- Romano Lab for ista
- Himmelstein Lab for Hetionet
- All data source providers
- Open source community

---

**Maintained by**: Binglan Li and contributors  
**Repository**: https://github.com/BinglanLi/alzkb-updater
