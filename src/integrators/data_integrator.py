"""
Data integration module for combining data from multiple sources.
"""
import pandas as pd
import logging
from typing import Dict, List
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataIntegrator:
    """Integrate data from multiple biomedical databases."""
    
    def __init__(self):
        self.integrated_data = {}
        self.metadata = {
            "sources": [],
            "integration_date": None,
            "record_counts": {}
        }
    
    def add_source_data(self, source_name: str, data: pd.DataFrame):
        """
        Add data from a source to the integration.
        
        Args:
            source_name: Name of the data source
            data: DataFrame containing the source data
        """
        logger.info(f"Adding data from {source_name}: {len(data)} records")
        
        self.integrated_data[source_name] = data
        self.metadata["sources"].append(source_name)
        self.metadata["record_counts"][source_name] = len(data)
    
    def create_knowledge_base(self) -> Dict[str, pd.DataFrame]:
        """
        Create the integrated knowledge base.
        
        Returns:
            Dictionary of DataFrames, one per source
        """
        logger.info("Creating integrated knowledge base")
        
        self.metadata["integration_date"] = datetime.now().isoformat()
        
        # For AlzKB, we keep separate tables for different entity types
        # This allows for easier querying and updates
        
        knowledge_base = {}
        
        for source_name, data in self.integrated_data.items():
            if len(data) > 0:
                # Add source metadata column
                data_with_source = data.copy()
                data_with_source["data_source"] = source_name
                data_with_source["integration_date"] = self.metadata["integration_date"]
                
                knowledge_base[source_name] = data_with_source
                logger.info(f"Added {len(data_with_source)} records from {source_name}")
        
        return knowledge_base
    
    def get_metadata(self) -> Dict:
        """
        Get metadata about the integration.
        
        Returns:
            Dictionary containing integration metadata
        """
        return self.metadata
    
    def create_summary_statistics(self) -> pd.DataFrame:
        """
        Create summary statistics for the integrated data.
        
        Returns:
            DataFrame with summary statistics
        """
        summary_data = []
        
        for source_name, data in self.integrated_data.items():
            summary_data.append({
                "source": source_name,
                "total_records": len(data),
                "columns": len(data.columns),
                "non_null_records": data.notna().sum().sum(),
                "null_records": data.isna().sum().sum()
            })
        
        return pd.DataFrame(summary_data)
