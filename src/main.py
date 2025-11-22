"""
AlzKB v2 Main Application

This is the main entry point for building the Alzheimer's Knowledge Base (AlzKB) v2.
It orchestrates the entire pipeline:
1. Download/check data from multiple sources
2. Parse and process the data
3. Populate the OWL ontology
4. Export to various formats (CSV, graph database)
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ontology import OntologyManager, OntologyPopulator
from parsers import (
    HetionetParser, NCBIGeneParser, DrugBankParser,
    DisGeNETParser, AOPDBParser
)
from integrators.data_integrator import DataIntegrator
from csv_exporter import CSVExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlzKBBuilder:
    """
    Main class for building AlzKB v2.
    
    Coordinates data retrieval, parsing, ontology population,
    and export operations.
    """
    
    def __init__(self, data_dir: str = None, mysql_config: dict = None):
        """
        Initialize the AlzKB builder.
        
        Args:
            data_dir: Directory for storing data files
            mysql_config: MySQL configuration for AOP-DB
        """
        if data_dir is None:
            current_dir = Path(__file__).parent
            data_dir = current_dir.parent / "data"
        
        self.data_dir = Path(data_dir)
        self.raw_data_dir = self.data_dir / "raw"
        self.processed_data_dir = self.data_dir / "processed"
        self.ontology_dir = self.data_dir / "ontology"
        
        # Create directories
        for d in [self.raw_data_dir, self.processed_data_dir, self.ontology_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        self.mysql_config = mysql_config
        
        # Initialize components
        self.ontology_manager = None
        self.ontology_populator = None
        self.parsers = {}
        
        logger.info(f"Initialized AlzKB Builder")
        logger.info(f"Data directory: {self.data_dir}")
    
    def initialize_ontology(self) -> bool:
        """
        Initialize the ontology manager and load the ontology.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 80)
        logger.info("STEP 1: Initializing Ontology")
        logger.info("=" * 80)
        
        ontology_path = self.ontology_dir / "alzkb_v2.rdf"
        
        if not ontology_path.exists():
            logger.error(f"Ontology file not found: {ontology_path}")
            logger.error("Please ensure alzkb_v2.rdf is in the data/ontology directory")
            return False
        
        self.ontology_manager = OntologyManager(str(ontology_path))
        
        if not self.ontology_manager.load_ontology():
            logger.error("Failed to load ontology")
            return False
        
        self.ontology_manager.print_statistics()
        
        # Initialize populator
        self.ontology_populator = OntologyPopulator(self.ontology_manager)
        
        logger.info("✓ Ontology initialized successfully")
        return True
    
    def initialize_parsers(self) -> dict:
        """
        Initialize all data parsers.
        
        Returns:
            Dictionary of initialized parsers
        """
        logger.info("=" * 80)
        logger.info("STEP 2: Initializing Data Parsers")
        logger.info("=" * 80)
        
        parsers = {}
        
        # Initialize each parser
        try:
            parsers['hetionet'] = HetionetParser(str(self.raw_data_dir))
            logger.info("✓ Initialized Hetionet parser")
        except Exception as e:
            logger.error(f"Failed to initialize Hetionet parser: {e}")
        
        try:
            parsers['ncbigene'] = NCBIGeneParser(str(self.raw_data_dir))
            logger.info("✓ Initialized NCBI Gene parser")
        except Exception as e:
            logger.error(f"Failed to initialize NCBI Gene parser: {e}")
        
        try:
            parsers['drugbank'] = DrugBankParser(str(self.raw_data_dir))
            logger.info("✓ Initialized DrugBank parser")
        except Exception as e:
            logger.error(f"Failed to initialize DrugBank parser: {e}")
        
        try:
            parsers['disgenet'] = DisGeNETParser(str(self.raw_data_dir))
            logger.info("✓ Initialized DisGeNET parser")
        except Exception as e:
            logger.error(f"Failed to initialize DisGeNET parser: {e}")
        
        try:
            if self.mysql_config:
                parsers['aopdb'] = AOPDBParser(str(self.raw_data_dir), self.mysql_config)
                logger.info("✓ Initialized AOP-DB parser")
            else:
                logger.warning("MySQL config not provided, skipping AOP-DB parser")
        except Exception as e:
            logger.error(f"Failed to initialize AOP-DB parser: {e}")
        
        self.parsers = parsers
        logger.info(f"\n✓ Initialized {len(parsers)} parsers")
        return parsers
    
    def download_data(self, sources: list = None) -> dict:
        """
        Download data from specified sources.
        
        Args:
            sources: List of source names to download. If None, downloads all.
        
        Returns:
            Dictionary mapping source names to success status
        """
        logger.info("=" * 80)
        logger.info("STEP 3: Downloading Data")
        logger.info("=" * 80)
        
        if sources is None:
            sources = list(self.parsers.keys())
        
        results = {}
        
        for source in sources:
            if source not in self.parsers:
                logger.warning(f"Parser not found for source: {source}")
                results[source] = False
                continue
            
            logger.info(f"\n--- Downloading {source.upper()} data ---")
            try:
                success = self.parsers[source].download_data()
                results[source] = success
                if success:
                    logger.info(f"✓ {source} download successful")
                else:
                    logger.warning(f"✗ {source} download failed or incomplete")
            except Exception as e:
                logger.error(f"Error downloading {source}: {e}")
                results[source] = False
        
        # Summary
        successful = sum(1 for v in results.values() if v)
        logger.info(f"\n✓ Downloaded data from {successful}/{len(results)} sources")
        
        return results
    
    def parse_data(self, sources: list = None) -> dict:
        """
        Parse data from specified sources.
        
        Args:
            sources: List of source names to parse. If None, parses all.
        
        Returns:
            Dictionary mapping source names to parsed DataFrames
        """
        logger.info("=" * 80)
        logger.info("STEP 4: Parsing Data")
        logger.info("=" * 80)
        
        if sources is None:
            sources = list(self.parsers.keys())
        
        parsed_data = {}
        
        for source in sources:
            if source not in self.parsers:
                logger.warning(f"Parser not found for source: {source}")
                continue
            
            logger.info(f"\n--- Parsing {source.upper()} data ---")
            try:
                data = self.parsers[source].parse_data()
                parsed_data[source] = data
                
                if data:
                    logger.info(f"✓ {source} parsing successful")
                    for entity_type, df in data.items():
                        logger.info(f"  - {entity_type}: {len(df)} records")
                else:
                    logger.warning(f"✗ {source} parsing returned no data")
            except Exception as e:
                logger.error(f"Error parsing {source}: {e}")
                parsed_data[source] = {}
        
        return parsed_data
    
    def export_csv(self, parsed_data: dict) -> bool:
        """
        Export parsed data to CSV files.
        
        Args:
            parsed_data: Dictionary of parsed data from all sources
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 80)
        logger.info("STEP 5: Exporting to CSV")
        logger.info("=" * 80)
        
        timestamp = datetime.now().strftime("%Y%m%d")
        
        try:
            exporter = CSVExporter(str(self.processed_data_dir))
            
            # Export each source's data
            for source, data in parsed_data.items():
                for entity_type, df in data.items():
                    if df is not None and len(df) > 0:
                        filename = f"alzkb_{source}_{entity_type}_{timestamp}.csv"
                        output_path = self.processed_data_dir / filename
                        
                        df.to_csv(output_path, index=False)
                        logger.info(f"✓ Exported {source}/{entity_type} to {filename}")
            
            # Create summary
            self._create_summary(parsed_data, timestamp)
            
            logger.info("\n✓ CSV export completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            return False
    
    def _create_summary(self, parsed_data: dict, timestamp: str):
        """Create a summary CSV of all data sources."""
        import pandas as pd
        
        summary_data = []
        for source, data in parsed_data.items():
            for entity_type, df in data.items():
                if df is not None:
                    summary_data.append({
                        'source': source,
                        'entity_type': entity_type,
                        'record_count': len(df),
                        'columns': ', '.join(df.columns.tolist()[:5]) + '...'
                    })
        
        summary_df = pd.DataFrame(summary_data)
        summary_path = self.processed_data_dir / f"alzkb_summary_{timestamp}.csv"
        summary_df.to_csv(summary_path, index=False)
        logger.info(f"✓ Created summary: {summary_path.name}")
    
    def build(self, download: bool = True, parse: bool = True, 
              export_csv: bool = True, sources: list = None):
        """
        Run the complete AlzKB build pipeline.
        
        Args:
            download: Whether to download data
            parse: Whether to parse data
            export_csv: Whether to export to CSV
            sources: List of sources to process (None = all)
        """
        logger.info("\n" + "=" * 80)
        logger.info("STARTING ALZKB V2 BUILD PIPELINE")
        logger.info("=" * 80 + "\n")
        
        # Step 1: Initialize ontology
        if not self.initialize_ontology():
            logger.error("Failed to initialize ontology. Aborting.")
            return False
        
        # Step 2: Initialize parsers
        self.initialize_parsers()
        
        if not self.parsers:
            logger.error("No parsers initialized. Aborting.")
            return False
        
        # Step 3: Download data
        if download:
            download_results = self.download_data(sources)
        
        # Step 4: Parse data
        if parse:
            parsed_data = self.parse_data(sources)
        else:
            parsed_data = {}
        
        # Step 5: Export to CSV
        if export_csv and parsed_data:
            self.export_csv(parsed_data)
        
        logger.info("\n" + "=" * 80)
        logger.info("ALZKB V2 BUILD PIPELINE COMPLETED")
        logger.info("=" * 80)
        
        return True


def main():
    """Main entry point for AlzKB v2 builder."""
    parser = argparse.ArgumentParser(
        description='Build Alzheimer\'s Knowledge Base (AlzKB) v2',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build with all data sources
  python main.py
  
  # Build with specific sources only
  python main.py --sources hetionet ncbigene
  
  # Skip download step (use cached data)
  python main.py --no-download
  
  # Provide MySQL configuration for AOP-DB
  python main.py --mysql-host localhost --mysql-user root --mysql-password pass --mysql-db aopdb
        """
    )
    
    parser.add_argument(
        '--data-dir',
        type=str,
        help='Directory for data files (default: ../data)'
    )
    
    parser.add_argument(
        '--sources',
        nargs='+',
        choices=['hetionet', 'ncbigene', 'drugbank', 'disgenet', 'aopdb'],
        help='Specific data sources to process (default: all)'
    )
    
    parser.add_argument(
        '--no-download',
        action='store_true',
        help='Skip download step (use cached data)'
    )
    
    parser.add_argument(
        '--no-parse',
        action='store_true',
        help='Skip parsing step'
    )
    
    parser.add_argument(
        '--no-export',
        action='store_true',
        help='Skip CSV export step'
    )
    
    # MySQL configuration
    parser.add_argument('--mysql-host', type=str, help='MySQL host')
    parser.add_argument('--mysql-user', type=str, help='MySQL username')
    parser.add_argument('--mysql-password', type=str, help='MySQL password')
    parser.add_argument('--mysql-db', type=str, default='aopdb', help='MySQL database name')
    
    args = parser.parse_args()
    
    # Build MySQL config if provided
    mysql_config = None
    if args.mysql_host and args.mysql_user:
        mysql_config = {
            'host': args.mysql_host,
            'user': args.mysql_user,
            'password': args.mysql_password or '',
            'database': args.mysql_db
        }
    
    # Initialize builder
    builder = AlzKBBuilder(
        data_dir=args.data_dir,
        mysql_config=mysql_config
    )
    
    # Run build pipeline
    builder.build(
        download=not args.no_download,
        parse=not args.no_parse,
        export_csv=not args.no_export,
        sources=args.sources
    )


if __name__ == '__main__':
    main()
