"""
Uberon Anatomy Parser for the knowledge graph.

This module parses the Uberon anatomy ontology to extract anatomical structure
nodes (Anatomy) for the knowledge graph.

Data Sources:
  - Full Uberon: http://purl.obolibrary.org/obo/uberon.obo
  - Hetio Slim: https://github.com/dhimmel/uberon (652 anatomies with MeSH xrefs)

Output:
  - anatomy_nodes.tsv: UBERON ID, name, definition (full ontology)
  - hetio_slim.tsv: UBERON ID, name, MeSH ID, BTO ID (652 Hetionet anatomies)
"""

import logging
from pathlib import Path
from typing import Dict, Optional
import pandas as pd

try:
    import obonet
except ImportError:
    obonet = None

try:
    import pronto
except ImportError:
    pronto = None

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class UberonParser(BaseParser):
    """
    Parser for the Uberon anatomy ontology.

    Extracts anatomical structure concepts for use as Anatomy nodes in the knowledge graph.
    Includes the hetio-slim subset with MeSH cross-references.
    """

    # Full Uberon OBO URL
    UBERON_URL = "http://purl.obolibrary.org/obo/uberon.obo"

    # Hetio slim from dhimmel/uberon (652 anatomies used in Hetionet)
    UBERON_SLIM_COMMIT = "75ad89d529ac88c25fc52add2f5b5f6dbb8edb17"
    UBERON_SLIM_URL = f"https://raw.githubusercontent.com/dhimmel/uberon/{UBERON_SLIM_COMMIT}/data/hetio-slim.tsv"

    def __init__(self, data_dir: str):
        """
        Initialize the Uberon parser.

        Args:
            data_dir: Directory to store downloaded and processed data
        """
        super().__init__(data_dir)
        self.source_name = "uberon"

    def download_data(self) -> bool:
        """
        Download Uberon files.

        Downloads both the full OBO file and the hetio-slim file
        used by Hetionet.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading Uberon ontology files...")

        # Download full OBO file
        obo_result = self.download_file(self.UBERON_URL, "uberon.obo")
        if not obo_result:
            logger.error("Failed to download Uberon OBO file")
            return False
        logger.info(f"Successfully downloaded Uberon OBO to {obo_result}")

        # Download hetio-slim (652 anatomies with MeSH xrefs)
        slim_result = self.download_file(self.UBERON_SLIM_URL, "hetio-slim.tsv")
        if not slim_result:
            logger.warning("Failed to download Uberon hetio-slim - continuing without slim data")
        else:
            logger.info(f"Successfully downloaded Uberon hetio-slim to {slim_result}")

        return True

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse Uberon files.

        Returns:
            Dictionary with:
              - 'anatomy_nodes': DataFrame of all anatomical concepts (full Uberon)
              - 'hetio_slim': DataFrame of 652 anatomies (Hetionet subset with MeSH xrefs)
        """
        result = {}

        # Parse hetio-slim first (this is what Hetionet uses)
        slim_path = self.source_dir / "hetio-slim.tsv"
        if slim_path.exists():
            slim_df = self._parse_hetio_slim(slim_path)
            if slim_df is not None:
                result["hetio_slim"] = slim_df
        else:
            logger.warning(f"Uberon hetio-slim file not found: {slim_path}")

        # Parse full OBO file
        obo_path = self.source_dir / "uberon.obo"
        if obo_path.exists():
            logger.info(f"Parsing Uberon from {obo_path}")

            if obonet:
                obo_result = self._parse_with_obonet(obo_path)
            elif pronto:
                obo_result = self._parse_with_pronto(obo_path)
            else:
                logger.error("Neither obonet nor pronto is installed")
                obo_result = {}

            result.update(obo_result)
        else:
            logger.error(f"Uberon file not found: {obo_path}")

        return result

    def _parse_hetio_slim(self, slim_path: Path) -> Optional[pd.DataFrame]:
        """
        Parse Uberon hetio-slim file.

        Args:
            slim_path: Path to hetio-slim.tsv

        Returns:
            DataFrame with slim anatomy terms and MeSH cross-references
        """
        logger.info(f"Parsing Uberon hetio-slim from {slim_path}")

        try:
            df = pd.read_csv(slim_path, sep='\t')

            # Expected columns: uberon_id, uberon_name, mesh_id, mesh_name, bto_id
            logger.info(f"Parsed {len(df)} hetio-slim anatomy terms")

            # Add metadata columns
            df['license'] = 'CC BY 3.0'
            df['source'] = 'Uberon'
            df['sourceDatabase'] = 'Uberon'

            return df

        except Exception as e:
            logger.error(f"Error parsing Uberon hetio-slim: {e}")
            return None

    def _parse_with_obonet(self, obo_path: Path) -> Dict[str, pd.DataFrame]:
        """Parse using obonet library."""
        logger.info("Parsing Uberon with obonet...")

        try:
            graph = obonet.read_obo(str(obo_path))

            anatomy_terms = []

            for node_id, node_data in graph.nodes(data=True):
                if not node_id.startswith("UBERON:"):
                    continue

                if node_data.get("is_obsolete", False):
                    continue

                term = {
                    "uberon_id": node_id,
                    "name": node_data.get("name", ""),
                    "definition": self._clean_definition(node_data.get("def", "")),
                    "synonyms": "|".join(node_data.get("synonym", []))
                }
                anatomy_terms.append(term)

            logger.info(f"Parsed {len(anatomy_terms)} Uberon anatomy terms")

            return {
                "anatomy_nodes": pd.DataFrame(anatomy_terms)
            }

        except Exception as e:
            logger.error(f"Error parsing Uberon with obonet: {e}")
            return {}

    def _parse_with_pronto(self, obo_path: Path) -> Dict[str, pd.DataFrame]:
        """Parse using pronto library."""
        logger.info("Parsing Uberon with pronto...")

        try:
            ontology = pronto.Ontology(str(obo_path))

            anatomy_terms = []

            for term in ontology.terms():
                if not term.id.startswith("UBERON:"):
                    continue

                if term.obsolete:
                    continue

                term_data = {
                    "uberon_id": term.id,
                    "name": term.name or "",
                    "definition": str(term.definition) if term.definition else "",
                    "synonyms": "|".join(str(s) for s in term.synonyms)
                }
                anatomy_terms.append(term_data)

            logger.info(f"Parsed {len(anatomy_terms)} Uberon anatomy terms")

            return {
                "anatomy_nodes": pd.DataFrame(anatomy_terms)
            }

        except Exception as e:
            logger.error(f"Error parsing Uberon with pronto: {e}")
            return {}

    def _clean_definition(self, definition: str) -> str:
        """Clean up definition string from OBO format."""
        if not definition:
            return ""
        definition = definition.strip('"')
        if " [" in definition:
            definition = definition.split(" [")[0]
        return definition

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for Uberon data.

        Returns:
            Dictionary defining the schema for anatomy nodes
        """
        return {
            "hetio_slim": {
                "uberon_id": "Uberon ID (e.g., UBERON:0000955)",
                "uberon_name": "Anatomical structure name",
                "mesh_id": "MeSH descriptor ID",
                "mesh_name": "MeSH descriptor name",
                "bto_id": "BRENDA Tissue Ontology ID",
                "license": "License (CC BY 3.0)",
                "source": "Data source (Uberon)",
                "sourceDatabase": "Source database (Uberon)"
            },
            "anatomy_nodes": {
                "uberon_id": "Uberon ID (e.g., UBERON:0000955)",
                "name": "Anatomical structure name",
                "definition": "Structure definition",
                "synonyms": "Pipe-separated list of synonyms"
            }
        }
