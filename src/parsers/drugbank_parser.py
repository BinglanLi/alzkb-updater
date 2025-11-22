"""
DrugBankParser: Parser for DrugBank data.

DrugBank is a comprehensive database of drug information including
drug targets, interactions, and pharmacology.

Source: https://go.drugbank.com/releases/latest
Note: Requires free academic account for access.
"""

import logging
from typing import Dict, Optional
import pandas as pd
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class DrugBankParser(BaseParser):
    """
    Parser for DrugBank data.
    
    Note: DrugBank data requires manual download due to licensing.
    This parser expects the data files to be placed in the data directory.
    """
    
    def download_data(self) -> bool:
        """
        Check for DrugBank data files.
        
        Since DrugBank requires manual download, this method only checks
        if the required files exist.
        
        Returns:
            True if files exist, False otherwise.
        """
        logger.info("Checking for DrugBank data files...")
        logger.info("Note: DrugBank data must be downloaded manually from:")
        logger.info("  https://go.drugbank.com/releases/latest")
        logger.info("  Required file: drug_links.csv (from External Links section)")
        
        # Check for drug_links file
        drug_links_path = self.get_file_path("drug_links.csv")
        
        import os
        if os.path.exists(drug_links_path):
            logger.info(f"✓ Found drug_links.csv")
            return True
        else:
            logger.error(f"✗ drug_links.csv not found at: {drug_links_path}")
            logger.error("Please download manually and place in the drugbank directory")
            return False
    
    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse DrugBank data.
        
        Returns:
            Dictionary with 'drugs' DataFrame.
        """
        logger.info("Parsing DrugBank data...")
        
        result = {}
        
        # Parse drug links file
        drug_links_file = self.get_file_path("drug_links.csv")
        
        try:
            drugs_df = self.read_csv(drug_links_file)
            
            if drugs_df is not None:
                # Rename columns for consistency
                column_mapping = {
                    'DrugBank ID': 'drugbank_id',
                    'Name': 'drug_name',
                    'CAS Number': 'cas_number',
                    'PubChem Compound ID': 'pubchem_cid',
                    'PubChem Substance ID': 'pubchem_sid',
                    'ChEMBL ID': 'chembl_id',
                    'ChEBI ID': 'chebi_id',
                    'KEGG Compound ID': 'kegg_compound_id',
                    'KEGG Drug ID': 'kegg_drug_id'
                }
                
                # Rename columns that exist
                existing_cols = {k: v for k, v in column_mapping.items() if k in drugs_df.columns}
                drugs_df = drugs_df.rename(columns=existing_cols)
                
                result['drugs'] = drugs_df
                logger.info(f"✓ Parsed {len(drugs_df)} drugs")
                
        except Exception as e:
            logger.error(f"Failed to parse DrugBank data: {e}")
        
        return result
    
    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for DrugBank data.
        
        Returns:
            Dictionary describing the schema for drugs.
        """
        return {
            'drugs': {
                'drugbank_id': 'DrugBank identifier',
                'drug_name': 'Drug name',
                'cas_number': 'CAS Registry Number',
                'pubchem_cid': 'PubChem Compound ID',
                'chembl_id': 'ChEMBL identifier',
                'chebi_id': 'ChEBI identifier',
                'kegg_compound_id': 'KEGG Compound ID',
                'kegg_drug_id': 'KEGG Drug ID'
            }
        }
    
    def filter_alzheimer_drugs(self, drugs_df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter drugs for those used in Alzheimer's disease.
        
        Args:
            drugs_df: DataFrame of all drugs
        
        Returns:
            Filtered DataFrame of Alzheimer's-related drugs
        """
        logger.info("Filtering for Alzheimer's-related drugs...")
        
        # Known Alzheimer's drugs
        known_ad_drugs = [
            'donepezil', 'rivastigmine', 'galantamine', 'memantine',
            'aducanumab', 'lecanemab', 'tacrine'
        ]
        
        mask = drugs_df['drug_name'].str.lower().isin(known_ad_drugs)
        
        # Also search for drugs containing "alzheimer" in annotations
        # (if that data is available)
        
        alzheimer_drugs = drugs_df[mask].copy()
        
        logger.info(f"✓ Found {len(alzheimer_drugs)} known Alzheimer's drugs")
        
        if len(alzheimer_drugs) > 0:
            logger.info("Drugs found:")
            for _, drug in alzheimer_drugs.iterrows():
                logger.info(f"  - {drug.get('drug_name', 'Unknown')}")
        
        return alzheimer_drugs
