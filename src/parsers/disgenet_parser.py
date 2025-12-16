"""
DisGeNETParser: Parser for DisGeNET data with API support.

DisGeNET is a comprehensive database of gene-disease associations
from various sources including literature and databases.

Source: https://www.disgenet.org/
API Documentation: https://www.disgenet.org/api/
"""

import logging
import os
from typing import Dict, Optional, List
import pandas as pd
import requests
import time
from .base_parser import BaseParser
from pathlib import Path

logger = logging.getLogger(__name__)


class DisGeNETParser(BaseParser):
    """
    Parser for DisGeNET gene-disease association data with API support.
    
    Supports both API-based retrieval and manual file-based parsing.
    """
    
    API_BASE_URL = "https://www.disgenet.org/api"
    
    def __init__(self, data_dir: str, api_key: Optional[str] = None):
        """
        Initialize DisGeNET parser.
        
        Args:
            data_dir: Directory for storing data files
            api_key: DisGeNET API key (optional, for API access)
        """
        super().__init__(data_dir)
        self.api_key = api_key or os.getenv('DISGENET_API_KEY')
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({'Authorization': f'Bearer {self.api_key}'})
            logger.info("DisGeNET API key configured")
        else:
            logger.warning("No DisGeNET API key provided. Will attempt file-based parsing.")
    
    def download_data(self) -> bool:
        """
        Download or check for DisGeNET data.
        
        If API key is available, downloads data via API.
        Otherwise, checks for manually downloaded files.
        
        Returns:
            True if data is available, False otherwise.
        """
        if self.api_key:
            return self._download_via_api()
        else:
            return self._check_manual_files()
    
    def _check_manual_files(self) -> bool:
        """Check for manually downloaded DisGeNET files."""
        logger.info("Checking for DisGeNET data files...")
        logger.info("Note: DisGeNET data must be downloaded manually from:")
        logger.info("  https://www.disgenet.org/downloads")
        logger.info("  Required files:")
        logger.info("    - curated_gene_disease_associations.tsv")
        logger.info("    - disease_mappings.tsv")
        
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
            logger.error("Please download manually or provide API key")
            return False
        
        return True
    
    def _download_via_api(self) -> bool:
        """
        Download DisGeNET data via API.
        
        Returns:
            True if successful, False otherwise.
        """
        logger.info("Downloading DisGeNET data via API...")
        
        try:
            # Get Alzheimer's disease associations
            alzheimer_data = self._get_disease_associations("alzheimer")
            
            if alzheimer_data:
                # Save to file
                output_path = self.get_file_path("api_gene_disease_associations.tsv")
                alzheimer_data.to_csv(output_path, sep='\t', index=False)
                logger.info(f"✓ Downloaded {len(alzheimer_data)} associations via API")
                return True
            else:
                logger.error("Failed to download data via API")
                return False
                
        except Exception as e:
            logger.error(f"API download failed: {e}")
            return False
    
    def _get_disease_associations(self, disease_term: str, 
                                   limit: int = 10000) -> Optional[pd.DataFrame]:
        """
        Get disease-gene associations from DisGeNET API.
        
        Args:
            disease_term: Disease search term
            limit: Maximum number of results
            
        Returns:
            DataFrame of associations or None if failed
        """
        logger.info(f"Querying DisGeNET API for: {disease_term}")
        
        # First, search for disease ID
        disease_id = self._search_disease(disease_term)
        
        if not disease_id:
            logger.error(f"Could not find disease ID for: {disease_term}")
            return None
        
        logger.info(f"Found disease ID: {disease_id}")
        
        # Get gene-disease associations
        endpoint = f"{self.API_BASE_URL}/gda/disease/{disease_id}"
        params = {
            'source': 'ALL',
            'format': 'json',
            'limit': limit
        }
        
        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                logger.warning(f"No associations found for disease: {disease_id}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            logger.info(f"✓ Retrieved {len(df)} gene-disease associations")
            
            return df
            
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def _search_disease(self, disease_term: str) -> Optional[str]:
        """
        Search for disease ID by term.
        
        Args:
            disease_term: Disease search term
            
        Returns:
            Disease ID (UMLS CUI) or None if not found
        """
        endpoint = f"{self.API_BASE_URL}/disease/search"
        params = {
            'q': disease_term,
            'format': 'json'
        }
        
        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data and len(data) > 0:
                # Return the first match
                return data[0].get('disease_id')
            
            return None
            
        except requests.RequestException as e:
            logger.error(f"Disease search failed: {e}")
            return None
    
    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse DisGeNET data.
        
        Returns:
            Dictionary with 'associations' and optionally 'disease_mappings' DataFrames.
        """
        logger.info("Parsing DisGeNET data...")
        
        result = {}
        
        # Try API file first
        api_file = self.get_file_path("api_gene_disease_associations.tsv")
        if os.path.exists(api_file):
            logger.info("Using API-downloaded data")
            try:
                assoc_df = self.read_tsv(api_file)
                if assoc_df is not None:
                    result['associations'] = assoc_df
                    logger.info(f"✓ Parsed {len(assoc_df)} gene-disease associations from API")
            except Exception as e:
                logger.error(f"Failed to parse API data: {e}")
        
        # Fall back to manual files
        if 'associations' not in result:
            assoc_file = self.get_file_path("curated_gene_disease_associations.tsv")
            
            if os.path.exists(assoc_file):
                try:
                    assoc_df = self.read_tsv(assoc_file)
                    
                    if assoc_df is not None:
                        result['associations'] = assoc_df
                        logger.info(f"✓ Parsed {len(assoc_df)} gene-disease associations")
                        
                except Exception as e:
                    logger.error(f"Failed to parse associations: {e}")
        
        # Parse disease mappings if available
        mappings_file = self.get_file_path("disease_mappings.tsv")
        
        if os.path.exists(mappings_file):
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
    
    def get_alzheimer_disease_ids(self, mappings_df: pd.DataFrame) -> List[str]:
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
    
    def export_to_tsv(self, data: Dict[str, pd.DataFrame], output_dir: str) -> List[str]:
        """
        Export parsed data to TSV files for ista.
        
        Args:
            data: Dictionary of DataFrames
            output_dir: Output directory path
            
        Returns:
            List of created file paths
        """
        logger.info("Exporting DisGeNET data to TSV for ista...")
        
        os.makedirs(output_dir, exist_ok=True)
        created_files = []
        
        # Export gene-disease associations
        if 'associations' in data:
            assoc_df = data['associations']
            
            # Filter for Alzheimer's
            alzheimer_assoc = self.filter_alzheimer_associations(assoc_df)
            
            if len(alzheimer_assoc) > 0:
                output_path = os.path.join(output_dir, 'disgenet_gene_disease_associations.tsv')
                alzheimer_assoc.to_csv(output_path, sep='\t', index=False)
                created_files.append(output_path)
                logger.info(f"✓ Exported {len(alzheimer_assoc)} associations to {output_path}")
        
        return created_files


    def export_to_tsv_for_ista(self, data: Dict[str, pd.DataFrame], output_dir: str) -> List[str]:
        """
        Export parsed data to TSV files formatted for ista ingestion.
        
        Args:
            data: Dictionary of parsed DataFrames
            output_dir: Directory to save TSV files
        
        Returns:
            List of paths to created TSV files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        exported_files = []
        
        # Export gene-disease associations
        if 'gene_disease_associations' in data:
            assoc_df = data['gene_disease_associations']
            
            # Format for ista: gene_id, disease_id, score, evidence_type
            ista_df = pd.DataFrame({
                'gene_id': assoc_df.get('geneId', assoc_df.get('gene_id', '')),
                'gene_symbol': assoc_df.get('geneSymbol', assoc_df.get('gene_symbol', '')),
                'disease_id': assoc_df.get('diseaseId', assoc_df.get('disease_id', '')),
                'disease_name': assoc_df.get('diseaseName', assoc_df.get('disease_name', '')),
                'score': assoc_df.get('score', ''),
                'evidence_type': assoc_df.get('evidenceType', assoc_df.get('evidence', ''))
            })
            
            output_file = output_dir / "disgenet_gene_disease_associations.tsv"
            ista_df.to_csv(output_file, sep='\t', index=False)
            exported_files.append(str(output_file))
            logger.info(f"✓ Exported {len(ista_df)} associations to {output_file}")
        
        return exported_files
