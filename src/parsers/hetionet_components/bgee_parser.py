"""
Bgee Expression Parser for AlzKB.

This module parses Bgee gene expression data to extract gene-anatomy
expression relationships for AlzKB.

Data Source: https://www.bgee.org/ftp/current/download/calls/expr_calls/

Output:
  - bodypart_overexpresses_gene.tsv: bodyPartOverexpressesGene relationships
  - bodypart_underexpresses_gene.tsv: bodyPartUnderexpressesGene relationships
"""

import logging
import gzip
from pathlib import Path
from typing import Dict, List
import pandas as pd

from ..base_parser import BaseParser

logger = logging.getLogger(__name__)


class BgeeParser(BaseParser):
    """
    Parser for Bgee gene expression database.

    Extracts gene expression data in anatomical structures for use in
    AlzKB's bodyPartOverexpressesGene and bodyPartUnderexpressesGene relationships.
    """

    # Bgee human expression calls URL
    BGEE_URL = "https://www.bgee.org/ftp/current/download/calls/expr_calls/Homo_sapiens_expr_simple.tsv.gz"

    def __init__(self, data_dir: str):
        """
        Initialize the Bgee parser.

        Args:
            data_dir: Directory to store downloaded and processed data
        """
        super().__init__(data_dir)
        self.source_name = "bgee"

    def download_data(self) -> bool:
        """
        Download Bgee expression data.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading Bgee expression data...")

        result = self.download_file(self.BGEE_URL, "Homo_sapiens_expr_simple.tsv.gz")

        if result:
            logger.info(f"Successfully downloaded Bgee to {result}")
            return True
        else:
            logger.error("Failed to download Bgee")
            return False

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse Bgee expression data.

        Returns:
            Dictionary with:
              - 'bodypart_overexpresses_gene': High expression relationships
              - 'bodypart_underexpresses_gene': Low expression relationships
        """
        tsv_path = self.source_dir / "Homo_sapiens_expr_simple.tsv.gz"

        if not tsv_path.exists():
            logger.error(f"Bgee file not found: {tsv_path}")
            return {}

        logger.info(f"Parsing Bgee from {tsv_path}")

        try:
            # Read Bgee expression calls
            df = pd.read_csv(
                tsv_path,
                sep='\t',
                compression='gzip',
                low_memory=False
            )

            logger.info(f"Loaded {len(df)} Bgee expression records")

            # Extract over/under expression relationships
            overexpressed = []
            underexpressed = []

            # Bgee columns: Gene ID, Gene name, Anatomical entity ID, Anatomical entity name,
            # Expression, Call quality, Expression score, Expression rank

            for _, row in df.iterrows():
                gene_id = row.get('Gene ID', '')
                gene_name = row.get('Gene name', '')
                anatomy_id = row.get('Anatomical entity ID', '')
                anatomy_name = row.get('Anatomical entity name', '')
                expression = row.get('Expression', '')
                expression_score = row.get('Expression score', None)
                expression_rank = row.get('Expression rank', None)

                if not gene_id or not anatomy_id:
                    continue

                # Only include UBERON anatomy IDs
                if not str(anatomy_id).startswith('UBERON:'):
                    continue

                record = {
                    "gene_id": gene_id,
                    "gene_name": gene_name,
                    "anatomy_id": anatomy_id,
                    "anatomy_name": anatomy_name,
                    "expression_score": expression_score,
                    "expression_rank": expression_rank,
                    "source": "Bgee"
                }

                # Classify as over or under expressed based on expression call
                # Bgee uses "present" for expressed, expression rank indicates level
                if expression == 'present':
                    # Use expression rank to determine over/under expression
                    # Lower rank = higher expression
                    try:
                        rank = float(expression_rank) if expression_rank else 50
                        if rank <= 25:  # Top 25% = overexpressed
                            record["relationship"] = "bodyPartOverexpressesGene"
                            overexpressed.append(record)
                        elif rank >= 75:  # Bottom 25% = underexpressed
                            record["relationship"] = "bodyPartUnderexpressesGene"
                            underexpressed.append(record)
                    except (ValueError, TypeError):
                        pass

            logger.info(f"Found {len(overexpressed)} overexpression relationships")
            logger.info(f"Found {len(underexpressed)} underexpression relationships")

            result = {}
            if overexpressed:
                result["bodypart_overexpresses_gene"] = pd.DataFrame(overexpressed)
            if underexpressed:
                result["bodypart_underexpresses_gene"] = pd.DataFrame(underexpressed)

            return result

        except Exception as e:
            logger.error(f"Error parsing Bgee: {e}")
            return {}

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for Bgee data.

        Returns:
            Dictionary defining the schema for gene expression relationships
        """
        return {
            "bodypart_overexpresses_gene": {
                "gene_id": "Ensembl gene ID",
                "gene_name": "Gene symbol",
                "anatomy_id": "UBERON anatomy ID",
                "anatomy_name": "Anatomical structure name",
                "expression_score": "Bgee expression score",
                "expression_rank": "Expression rank (percentile)",
                "relationship": "Relationship type (bodyPartOverexpressesGene)",
                "source": "Data source (Bgee)"
            },
            "bodypart_underexpresses_gene": {
                "gene_id": "Ensembl gene ID",
                "gene_name": "Gene symbol",
                "anatomy_id": "UBERON anatomy ID",
                "anatomy_name": "Anatomical structure name",
                "expression_score": "Bgee expression score",
                "expression_rank": "Expression rank (percentile)",
                "relationship": "Relationship type (bodyPartUnderexpressesGene)",
                "source": "Data source (Bgee)"
            }
        }
