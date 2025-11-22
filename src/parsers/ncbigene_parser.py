"""
NCBIGeneParser: Parser for NCBI Gene data.

NCBI Gene provides comprehensive gene information for multiple organisms.
For AlzKB, we focus on human genes (Homo sapiens).

Source: https://ftp.ncbi.nlm.nih.gov/gene/DATA/GENE_INFO/Mammalia/
"""

import logging
from typing import Dict, Optional
import pandas as pd
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class NCBIGeneParser(BaseParser):
    """
    Parser for NCBI Gene data.
    
    Downloads and parses human gene information from NCBI.
    """
    
    GENE_INFO_URL = "https://ftp.ncbi.nlm.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz"
    
    # Optional: Bgee expression data
    BGEE_URL = "https://bgee.org/ftp/bgee_v15_0/download/calls/expr_calls/Homo_sapiens_expr_advanced.tsv.gz"
    
    def download_data(self) -> bool:
        """
        Download NCBI Gene data.
        
        Returns:
            True if successful, False otherwise.
        """
        logger.info("Downloading NCBI Gene data...")
        
        # Download gene info file (gzipped)
        gene_info_gz = self.download_file(self.GENE_INFO_URL, "Homo_sapiens.gene_info.gz")
        if not gene_info_gz:
            logger.error("Failed to download NCBI gene info file")
            return False
        
        # Extract gene info file
        gene_info_file = self.extract_gzip(gene_info_gz)
        if not gene_info_file:
            logger.error("Failed to extract NCBI gene info file")
            return False
        
        logger.info("✓ Successfully downloaded NCBI Gene data")
        
        # Optionally download Bgee expression data
        logger.info("Attempting to download Bgee expression data (optional)...")
        try:
            bgee_gz = self.download_file(self.BGEE_URL, "Homo_sapiens_expr_advanced.tsv.gz")
            if bgee_gz:
                self.extract_gzip(bgee_gz)
                logger.info("✓ Downloaded Bgee expression data")
        except Exception as e:
            logger.warning(f"Could not download Bgee data (optional): {e}")
        
        return True
    
    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse NCBI Gene data.
        
        Returns:
            Dictionary with 'genes' DataFrame.
        """
        logger.info("Parsing NCBI Gene data...")
        
        result = {}
        
        # Parse gene info file
        gene_info_file = self.get_file_path("Homo_sapiens.gene_info")
        
        # Column names for NCBI gene_info file
        columns = [
            'tax_id', 'GeneID', 'Symbol', 'LocusTag', 'Synonyms', 'dbXrefs',
            'chromosome', 'map_location', 'description', 'type_of_gene',
            'Symbol_from_nomenclature_authority', 
            'Full_name_from_nomenclature_authority',
            'Nomenclature_status', 'Other_designations', 
            'Modification_date', 'Feature_type'
        ]
        
        genes_df = self.read_tsv(gene_info_file, names=columns, skiprows=1, 
                                low_memory=False)
        
        if genes_df is not None:
            # Filter for human genes (tax_id = 9606)
            genes_df = genes_df[genes_df['tax_id'] == 9606].copy()
            
            result['genes'] = genes_df
            logger.info(f"✓ Parsed {len(genes_df)} human genes")
            
            # Show gene type distribution
            gene_types = genes_df['type_of_gene'].value_counts()
            logger.info(f"Gene types: {dict(gene_types)}")
        
        return result
    
    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for NCBI Gene data.
        
        Returns:
            Dictionary describing the schema for genes.
        """
        return {
            'genes': {
                'GeneID': 'NCBI Gene ID',
                'Symbol': 'Gene symbol',
                'description': 'Gene description',
                'type_of_gene': 'Type of gene (protein-coding, ncRNA, etc.)',
                'chromosome': 'Chromosome location',
                'dbXrefs': 'Cross-references to other databases',
                'Synonyms': 'Alternative gene symbols',
                'Full_name_from_nomenclature_authority': 'Official full name'
            }
        }
    
    def filter_alzheimer_genes(self, genes_df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter genes for those related to Alzheimer's disease.
        
        Args:
            genes_df: DataFrame of all genes
        
        Returns:
            Filtered DataFrame of Alzheimer's-related genes
        """
        logger.info("Filtering for Alzheimer's-related genes...")
        
        # Search in description and synonyms for Alzheimer-related terms
        alzheimer_terms = ['alzheimer', 'amyloid', 'tau', 'apoe', 'psen', 'app']
        
        mask = genes_df['description'].str.contains(
            '|'.join(alzheimer_terms), case=False, na=False
        )
        
        alzheimer_genes = genes_df[mask].copy()
        
        logger.info(f"✓ Found {len(alzheimer_genes)} Alzheimer's-related genes")
        
        return alzheimer_genes
    
    def parse_dbxrefs(self, genes_df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse the dbXrefs column to extract cross-references.
        
        Args:
            genes_df: DataFrame with dbXrefs column
        
        Returns:
            DataFrame with additional columns for each cross-reference database
        """
        logger.info("Parsing database cross-references...")
        
        df = genes_df.copy()
        
        # Common databases to extract
        dbs_to_extract = ['MIM', 'HGNC', 'Ensembl']
        
        for db in dbs_to_extract:
            df[f'xref_{db}'] = df['dbXrefs'].str.extract(
                f'{db}:([^|]+)', expand=False
            )
        
        logger.info("✓ Parsed cross-references")
        return df
