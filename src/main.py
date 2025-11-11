"""
AlzKB Updater - Main application for updating the Alzheimer's Knowledge Base.
"""
import logging
import argparse
from retrievers import UniProtRetriever, PubChemRetriever
from integrators import DataCleaner, DataIntegrator
from csv_exporter import CSVExporter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description='Update the Alzheimer\'s Knowledge Base (AlzKB)'
    )
    parser.add_argument(
        '--query',
        type=str,
        default='alzheimer',
        help='Search query for data retrieval (default: alzheimer)'
    )
    parser.add_argument(
        '--protein-limit',
        type=int,
        default=100,
        help='Maximum number of proteins to retrieve (default: 100)'
    )
    parser.add_argument(
        '--compound-limit',
        type=int,
        default=50,
        help='Maximum number of compounds to retrieve (default: 50)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/processed',
        help='Output directory for CSV files (default: data/processed)'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("AlzKB Updater - Starting data integration")
    logger.info("=" * 60)
    
    # Initialize retrievers
    logger.info("\nStep 1: Initializing data retrievers")
    uniprot = UniProtRetriever()
    pubchem = PubChemRetriever()
    
    # Retrieve data
    logger.info("\nStep 2: Retrieving data from sources")
    logger.info(f"Query: {args.query}")
    
    protein_data = uniprot.retrieve_data(query=args.query, limit=args.protein_limit)
    compound_data = pubchem.retrieve_data(query=args.query, limit=args.compound_limit)
    
    # Clean data
    logger.info("\nStep 3: Cleaning and standardizing data")
    cleaner = DataCleaner()
    
    protein_data_clean = cleaner.standardize_dataframe(protein_data)
    compound_data_clean = cleaner.standardize_dataframe(compound_data)
    
    # Integrate data
    logger.info("\nStep 4: Integrating data sources")
    integrator = DataIntegrator()
    
    integrator.add_source_data("UniProt", protein_data_clean)
    integrator.add_source_data("PubChem", compound_data_clean)
    
    knowledge_base = integrator.create_knowledge_base()
    
    # Create summary statistics
    logger.info("\nStep 5: Generating summary statistics")
    summary = integrator.create_summary_statistics()
    print("\nSummary Statistics:")
    print(summary.to_string(index=False))
    
    # Export to CSV
    logger.info("\nStep 6: Exporting data to CSV files")
    exporter = CSVExporter(output_dir=args.output_dir)
    
    exported_files = exporter.export_knowledge_base(knowledge_base)
    exporter.export_summary(summary)
    exporter.export_metadata(integrator.get_metadata())
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("AlzKB Update Complete!")
    logger.info("=" * 60)
    logger.info(f"\nExported files:")
    for source, filepath in exported_files.items():
        logger.info(f"  - {source}: {filepath}")
    
    logger.info(f"\nTotal records: {sum(integrator.metadata['record_counts'].values())}")
    logger.info(f"Sources: {', '.join(integrator.metadata['sources'])}")


if __name__ == "__main__":
    main()
