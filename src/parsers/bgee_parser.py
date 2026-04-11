"""
Bgee Expression Parser for the knowledge graph.

This module parses Bgee gene expression data to extract gene-anatomy
differential expression relationships for the knowledge graph.

Data Source: https://github.com/dhimmel/bgee (precomputed differential expression)
Commit: 08ba54e83ee8e28dec22b4351d29e23f1d034d30

Output:
  - anatomy_upregulates_gene.tsv: AuG edges (Anatomy upregulates Gene)
  - anatomy_downregulates_gene.tsv: AdG edges (Anatomy downregulates Gene)
"""

import logging
import gzip
from pathlib import Path
from typing import Dict, List, Set
import pandas as pd

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class BgeeParser(BaseParser):
    """
    Parser for Bgee gene expression database.

    Extracts differential gene expression data from the pre-computed
    dhimmel/bgee repository, which provides a pivoted matrix of
    expression direction by anatomy.
    """

    # Pre-computed differential expression from dhimmel/bgee
    BGEE_COMMIT = "08ba54e83ee8e28dec22b4351d29e23f1d034d30"
    BGEE_DIFFEX_URL = f"https://raw.githubusercontent.com/dhimmel/bgee/{BGEE_COMMIT}/data/diffex.tsv.gz"

    # Fallback: current Bgee expression calls (if pre-computed not available)
    BGEE_CURRENT_URL = "https://www.bgee.org/ftp/current/download/calls/expr_calls/Homo_sapiens_expr_simple.tsv.gz"

    def __init__(self, data_dir: str, valid_uberon_ids: Set[str] = None, valid_gene_ids: Set[int] = None):
        """
        Initialize the Bgee parser.

        Args:
            data_dir: Directory to store downloaded and processed data
            valid_uberon_ids: Optional set of valid UBERON IDs to filter by
            valid_gene_ids: Optional set of valid Entrez Gene IDs to filter by
        """
        super().__init__(data_dir)
        self.source_name = "bgee"
        self.valid_uberon_ids = valid_uberon_ids
        self.valid_gene_ids = valid_gene_ids

    def download_data(self) -> bool:
        """
        Download Bgee differential expression data.

        Downloads the pre-computed diffex.tsv.gz from dhimmel/bgee
        which contains a pivoted matrix of differential expression.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading Bgee differential expression data...")

        # Try pre-computed first
        result = self.download_file(self.BGEE_DIFFEX_URL, "diffex.tsv.gz")

        if result:
            logger.info(f"Successfully downloaded Bgee diffex to {result}")
            return True
        else:
            logger.error("Failed to download Bgee diffex data")
            return False

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse Bgee differential expression data.

        The diffex.tsv.gz file is a pivoted matrix where:
        - Rows are genes (GeneID column)
        - Columns are UBERON anatomy IDs
        - Values are: -1 (downregulated), 0 (no change), 1 (upregulated)

        Returns:
            Dictionary with:
              - 'anatomy_upregulates_gene': AuG edges
              - 'anatomy_downregulates_gene': AdG edges
        """
        diffex_path = self.source_dir / "diffex.tsv.gz"

        if not diffex_path.exists():
            logger.error(f"Bgee diffex file not found: {diffex_path}")
            return {}

        logger.info(f"Parsing Bgee differential expression from {diffex_path}")

        try:
            # Read the pivoted diffex matrix
            df = pd.read_csv(
                diffex_path,
                sep='\t',
                compression='gzip',
                low_memory=False
            )

            logger.info(f"Loaded diffex matrix: {df.shape[0]} genes x {df.shape[1]-1} anatomies")

            # Melt the pivoted matrix to long format
            # First column is GeneID, rest are UBERON IDs
            melted = pd.melt(
                df,
                id_vars='GeneID',
                var_name='uberon_id',
                value_name='direction'
            )

            # Filter out no-change (direction == 0)
            melted = melted[melted['direction'] != 0]

            logger.info(f"Found {len(melted)} differential expression relationships")

            # Apply filters if provided
            if self.valid_uberon_ids:
                melted = melted[melted['uberon_id'].isin(self.valid_uberon_ids)]
                logger.info(f"After UBERON filter: {len(melted)} relationships")

            if self.valid_gene_ids:
                melted = melted[melted['GeneID'].isin(self.valid_gene_ids)]
                logger.info(f"After Gene ID filter: {len(melted)} relationships")

            # Separate upregulation and downregulation
            upregulated = melted[melted['direction'] == 1].copy()
            downregulated = melted[melted['direction'] == -1].copy()

            result = {}

            # Anatomy upregulates Gene (AuG)
            if len(upregulated) > 0:
                aug = pd.DataFrame({
                    'uberon_id': upregulated['uberon_id'],
                    'entrez_gene_id': upregulated['GeneID'],
                    'source': 'Bgee',
                    'unbiased': True,
                    'sourceDatabase': 'Bgee'
                })
                result["anatomy_upregulates_gene"] = aug
                logger.info(f"Parsed {len(aug)} Anatomy-upregulates-Gene edges")

            # Anatomy downregulates Gene (AdG)
            if len(downregulated) > 0:
                adg = pd.DataFrame({
                    'uberon_id': downregulated['uberon_id'],
                    'entrez_gene_id': downregulated['GeneID'],
                    'source': 'Bgee',
                    'unbiased': True,
                    'sourceDatabase': 'Bgee'
                })
                result["anatomy_downregulates_gene"] = adg
                logger.info(f"Parsed {len(adg)} Anatomy-downregulates-Gene edges")

            return result

        except Exception as e:
            logger.error(f"Error parsing Bgee diffex: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for Bgee data.

        Returns:
            Dictionary defining the schema for differential expression relationships
        """
        return {
            "anatomy_upregulates_gene": {
                "uberon_id": "UBERON anatomy ID",
                "entrez_gene_id": "Entrez Gene ID",
                "source": "Data source (Bgee)",
                "unbiased": "Whether edge is unbiased (True for Bgee)",
                "sourceDatabase": "Source database name (Bgee)"
            },
            "anatomy_downregulates_gene": {
                "uberon_id": "UBERON anatomy ID",
                "entrez_gene_id": "Entrez Gene ID",
                "source": "Data source (Bgee)",
                "unbiased": "Whether edge is unbiased (True for Bgee)",
                "sourceDatabase": "Source database name (Bgee)"
            }
        }
