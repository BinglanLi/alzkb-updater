"""
CSV export functionality for AlzKB data.
"""
import pandas as pd
import logging
import os
from typing import Dict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSVExporter:
    """Export integrated data to CSV files."""
    
    def __init__(self, output_dir: str = "data/processed"):
        """
        Initialize the CSV exporter.
        
        Args:
            output_dir: Directory to save CSV files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def export_knowledge_base(self, knowledge_base: Dict[str, pd.DataFrame], 
                             prefix: str = "alzkb") -> Dict[str, str]:
        """
        Export the knowledge base to CSV files.
        
        Args:
            knowledge_base: Dictionary of DataFrames to export
            prefix: Prefix for output filenames
            
        Returns:
            Dictionary mapping source names to output file paths
        """
        logger.info(f"Exporting knowledge base to {self.output_dir}")
        
        timestamp = datetime.now().strftime("%Y%m%d")
        exported_files = {}
        
        for source_name, data in knowledge_base.items():
            if len(data) == 0:
                logger.warning(f"Skipping empty dataset: {source_name}")
                continue
            
            # Create filename
            filename = f"{prefix}_{source_name.lower()}_{timestamp}.csv"
            filepath = os.path.join(self.output_dir, filename)
            
            # Export to CSV
            try:
                data.to_csv(filepath, index=False, encoding='utf-8')
                logger.info(f"Exported {len(data)} records to {filepath}")
                exported_files[source_name] = filepath
            except Exception as e:
                logger.error(f"Failed to export {source_name}: {str(e)}")
        
        return exported_files
    
    def export_summary(self, summary_df: pd.DataFrame, prefix: str = "alzkb"):
        """
        Export summary statistics to CSV.
        
        Args:
            summary_df: DataFrame containing summary statistics
            prefix: Prefix for output filename
        """
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{prefix}_summary_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            summary_df.to_csv(filepath, index=False, encoding='utf-8')
            logger.info(f"Exported summary to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to export summary: {str(e)}")
            return None
    
    def export_metadata(self, metadata: Dict, prefix: str = "alzkb"):
        """
        Export integration metadata to CSV.
        
        Args:
            metadata: Dictionary containing metadata
            prefix: Prefix for output filename
        """
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{prefix}_metadata_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # Convert metadata to DataFrame
            metadata_df = pd.DataFrame([metadata])
            metadata_df.to_csv(filepath, index=False, encoding='utf-8')
            logger.info(f"Exported metadata to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to export metadata: {str(e)}")
            return None
