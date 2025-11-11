"""
UniProt data retriever for protein information.
"""
import pandas as pd
from typing import List, Optional
from .base_retriever import BaseRetriever


class UniProtRetriever(BaseRetriever):
    """Retrieve protein data from UniProt."""
    
    def __init__(self):
        super().__init__(
            name="UniProt",
            base_url="https://rest.uniprot.org",
            rate_limit=0.5  # 2 requests per second max
        )
    
    def get_schema(self) -> List[str]:
        """Get the expected schema for UniProt data."""
        return [
            "uniprot_id",
            "protein_name",
            "gene_name",
            "organism",
            "function",
            "subcellular_location",
            "disease_association"
        ]
    
    def retrieve_data(self, query: str = "alzheimer", limit: int = 100) -> pd.DataFrame:
        """
        Retrieve protein data from UniProt.
        
        Args:
            query: Search query (default: alzheimer)
            limit: Maximum number of results
            
        Returns:
            DataFrame with protein information
        """
        self.logger.info(f"Retrieving UniProt data for query: {query}")
        
        # UniProt REST API endpoint
        url = f"{self.base_url}/uniprotkb/search"
        
        params = {
            "query": query,
            "format": "tsv",
            "fields": "accession,protein_name,gene_names,organism_name,cc_function,cc_subcellular_location,cc_disease",
            "size": limit
        }
        
        response = self._make_request(url, params=params)
        
        if response is None:
            self.logger.warning("Failed to retrieve data from UniProt")
            return pd.DataFrame(columns=self.get_schema())
        
        try:
            # Parse TSV response
            from io import StringIO
            df = pd.read_csv(StringIO(response.text), sep='\t')
            
            # Rename columns to match schema
            column_mapping = {
                "Entry": "uniprot_id",
                "Protein names": "protein_name",
                "Gene Names": "gene_name",
                "Organism": "organism",
                "Function [CC]": "function",
                "Subcellular location [CC]": "subcellular_location",
                "Involvement in disease": "disease_association"
            }
            
            df = df.rename(columns=column_mapping)
            
            # Ensure all schema columns exist
            for col in self.get_schema():
                if col not in df.columns:
                    df[col] = None
            
            df = df[self.get_schema()]
            
            self.logger.info(f"Retrieved {len(df)} proteins from UniProt")
            return df
            
        except Exception as e:
            self.logger.error(f"Error parsing UniProt response: {str(e)}")
            return pd.DataFrame(columns=self.get_schema())
