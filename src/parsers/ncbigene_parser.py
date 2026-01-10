"""
NCBIGeneParser: Parser for NCBI Gene data.

NCBI Gene provides comprehensive gene information for multiple organisms.
For AlzKB, we focus on human genes (Homo sapiens).

Source: https://ftp.ncbi.nlm.nih.gov/gene/DATA/GENE_INFO/Mammalia/
"""

import logging
import pandas as pd
from typing import Dict, Optional
from pathlib import Path
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class NCBIGeneParser(BaseParser):
    """
    Parser for NCBI Gene data.

    Downloads and parses human gene information from NCBI.
    Optionally filters genes based on tissue expression using Bgee data.
    """

    GENE_INFO_URL = "https://ftp.ncbi.nlm.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz"
    GENE_INFO_FILE = "Homo_sapiens.gene_info"
    # Optional: Bgee expression data to filter genes by expression level in certain tissues
    BGEE_URL = "https://bgee.org/ftp/bgee_v15_0/download/calls/expr_calls/Homo_sapiens_expr_advanced.tsv.gz"
    BGEE_FILE = "Homo_sapiens_expr_advanced.tsv"

    def __init__(self, data_dir: str, tissue_filter: Optional[str] = None):
        """
        Initialize NCBI Gene parser.

        Args:
            data_dir: Directory for storing data files
            tissue_filter: Optional tissue name to filter genes by expression (e.g., "brain")
        """
        super().__init__(data_dir)
        self.tissue_filter = tissue_filter
        if self.tissue_filter:
            logger.info(f"Gene filtering enabled for tissue: {self.tissue_filter}")

    def download_data(self) -> bool:
        """
        Download NCBI Gene data.
        
        Returns:
            True if successful, False otherwise.
        """
        logger.info("Downloading NCBI Gene data...")
        
        # Download gene info file (gzipped)
        gene_info_gz = self.download_file(self.GENE_INFO_URL, Path(self.GENE_INFO_URL).name)
        if not gene_info_gz:
            logger.error("Failed to download NCBI gene info file")
            return False
        
        # Extract gene info file
        gene_info_file = self.extract_gzip(gene_info_gz)
        if not gene_info_file:
            logger.error("Failed to extract NCBI gene info file")
            return False
        
        # Optionally download Bgee expression data
        logger.info("Attempting to download Bgee expression data (optional)...")
        try:
            bgee_gz = self.download_file(self.BGEE_URL, Path(self.BGEE_URL).name)
            if bgee_gz:
                self.extract_gzip(bgee_gz)
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
        gene_info_file = self.get_file_path(self.GENE_INFO_FILE)

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

            logger.info(f"✓ Parsed {len(genes_df)} human genes")

            # Show gene type distribution
            gene_types = genes_df['type_of_gene'].value_counts()
            logger.info(f"Gene types: {dict(gene_types)}")

            # Parse cross-references to extract MIM, HGNC, and Ensembl IDs into separate columns
            genes_df = self.parse_dbxrefs(genes_df)

            # Apply tissue filter if specified
            if self.tissue_filter:
                genes_df = self.filter_genes_by_tissue(genes_df, self.tissue_filter)

            result['genes'] = genes_df

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
                'xref_MIM': 'MIM (OMIM) identifier',
                'xref_HGNC': 'HGNC identifier',
                'xref_Ensembl': 'Ensembl gene identifier',
                'Synonyms': 'Alternative gene symbols',
                'Full_name_from_nomenclature_authority': 'Official full name'
            }
        }
    
    
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

    def filter_genes_by_tissue(self, genes_df: pd.DataFrame, tissue_name: str) -> pd.DataFrame:
        """
        Filter genes based on tissue expression from Bgee data.

        Simple filter: checks if tissue_name exists in a line of the Bgee file,
        then extracts the Gene ID (Ensembl ID) from the first column.

        Args:
            genes_df: DataFrame of all genes
            tissue_name: Name of tissue to filter by (e.g., "brain")

        Returns:
            Filtered DataFrame of genes expressed in the specified tissue
        """
        logger.info(f"Filtering for genes expressed in '{tissue_name}'...")

        # Get path to extracted Bgee file
        bgee_file = Path(self.get_file_path(self.BGEE_FILE))

        if not bgee_file.exists():
            logger.warning(f"Bgee file not found at {bgee_file}")
            logger.warning("Tissue filtering requires Bgee data. Returning unfiltered genes.")
            return genes_df

        try:
            # Read Bgee file and collect Ensembl Gene IDs for lines containing tissue name
            tissue_gene_ids = set()

            logger.info(f"Reading Bgee expression file: {bgee_file}")
            with open(bgee_file, 'r', encoding='utf-8') as f:
                # Skip header line
                next(f, None)

                for line in f:
                    # Check if tissue name exists in the line (case-insensitive)
                    if tissue_name.lower() in line.lower():
                        # Extract first column (Gene ID - Ensembl ID)
                        parts = line.split('\t')
                        if parts:
                            gene_id = parts[0].strip()
                            if gene_id:
                                tissue_gene_ids.add(gene_id)

            logger.info(f"Found {len(tissue_gene_ids)} unique Ensembl gene IDs expressed in '{tissue_name}'")

            if not tissue_gene_ids:
                logger.warning(f"No genes found with '{tissue_name}' expression in Bgee data")
                logger.warning("Returning unfiltered genes")
                return genes_df

            # Filter genes_df based on xref_Ensembl column (already parsed by parse_dbxrefs)
            # Check if xref_Ensembl column exists
            if 'xref_Ensembl' not in genes_df.columns:
                logger.error("xref_Ensembl column not found. Expected parse_dbxrefs() to be called first.")
                logger.warning("Returning unfiltered genes")
                return genes_df

            # Filter for genes with Ensembl IDs that match tissue-expressed genes
            filtered_genes = genes_df[
                genes_df['xref_Ensembl'].isin(tissue_gene_ids)
            ].copy()

            logger.info(f"✓ Filtered to {len(filtered_genes)} genes expressed in '{tissue_name}'")
            logger.info(f"   ({len(genes_df) - len(filtered_genes)} genes removed)")

            return filtered_genes

        except Exception as e:
            logger.error(f"Error filtering genes by tissue: {e}")
            import traceback
            logger.error(traceback.format_exc())
            logger.warning("Returning unfiltered genes")
            return genes_df
