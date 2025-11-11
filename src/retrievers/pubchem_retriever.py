"""
PubChem data retriever for compound information.
"""
import pandas as pd
import json
from typing import List, Optional
from .base_retriever import BaseRetriever


class PubChemRetriever(BaseRetriever):
    """Retrieve compound data from PubChem."""
    
    def __init__(self):
        super().__init__(
            name="PubChem",
            base_url="https://pubchem.ncbi.nlm.nih.gov/rest/pug",
            rate_limit=0.2  # 5 requests per second max
        )
    
    def get_schema(self) -> List[str]:
        """Get the expected schema for PubChem data."""
        return [
            "pubchem_cid",
            "compound_name",
            "molecular_formula",
            "molecular_weight",
            "smiles",
            "inchi",
            "description"
        ]
    
    def _search_compounds(self, query: str, limit: int = 100) -> List[int]:
        """
        Search for compound IDs matching the query.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of PubChem CIDs
        """
        url = f"{self.base_url}/compound/name/{query}/cids/JSON"
        params = {"MaxRecords": limit}
        
        response = self._make_request(url, params=params)
        
        if response is None:
            return []
        
        try:
            data = response.json()
            cids = data.get("IdentifierList", {}).get("CID", [])
            return cids[:limit]
        except Exception as e:
            self.logger.error(f"Error parsing search results: {str(e)}")
            return []
    
    def _get_compound_properties(self, cids: List[int]) -> pd.DataFrame:
        """
        Get properties for a list of compound IDs.
        
        Args:
            cids: List of PubChem CIDs
            
        Returns:
            DataFrame with compound properties
        """
        if not cids:
            return pd.DataFrame(columns=self.get_schema())
        
        # Batch request for efficiency (max 100 at a time)
        cid_str = ",".join(map(str, cids[:100]))
        url = f"{self.base_url}/compound/cid/{cid_str}/property/MolecularFormula,MolecularWeight,CanonicalSMILES,InChI,IUPACName/JSON"
        
        response = self._make_request(url)
        
        if response is None:
            return pd.DataFrame(columns=self.get_schema())
        
        try:
            data = response.json()
            properties = data.get("PropertyTable", {}).get("Properties", [])
            
            records = []
            for prop in properties:
                record = {
                    "pubchem_cid": prop.get("CID"),
                    "compound_name": prop.get("IUPACName", ""),
                    "molecular_formula": prop.get("MolecularFormula", ""),
                    "molecular_weight": prop.get("MolecularWeight", None),
                    "smiles": prop.get("CanonicalSMILES", ""),
                    "inchi": prop.get("InChI", ""),
                    "description": None  # Would need separate API call
                }
                records.append(record)
            
            return pd.DataFrame(records)
            
        except Exception as e:
            self.logger.error(f"Error parsing compound properties: {str(e)}")
            return pd.DataFrame(columns=self.get_schema())
    
    def retrieve_data(self, query: str = "alzheimer", limit: int = 50) -> pd.DataFrame:
        """
        Retrieve compound data from PubChem.
        
        Args:
            query: Search query (default: alzheimer)
            limit: Maximum number of results
            
        Returns:
            DataFrame with compound information
        """
        self.logger.info(f"Retrieving PubChem data for query: {query}")
        
        # First, search for compound IDs
        cids = self._search_compounds(query, limit)
        
        if not cids:
            self.logger.warning("No compounds found in PubChem")
            return pd.DataFrame(columns=self.get_schema())
        
        self.logger.info(f"Found {len(cids)} compounds")
        
        # Get properties for the compounds
        df = self._get_compound_properties(cids)
        
        self.logger.info(f"Retrieved {len(df)} compounds from PubChem")
        return df
