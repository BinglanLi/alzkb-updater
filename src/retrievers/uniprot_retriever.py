"""
UniProt data retriever for Alzheimer's disease related proteins
"""
import requests
import pandas as pd
import time
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UniProtRetriever:
    """Retrieves Alzheimer's-related protein data from UniProt"""
    
    def __init__(self, config: dict):
        self.base_url = config["base_url"]
        self.query = config["query"]
        self.fields = config["fields"]
        self.format = config["format"]
        self.size = config["size"]
        
    def fetch_data(self) -> pd.DataFrame:
        """
        Fetch Alzheimer's related proteins from UniProt
        
        Returns:
            DataFrame with protein information
        """
        logger.info("Fetching data from UniProt...")
        
        params = {
            "query": self.query,
            "fields": self.fields,
            "format": self.format,
            "size": self.size
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse TSV response
            from io import StringIO
            df = pd.read_csv(StringIO(response.text), sep='\t')
            
            logger.info(f"Retrieved {len(df)} proteins from UniProt")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching UniProt data: {e}")
            return pd.DataFrame()
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize UniProt data
        
        Args:
            df: Raw UniProt dataframe
            
        Returns:
            Cleaned dataframe
        """
        if df.empty:
            return df
            
        logger.info("Cleaning UniProt data...")
        
        # Rename columns for consistency
        column_mapping = {
            "Entry": "uniprot_id",
            "Entry Name": "entry_name",
            "Gene Names": "gene_names",
            "Protein names": "protein_name",
            "Organism": "organism",
            "Length": "sequence_length",
            "Function [CC]": "function",
            "Involvement in disease": "disease_association"
        }
        
        df = df.rename(columns=column_mapping)
        
        # Extract primary gene name
        if 'gene_names' in df.columns:
            df['gene_name'] = df['gene_names'].apply(
                lambda x: str(x).split()[0] if pd.notna(x) and str(x) != 'nan' else None
            )
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['uniprot_id'])
        
        # Add source column
        df['source'] = 'UniProt'
        
        logger.info(f"Cleaned data: {len(df)} unique proteins")
        return df
    
    def save_data(self, df: pd.DataFrame, output_path: str):
        """Save data to CSV"""
        df.to_csv(output_path, index=False)
        logger.info(f"Saved UniProt data to {output_path}")
