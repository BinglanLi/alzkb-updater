"""
GWAS Catalog Parser for AlzKB.

This module parses the GWAS Catalog to extract gene-disease associations
(geneAssociatesWithDisease) for AlzKB.

Data Source: https://www.ebi.ac.uk/gwas/api/search/downloads/full

Output:
  - gene_disease_gwas.tsv: Gene-disease associations from GWAS studies
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

from ..base_parser import BaseParser

logger = logging.getLogger(__name__)


class GWASParser(BaseParser):
    """
    Parser for the GWAS Catalog.

    Extracts gene-disease associations from genome-wide association studies
    for use in AlzKB's geneAssociatesWithDisease relationships.
    """

    # GWAS Catalog download URL
    GWAS_URL = "https://www.ebi.ac.uk/gwas/api/search/downloads/full"

    def __init__(self, data_dir: str):
        """
        Initialize the GWAS Catalog parser.

        Args:
            data_dir: Directory to store downloaded and processed data
        """
        super().__init__(data_dir)
        self.source_name = "gwas"

    def download_data(self) -> bool:
        """
        Download the GWAS Catalog data.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading GWAS Catalog...")

        result = self.download_file(self.GWAS_URL, "gwas_catalog.tsv")

        if result:
            logger.info(f"Successfully downloaded GWAS Catalog to {result}")
            return True
        else:
            logger.error("Failed to download GWAS Catalog")
            return False

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse the GWAS Catalog TSV file.

        Returns:
            Dictionary with:
              - 'gene_disease_gwas': DataFrame of gene-disease associations
        """
        tsv_path = self.source_dir / "gwas_catalog.tsv"

        if not tsv_path.exists():
            logger.error(f"GWAS Catalog file not found: {tsv_path}")
            return {}

        logger.info(f"Parsing GWAS Catalog from {tsv_path}")

        try:
            # Read GWAS Catalog (tab-separated, may have encoding issues)
            df = pd.read_csv(
                tsv_path,
                sep='\t',
                low_memory=False,
                encoding='utf-8',
                on_bad_lines='skip'
            )

            logger.info(f"Loaded {len(df)} GWAS associations")

            # Extract relevant columns
            # Key columns: REPORTED GENE(S), DISEASE/TRAIT, MAPPED_GENE, P-VALUE, STUDY ACCESSION
            relevant_cols = [
                'REPORTED GENE(S)',
                'MAPPED_GENE',
                'DISEASE/TRAIT',
                'MAPPED_TRAIT',
                'MAPPED_TRAIT_URI',
                'P-VALUE',
                'STUDY ACCESSION',
                'PUBMEDID',
                'OR or BETA',
                'RISK ALLELE FREQUENCY'
            ]

            # Keep only columns that exist
            existing_cols = [c for c in relevant_cols if c in df.columns]
            df = df[existing_cols].copy()

            # Process gene-disease associations
            associations = self._extract_associations(df)

            logger.info(f"Extracted {len(associations)} gene-disease associations")

            return {
                "gene_disease_gwas": pd.DataFrame(associations)
            }

        except Exception as e:
            logger.error(f"Error parsing GWAS Catalog: {e}")
            return {}

    def _extract_associations(self, df: pd.DataFrame) -> List[Dict]:
        """
        Extract gene-disease associations from GWAS data.

        Args:
            df: GWAS Catalog DataFrame

        Returns:
            List of gene-disease association dictionaries
        """
        associations = []

        for _, row in df.iterrows():
            # Get gene(s) - prefer MAPPED_GENE over REPORTED GENE(S)
            genes = self._parse_genes(row)
            if not genes:
                continue

            # Get disease/trait
            disease_trait = row.get('DISEASE/TRAIT', '')
            mapped_trait = row.get('MAPPED_TRAIT', '')
            mapped_trait_uri = row.get('MAPPED_TRAIT_URI', '')

            if not disease_trait and not mapped_trait:
                continue

            # Get p-value
            p_value = row.get('P-VALUE', '')
            try:
                p_value = float(p_value) if p_value else None
            except (ValueError, TypeError):
                p_value = None

            # Get study info
            study_accession = row.get('STUDY ACCESSION', '')
            pubmed_id = row.get('PUBMEDID', '')

            # Create association for each gene
            for gene in genes:
                if not gene or gene == '-' or gene == 'NR':
                    continue

                assoc = {
                    "gene_symbol": gene.strip(),
                    "disease_trait": disease_trait,
                    "mapped_trait": mapped_trait,
                    "mapped_trait_uri": mapped_trait_uri,
                    "p_value": p_value,
                    "study_accession": study_accession,
                    "pubmed_id": pubmed_id,
                    "relationship": "geneAssociatesWithDisease",
                    "source": "GWAS_Catalog"
                }
                associations.append(assoc)

        # Remove duplicates based on gene and disease
        seen = set()
        unique_associations = []
        for assoc in associations:
            key = (assoc['gene_symbol'], assoc['disease_trait'])
            if key not in seen:
                seen.add(key)
                unique_associations.append(assoc)

        return unique_associations

    def _parse_genes(self, row: pd.Series) -> List[str]:
        """
        Parse gene symbols from GWAS row.

        Args:
            row: GWAS Catalog row

        Returns:
            List of gene symbols
        """
        genes = []

        # Try MAPPED_GENE first (more reliable)
        mapped_gene = row.get('MAPPED_GENE', '')
        if pd.notna(mapped_gene) and mapped_gene:
            # Split on common delimiters
            for gene in str(mapped_gene).replace(';', ',').replace(' - ', ',').split(','):
                gene = gene.strip()
                if gene and gene not in ['NR', '-', 'intergenic']:
                    genes.append(gene)

        # If no mapped genes, try reported genes
        if not genes:
            reported_genes = row.get('REPORTED GENE(S)', '')
            if pd.notna(reported_genes) and reported_genes:
                for gene in str(reported_genes).replace(';', ',').replace(' - ', ',').split(','):
                    gene = gene.strip()
                    if gene and gene not in ['NR', '-', 'intergenic']:
                        genes.append(gene)

        return genes

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for GWAS Catalog data.

        Returns:
            Dictionary defining the schema for gene-disease associations
        """
        return {
            "gene_disease_gwas": {
                "gene_symbol": "Gene symbol",
                "disease_trait": "Reported disease/trait",
                "mapped_trait": "Mapped trait (EFO term)",
                "mapped_trait_uri": "EFO URI for the trait",
                "p_value": "Association p-value",
                "study_accession": "GWAS study accession",
                "pubmed_id": "PubMed ID of the study",
                "relationship": "Relationship type (geneAssociatesWithDisease)",
                "source": "Data source (GWAS_Catalog)"
            }
        }
