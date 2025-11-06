"""
UniProt data source implementation
"""
import pandas as pd
import requests
import time
from typing import Dict, List
import logging
from alzkb.sources.base import DataSource

logger = logging.getLogger(__name__)


class UniProtSource(DataSource):
    """UniProt data source for protein information"""
    
    def __init__(self, output_dir: str, keywords: List[str]):
        super().__init__("UniProt", "https://rest.uniprot.org/uniprotkb/stream", output_dir)
        self.keywords = keywords
        
    def fetch_data(self) -> pd.DataFrame:
        """Fetch Alzheimer's-related proteins from UniProt"""
        all_data = []
        
        # Query UniProt for each Alzheimer's keyword
        for keyword in self.keywords:
            logger.info(f"Querying UniProt for: {keyword}")
            
            # Build query parameters
            params = {
                "query": f"({keyword}) AND (reviewed:true)",
                "format": "tsv",
                "fields": "accession,id,gene_names,protein_name,organism_name,length,cc_function,cc_disease",
                "size": 100  # Limit for testing
            }
            
            try:
                response = requests.get(self.url, params=params, timeout=30)
                response.raise_for_status()
                
                # Parse TSV response
                from io import StringIO
                df = pd.read_csv(StringIO(response.text), sep='\t')
                df['search_keyword'] = keyword
                all_data.append(df)
                
                # Be nice to the API
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error fetching data for {keyword}: {e}")
                continue
        
        if not all_data:
            logger.warning("No data fetched from UniProt")
            return pd.DataFrame()
            
        # Combine all results
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Remove duplicates based on accession
        combined_df = combined_df.drop_duplicates(subset=['Entry'], keep='first')
        
        logger.info(f"Fetched {len(combined_df)} unique proteins from UniProt")
        return combined_df
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize UniProt data"""
        if df.empty:
            return df
            
        # Rename columns to standard format
        column_mapping = {
            'Entry': 'protein_id',
            'Entry Name': 'protein_name',
            'Gene Names': 'gene_names',
            'Protein names': 'protein_full_name',
            'Organism': 'organism',
            'Length': 'sequence_length',
            'Function [CC]': 'function',
            'Involvement in disease': 'disease_involvement'
        }
        
        cleaned_df = df.rename(columns=column_mapping)
        
        # Add metadata
        cleaned_df['source'] = 'UniProt'
        cleaned_df['source_type'] = 'protein'
        cleaned_df['last_updated'] = pd.Timestamp.now().isoformat()
        
        # Handle missing values
        cleaned_df = cleaned_df.fillna('')
        
        # Select relevant columns
        output_columns = [
            'protein_id', 'protein_name', 'gene_names', 'protein_full_name',
            'organism', 'sequence_length', 'function', 'disease_involvement',
            'search_keyword', 'source', 'source_type', 'last_updated'
        ]
        
        cleaned_df = cleaned_df[[col for col in output_columns if col in cleaned_df.columns]]
        
        logger.info(f"Cleaned {len(cleaned_df)} protein records")
        return cleaned_df
