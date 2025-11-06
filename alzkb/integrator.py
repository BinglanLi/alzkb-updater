"""
Main AlzKB integrator module
"""
import os
import pandas as pd
import logging
from typing import List, Dict
from datetime import datetime

from alzkb.config import DATA_DIR, ALZHEIMER_KEYWORDS, DATA_SOURCES
from alzkb.sources.uniprot import UniProtSource
from alzkb.sources.drugcentral import DrugCentralSource

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AlzKBIntegrator:
    """Main class for integrating Alzheimer's disease data from multiple sources"""
    
    def __init__(self, output_dir: str = None, keywords: List[str] = None):
        """
        Initialize the AlzKB Integrator
        
        Args:
            output_dir: Directory for output files (default: from config)
            keywords: Keywords for Alzheimer's disease search (default: from config)
        """
        self.output_dir = output_dir or DATA_DIR
        self.keywords = keywords or ALZHEIMER_KEYWORDS
        self.sources = []
        self._initialize_sources()
        
    def _initialize_sources(self):
        """Initialize all enabled data sources"""
        logger.info("Initializing data sources...")
        
        if DATA_SOURCES["uniprot"]["enabled"]:
            self.sources.append(UniProtSource(self.output_dir, self.keywords))
            
        if DATA_SOURCES["drugcentral"]["enabled"]:
            self.sources.append(DrugCentralSource(self.output_dir, self.keywords))
            
        logger.info(f"Initialized {len(self.sources)} data sources")
    
    def update_all_sources(self) -> Dict[str, pd.DataFrame]:
        """Update data from all sources"""
        logger.info("Starting data update from all sources...")
        results = {}
        
        for source in self.sources:
            try:
                df = source.update()
                results[source.name] = df
            except Exception as e:
                logger.error(f"Error updating {source.name}: {e}")
                results[source.name] = pd.DataFrame()
        
        logger.info("Completed data update from all sources")
        return results
    
    def integrate_data(self) -> pd.DataFrame:
        """Integrate data from all sources into a unified knowledge base"""
        logger.info("Starting data integration...")
        
        # Update all sources first
        source_data = self.update_all_sources()
        
        if not source_data:
            logger.warning("No data to integrate")
            return pd.DataFrame()
        
        # For now, we'll keep sources separate but could merge on common identifiers
        # Create a unified view with source tracking
        integrated_records = []
        
        for source_name, df in source_data.items():
            if not df.empty:
                # Add integration metadata
                df_copy = df.copy()
                df_copy['integration_date'] = datetime.now().isoformat()
                integrated_records.append(df_copy)
        
        if not integrated_records:
            logger.warning("No records to integrate")
            return pd.DataFrame()
        
        # Combine all data
        integrated_df = pd.concat(integrated_records, ignore_index=True)
        
        # Save integrated data
        output_path = os.path.join(self.output_dir, "processed", "alzkb_integrated.csv")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        integrated_df.to_csv(output_path, index=False)
        
        logger.info(f"Integration complete. Total records: {len(integrated_df)}")
        logger.info(f"Integrated data saved to: {output_path}")
        
        return integrated_df
    
    def generate_summary(self, integrated_df: pd.DataFrame) -> Dict:
        """Generate summary statistics of the integrated data"""
        if integrated_df.empty:
            return {}
        
        summary = {
            'total_records': len(integrated_df),
            'sources': integrated_df['source'].value_counts().to_dict(),
            'source_types': integrated_df['source_type'].value_counts().to_dict(),
            'last_updated': datetime.now().isoformat()
        }
        
        # Save summary
        summary_path = os.path.join(self.output_dir, "processed", "alzkb_summary.txt")
        with open(summary_path, 'w') as f:
            f.write("AlzKB Integration Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total Records: {summary['total_records']}\n")
            f.write(f"Last Updated: {summary['last_updated']}\n\n")
            f.write("Records by Source:\n")
            for source, count in summary['sources'].items():
                f.write(f"  - {source}: {count}\n")
            f.write("\nRecords by Type:\n")
            for source_type, count in summary['source_types'].items():
                f.write(f"  - {source_type}: {count}\n")
        
        logger.info(f"Summary saved to: {summary_path}")
        return summary
