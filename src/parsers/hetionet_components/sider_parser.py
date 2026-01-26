"""
SIDER Parser for AlzKB.

This module parses SIDER (Side Effect Resource) data to extract:
- Side Effect nodes (UMLS CUI identifiers)
- Compound-causes-Side Effect (CcSE) edges

Data Source: https://github.com/dhimmel/SIDER4
Commit: be3adebc0d845baaddb907a880890cb5e85f5801

Output:
  - side_effect_nodes.tsv: UMLS CUI, name, source, url, license
  - compound_causes_side_effect.tsv: drugbank_id, umls_cui, source, unbiased, url, license
"""

import logging
from pathlib import Path
from typing import Dict
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)


class SIDERParser(BaseParser):
    """
    Parser for SIDER (Side Effect Resource) database.

    Extracts drug side effect information from SIDER via the dhimmel/SIDER4
    GitHub repository, which provides pre-processed data with DrugBank IDs.
    """

    # SIDER4 data from dhimmel GitHub repo
    SIDER_COMMIT = "be3adebc0d845baaddb907a880890cb5e85f5801"
    SIDER_BASE_URL = f"https://raw.githubusercontent.com/dhimmel/SIDER4/{SIDER_COMMIT}/data"

    # File URLs
    SIDE_EFFECT_TERMS_URL = f"{SIDER_BASE_URL}/side-effect-terms.tsv"
    SIDE_EFFECTS_URL = f"{SIDER_BASE_URL}/side-effects.tsv"

    def __init__(self, data_dir: str):
        """
        Initialize the SIDER parser.

        Args:
            data_dir: Directory to store downloaded and processed data
        """
        super().__init__(data_dir)
        self.source_name = "sider"

    def download_data(self) -> bool:
        """
        Download SIDER data files from dhimmel/SIDER4 GitHub repo.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading SIDER data...")

        # Download side effect terms (nodes)
        terms_result = self.download_file(self.SIDE_EFFECT_TERMS_URL, "side-effect-terms.tsv")
        if not terms_result:
            logger.error("Failed to download side-effect-terms.tsv")
            return False

        # Download side effects relationships (edges)
        effects_result = self.download_file(self.SIDE_EFFECTS_URL, "side-effects.tsv")
        if not effects_result:
            logger.error("Failed to download side-effects.tsv")
            return False

        logger.info("Successfully downloaded SIDER data files")
        return True

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse the SIDER data files.

        Returns:
            Dictionary with:
              - 'side_effect_nodes': DataFrame of Side Effect nodes
              - 'compound_causes_side_effect': DataFrame of CcSE edges
        """
        result = {}

        # Parse side effect terms (nodes)
        terms_path = self.source_dir / "side-effect-terms.tsv"
        if terms_path.exists():
            side_effect_nodes = self._parse_side_effect_nodes(terms_path)
            if side_effect_nodes is not None:
                result["side_effect_nodes"] = side_effect_nodes
        else:
            logger.error(f"Side effect terms file not found: {terms_path}")

        # Parse side effects relationships (edges)
        effects_path = self.source_dir / "side-effects.tsv"
        if effects_path.exists():
            ccse_edges = self._parse_compound_causes_side_effect(effects_path)
            if ccse_edges is not None:
                result["compound_causes_side_effect"] = ccse_edges
        else:
            logger.error(f"Side effects file not found: {effects_path}")

        return result

    def _parse_side_effect_nodes(self, terms_path: Path) -> pd.DataFrame:
        """
        Parse side effect terms to create Side Effect nodes.

        Args:
            terms_path: Path to side-effect-terms.tsv

        Returns:
            DataFrame with Side Effect node data
        """
        logger.info(f"Parsing side effect terms from {terms_path}")

        try:
            df = pd.read_csv(terms_path, sep='\t')

            # Expected columns: umls_cui_from_meddra, side_effect_name
            if 'umls_cui_from_meddra' not in df.columns:
                logger.error("Missing required column: umls_cui_from_meddra")
                return None

            # Create node DataFrame with required fields
            nodes = pd.DataFrame({
                'umls_cui': df['umls_cui_from_meddra'],
                'name': df['side_effect_name'],
                'source': 'UMLS via SIDER 4.1',
                'url': df['umls_cui_from_meddra'].apply(
                    lambda x: f'http://identifiers.org/umls/{x}'
                ),
                'license': 'CC BY-NC-SA 4.0',
                'sourceDatabase': 'SIDER'
            })

            # Remove duplicates
            nodes = nodes.drop_duplicates(subset=['umls_cui'])

            logger.info(f"Parsed {len(nodes)} Side Effect nodes")
            return nodes

        except Exception as e:
            logger.error(f"Error parsing side effect terms: {e}")
            return None

    def _parse_compound_causes_side_effect(self, effects_path: Path) -> pd.DataFrame:
        """
        Parse side effects to create Compound-causes-Side Effect edges.

        Args:
            effects_path: Path to side-effects.tsv

        Returns:
            DataFrame with CcSE edge data
        """
        logger.info(f"Parsing compound-side effect relationships from {effects_path}")

        try:
            df = pd.read_csv(effects_path, sep='\t')

            # Expected columns: drugbank_id, drugbank_name, umls_cui_from_meddra, side_effect_name
            required_cols = ['drugbank_id', 'umls_cui_from_meddra']
            for col in required_cols:
                if col not in df.columns:
                    logger.error(f"Missing required column: {col}")
                    return None

            # Create edge DataFrame
            edges = pd.DataFrame({
                'drugbank_id': df['drugbank_id'],
                'umls_cui': df['umls_cui_from_meddra'],
                'source': 'SIDER 4.1',
                'url': df['umls_cui_from_meddra'].apply(
                    lambda x: f'http://sideeffects.embl.de/se/{x}/'
                ),
                'unbiased': False,
                'license': 'CC BY-NC-SA 4.0',
                'sourceDatabase': 'SIDER'
            })

            # Remove duplicates (same compound-side effect pair)
            edges = edges.drop_duplicates(subset=['drugbank_id', 'umls_cui'])

            logger.info(f"Parsed {len(edges)} Compound-causes-Side Effect edges")
            return edges

        except Exception as e:
            logger.error(f"Error parsing side effects: {e}")
            return None

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for SIDER data.

        Returns:
            Dictionary defining the schema for Side Effect nodes and CcSE edges
        """
        return {
            "side_effect_nodes": {
                "umls_cui": "UMLS Concept Unique Identifier (e.g., C0000001)",
                "name": "Side effect name",
                "source": "Data source description",
                "url": "URL to UMLS identifier",
                "license": "License (CC BY-NC-SA 4.0)",
                "sourceDatabase": "Source database name (SIDER)"
            },
            "compound_causes_side_effect": {
                "drugbank_id": "DrugBank ID of compound",
                "umls_cui": "UMLS CUI of side effect",
                "source": "Data source (SIDER 4.1)",
                "url": "URL to SIDER side effect page",
                "unbiased": "Whether edge is unbiased (False for SIDER)",
                "license": "License (CC BY-NC-SA 4.0)",
                "sourceDatabase": "Source database name (SIDER)"
            }
        }
