"""
DoRothEA Parser for AlzKB.

This module parses DoRothEA data to extract transcription factor nodes
and TF-gene regulatory relationships for AlzKB.

DoRothEA is a gene regulatory network containing signed TF-target interactions.

Data Source: https://github.com/saezlab/dorothea (via decoupler-py or flat files)

Output:
  - transcription_factor_nodes.tsv: TranscriptionFactor nodes
  - tf_gene_interactions.tsv: transcriptionFactorInteractsWithGene relationships
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)


class DoRothEAParser(BaseParser):
    """
    Parser for DoRothEA transcription factor regulatory network.

    Extracts TF-gene regulatory relationships for use in AlzKB's
    transcriptionFactorInteractsWithGene relationships.
    """

    # DoRothEA GitHub raw data URL
    DOROTHEA_URL = "https://raw.githubusercontent.com/saezlab/dorothea/master/data/dorothea_hs.csv"

    # Alternative: Zenodo release
    DOROTHEA_ZENODO_URL = "https://zenodo.org/record/3701362/files/dorothea_hs.csv"

    def __init__(self, data_dir: str):
        """
        Initialize the DoRothEA parser.

        Args:
            data_dir: Directory to store downloaded and processed data
        """
        super().__init__(data_dir)
        self.source_name = "dorothea"

    def download_data(self) -> bool:
        """
        Download DoRothEA data.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading DoRothEA TF-gene regulatory network...")

        # Try GitHub first, then Zenodo
        result = self.download_file(self.DOROTHEA_URL, "dorothea_hs.csv")

        if not result:
            logger.info("GitHub download failed, trying Zenodo...")
            result = self.download_file(self.DOROTHEA_ZENODO_URL, "dorothea_hs.csv")

        if result:
            logger.info(f"Successfully downloaded DoRothEA to {result}")
            return True
        else:
            logger.error("Failed to download DoRothEA")
            return False

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse DoRothEA TF-gene regulatory data.

        Returns:
            Dictionary with:
              - 'transcription_factor_nodes': TF nodes
              - 'tf_gene_interactions': TF-gene regulatory relationships
        """
        csv_path = self.source_dir / "dorothea_hs.csv"

        if not csv_path.exists():
            logger.error(f"DoRothEA file not found: {csv_path}")
            return {}

        logger.info(f"Parsing DoRothEA from {csv_path}")

        try:
            # Read DoRothEA data
            # Format: tf, confidence, target, mor (mode of regulation)
            df = pd.read_csv(csv_path)

            logger.info(f"Loaded {len(df)} DoRothEA TF-target interactions")

            # Extract unique TFs as nodes
            tfs = df['tf'].unique() if 'tf' in df.columns else []
            tf_nodes = [{"tf_symbol": tf, "node_type": "TranscriptionFactor"} for tf in tfs]

            logger.info(f"Found {len(tf_nodes)} unique transcription factors")

            # Format TF-gene interactions
            interactions = []
            for _, row in df.iterrows():
                tf = row.get('tf', '')
                target = row.get('target', '')
                confidence = row.get('confidence', '')
                mor = row.get('mor', 0)  # Mode of regulation: 1=activation, -1=repression

                if not tf or not target:
                    continue

                interaction = {
                    "tf_symbol": tf,
                    "target_gene": target,
                    "confidence": confidence,
                    "mode_of_regulation": "activation" if mor > 0 else "repression" if mor < 0 else "unknown",
                    "mor_score": mor,
                    "relationship": "transcriptionFactorInteractsWithGene",
                    "source": "DoRothEA"
                }
                interactions.append(interaction)

            logger.info(f"Extracted {len(interactions)} TF-gene interactions")

            # Filter by confidence if desired (A, B, C, D, E levels)
            # A = highest confidence, E = lowest
            high_conf = [i for i in interactions if i['confidence'] in ['A', 'B', 'C']]
            logger.info(f"High confidence (A/B/C): {len(high_conf)} interactions")

            return {
                "transcription_factor_nodes": pd.DataFrame(tf_nodes),
                "tf_gene_interactions": pd.DataFrame(interactions)
            }

        except Exception as e:
            logger.error(f"Error parsing DoRothEA: {e}")
            return {}

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for DoRothEA data.

        Returns:
            Dictionary defining the schema for TF nodes and interactions
        """
        return {
            "transcription_factor_nodes": {
                "tf_symbol": "Transcription factor gene symbol",
                "node_type": "Node type (TranscriptionFactor)"
            },
            "tf_gene_interactions": {
                "tf_symbol": "Transcription factor gene symbol",
                "target_gene": "Target gene symbol",
                "confidence": "DoRothEA confidence level (A-E)",
                "mode_of_regulation": "Mode of regulation (activation/repression)",
                "mor_score": "Mode of regulation score (1/-1)",
                "relationship": "Relationship type (transcriptionFactorInteractsWithGene)",
                "source": "Data source (DoRothEA)"
            }
        }
