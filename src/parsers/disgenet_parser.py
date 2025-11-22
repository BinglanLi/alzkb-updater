"""
DisGeNETParser: Parser for DisGeNET data.

DisGeNET is a comprehensive database of gene-disease associations
from various sources including literature and databases.

Source: https://www.disgenet.org/
Note: Requires free account for data download.
"""

import logging
from typing import Dict, Optional
import pandas as pd
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class DisGeNETParser(BaseParser):
    """
    Parser for DisGeNET gene-disease association data.
    
    Note: DisGeNET data requires manual download due to licensing.
    This parser expects the data files to be placed in the data directory.
    """
    
    def download_data(self) -> bool:
        """
        Check for DisGeNET data files.
        
        Since DisGeNET requires manual download, this method only checks
        if the required files exist.
        
        Returns:
            True if files exist, False otherwise.
        """
        logger.info("Checking for DisGeNET data files...")
        logger.info("Note: DisGeNET data must be downloaded manually from:")
        logger.info("  https://www.disgenet.org/downloads")
        logger.info("  Required files:")
        logger.info("    - curated_gene_disease_associations.tsv")
        logger.info("    - disease_mappings.tsv")
        
        import os
        
        # Check for required files
        required_files = [
            "curated_gene_disease_associations.tsv",
            "disease_mappings.tsv"
        ]
        
        all_exist = True
        for filename in required_files:
            filepath = self.get_file_path(filename)
            if os.path.exists(filepath):
                logger.info(f"✓ Found {filename}")
            else:
                logger.error(f"✗ {filename} not found at: {filepath}")
                all_exist = False
        
        if not all_exist:
            logger.error("Please download manually and place in the disgenet directory")
            return False
        
        return True
    
    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse DisGeNET data.
        
        Returns:
            Dictionary with 'associations' and 'disease_mappings' DataFrames.
        """
        logger.info("Parsing DisGeNET data...")
        
        result = {}
        
        # Parse gene-disease associations
        assoc_file = self.get_file_path("curated_gene_disease_associations.tsv")
        
        try:
            assoc_df = self.read_tsv(assoc_file)
            
            if assoc_df is not None:
                result['associations'] = assoc_df
                logger.info(f"✓ Parsed {len(assoc_df)} gene-disease associations")
                
        except Exception as e:
            logger.error(f"Failed to parse associations: {e}")
        
        # Parse disease mappings
        mappings_file = self.get_file_path("disease_mappings.tsv")
        
        try:
            mappings_df = self.read_tsv(mappings_file)
            
            if mappings_df is not None:
                result['disease_mappings'] = mappings_df
                logger.info(f"✓ Parsed {len(mappings_df)} disease mappings")
                
        except Exception as e:
            logger.error(f"Failed to parse disease mappings: {e}")
        
        return result
    
    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for DisGeNET data.
        
        Returns:
            Dictionary describing the schema for associations and mappings.
        """
        return {
            'associations': {
                'geneId': 'NCBI Gene ID',
                'geneSymbol': 'Gene symbol',
                'diseaseId': 'Disease identifier (UMLS CUI)',
                'diseaseName': 'Disease name',
                'score': 'Association score',
                'source': 'Data source'
            },
            'disease_mappings': {
                'diseaseId': 'Disease identifier (UMLS CUI)',
                'name': 'Disease name',
                'vocabulary': 'Vocabulary/ontology',
                'code': 'Disease code in vocabulary'
            }
        }
    
    def filter_alzheimer_associations(self, assoc_df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter associations for Alzheimer's disease.
        
        Args:
            assoc_df: DataFrame of all gene-disease associations
        
        Returns:
            Filtered DataFrame of Alzheimer's-related associations
        """
        logger.info("Filtering for Alzheimer's disease associations...")
        
        # Search for Alzheimer's in disease name
        mask = assoc_df['diseaseName'].str.contains(
            'Alzheimer', case=False, na=False
        )
        
        alzheimer_assoc = assoc_df[mask].copy()
        
        logger.info(f"✓ Found {len(alzheimer_assoc)} Alzheimer's gene-disease associations")
        
        if len(alzheimer_assoc) > 0:
            # Show unique diseases
            unique_diseases = alzheimer_assoc['diseaseName'].unique()
            logger.info(f"Unique Alzheimer's diseases: {len(unique_diseases)}")
            for disease in unique_diseases[:5]:
                logger.info(f"  - {disease}")
            
            # Show top associated genes
            top_genes = alzheimer_assoc['geneSymbol'].value_counts().head(10)
            logger.info(f"Top associated genes: {dict(top_genes)}")
        
        return alzheimer_assoc
    
    def get_alzheimer_disease_ids(self, mappings_df: pd.DataFrame) -> list:
        """
        Get disease IDs for Alzheimer's disease from mappings.
        
        Args:
            mappings_df: DataFrame of disease mappings
        
        Returns:
            List of disease IDs (UMLS CUIs) for Alzheimer's disease
        """
        logger.info("Finding Alzheimer's disease IDs...")
        
        mask = mappings_df['name'].str.contains(
            'Alzheimer', case=False, na=False
        )
        
        alzheimer_mappings = mappings_df[mask]
        disease_ids = alzheimer_mappings['diseaseId'].unique().tolist()
        
        logger.info(f"✓ Found {len(disease_ids)} Alzheimer's disease IDs")
        
        return disease_ids
