"""
Main application script for AlzKB updater
Orchestrates data retrieval, integration, and export
"""
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config import UNIPROT_CONFIG, DRUGBANK_CONFIG, OUTPUT_CONFIG, INTEGRATION_CONFIG
from retrievers.uniprot_retriever import UniProtRetriever
from retrievers.drugbank_retriever import DrugBankRetriever
from integrators.data_integrator import AlzKBIntegrator
from integrators.data_exporter import DataExporter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main execution function"""
    logger.info("=" * 60)
    logger.info("Starting AlzKB Update Process")
    logger.info("=" * 60)
    
    try:
        # Step 1: Retrieve UniProt data
        logger.info("\nStep 1: Retrieving UniProt data...")
        uniprot_retriever = UniProtRetriever(UNIPROT_CONFIG)
        uniprot_raw = uniprot_retriever.fetch_data()
        uniprot_clean = uniprot_retriever.clean_data(uniprot_raw)
        uniprot_retriever.save_data(
            uniprot_clean, 
            f"{OUTPUT_CONFIG['raw_data_dir']}/uniprot_raw.csv"
        )
        
        # Step 2: Retrieve DrugBank data
        logger.info("\nStep 2: Retrieving DrugBank data...")
        drugbank_retriever = DrugBankRetriever(DRUGBANK_CONFIG)
        drugbank_raw = drugbank_retriever.fetch_data()
        drugbank_clean = drugbank_retriever.clean_data(drugbank_raw)
        drugbank_retriever.save_data(
            drugbank_clean,
            f"{OUTPUT_CONFIG['raw_data_dir']}/drugbank_raw.csv"
        )
        
        # Step 3: Integrate data
        logger.info("\nStep 3: Integrating data sources...")
        integrator = AlzKBIntegrator(INTEGRATION_CONFIG)
        integrated_data = integrator.integrate_protein_drug_data(
            uniprot_clean, 
            drugbank_clean
        )
        
        # Create knowledge graph edges
        edges_data = integrator.create_knowledge_graph_edges(integrated_data)
        
        # Deduplicate if configured
        if INTEGRATION_CONFIG.get('deduplicate', True):
            integrated_data = integrator.deduplicate_data(integrated_data)
        
        # Add metadata
        integrated_data = integrator.add_metadata(integrated_data)
        
        # Step 4: Export data
        logger.info("\nStep 4: Exporting integrated data...")
        exporter = DataExporter(OUTPUT_CONFIG['processed_data_dir'])
        
        # Export main integrated file
        exporter.export_to_csv(integrated_data, 'alzkb_integrated.csv')
        
        # Export entity-specific files
        exporter.export_entities(integrated_data)
        
        # Export relationships
        exporter.export_relationships(edges_data)
        
        # Create summary report
        exporter.create_summary_report(integrated_data, edges_data)
        
        logger.info("\n" + "=" * 60)
        logger.info("AlzKB Update Complete!")
        logger.info("=" * 60)
        logger.info(f"Output files saved to: {OUTPUT_CONFIG['processed_data_dir']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during AlzKB update: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
