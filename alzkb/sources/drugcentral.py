"""
DrugCentral data source implementation
"""
import pandas as pd
import requests
import logging
from alzkb.sources.base import DataSource

logger = logging.getLogger(__name__)


class DrugCentralSource(DataSource):
    """DrugCentral data source for drug information"""
    
    def __init__(self, output_dir: str, keywords: list[str]):
        super().__init__("DrugCentral", "https://unmtid-shinyapps.net/download/", output_dir)
        self.keywords = [kw.lower() for kw in keywords]
        
    def fetch_data(self) -> pd.DataFrame:
        """Fetch drug data from DrugCentral
        
        Note: DrugCentral provides downloadable files. For this demo, we'll simulate
        fetching a subset of drug-indication data.
        """
        logger.info("Fetching drug-indication data from DrugCentral")
        
        # DrugCentral provides structured downloads
        # For demo purposes, we'll create sample data structure
        # In production, you would download actual files from:
        # https://unmtid-shinyapps.net/download/DrugCentral/
        
        try:
            # Simulate fetching drug indications
            # In real implementation, download and parse the actual file
            sample_data = {
                'struct_id': [1, 2, 3, 4, 5],
                'drug_name': ['Donepezil', 'Rivastigmine', 'Galantamine', 'Memantine', 'Aducanumab'],
                'indication': ['Alzheimer Disease', 'Alzheimer Disease', 'Alzheimer Disease', 
                              'Alzheimer Disease', 'Alzheimer Disease'],
                'approval_year': [1996, 2000, 2001, 2003, 2021],
                'mechanism': ['Acetylcholinesterase Inhibitor', 'Acetylcholinesterase Inhibitor',
                            'Acetylcholinesterase Inhibitor', 'NMDA Receptor Antagonist',
                            'Amyloid-beta targeting monoclonal antibody']
            }
            
            df = pd.DataFrame(sample_data)
            
            logger.info(f"Fetched {len(df)} drug records from DrugCentral")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching DrugCentral data: {e}")
            return pd.DataFrame()
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize DrugCentral data"""
        if df.empty:
            return df
            
        # Standardize column names
        column_mapping = {
            'struct_id': 'drug_id',
            'drug_name': 'drug_name',
            'indication': 'indication',
            'approval_year': 'approval_year',
            'mechanism': 'mechanism_of_action'
        }
        
        cleaned_df = df.rename(columns=column_mapping)
        
        # Add metadata
        cleaned_df['source'] = 'DrugCentral'
        cleaned_df['source_type'] = 'drug'
        cleaned_df['last_updated'] = pd.Timestamp.now().isoformat()
        
        # Filter for Alzheimer's related drugs
        alzheimer_mask = cleaned_df['indication'].str.contains(
            '|'.join(self.keywords), case=False, na=False
        )
        cleaned_df = cleaned_df[alzheimer_mask]
        
        # Handle missing values
        cleaned_df = cleaned_df.fillna('')
        
        logger.info(f"Cleaned {len(cleaned_df)} drug records")
        return cleaned_df
