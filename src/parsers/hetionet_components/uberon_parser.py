"""
Uberon Anatomy Parser for AlzKB.

This module parses the Uberon anatomy ontology to extract anatomical structure
nodes (BodyPart) for AlzKB.

Data Source: http://purl.obolibrary.org/obo/uberon.obo

Output:
  - anatomy_nodes.tsv: UBERON ID, name, definition
"""

import logging
from pathlib import Path
from typing import Dict
import pandas as pd

try:
    import obonet
except ImportError:
    obonet = None

try:
    import pronto
except ImportError:
    pronto = None

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)


class UberonParser(BaseParser):
    """
    Parser for the Uberon anatomy ontology.

    Extracts anatomical structure concepts for use as BodyPart nodes in AlzKB.
    """

    # Uberon OBO URL
    UBERON_URL = "http://purl.obolibrary.org/obo/uberon.obo"

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
        Download the Uberon OBO file.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading Uberon ontology...")

        result = self.download_file(self.UBERON_URL, "uberon.obo")

        if result:
            logger.info(f"Successfully downloaded Uberon to {result}")
            return True
        else:
            logger.error("Failed to download Uberon")
            return False

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse the Uberon OBO file.

        Returns:
            Dictionary with:
              - 'anatomy_nodes': DataFrame of anatomical structure concepts
        """
        obo_path = self.source_dir / "uberon.obo"

        if not obo_path.exists():
            logger.error(f"Uberon file not found: {obo_path}")
            return {}

        logger.info(f"Parsing Uberon from {obo_path}")

        if obonet:
            return self._parse_with_obonet(obo_path)
        elif pronto:
            return self._parse_with_pronto(obo_path)
        else:
            logger.error("Neither obonet nor pronto is installed")
            return {}

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
            "anatomy_nodes": {
                "uberon_id": "Uberon ID (e.g., UBERON:0000955)",
                "name": "Anatomical structure name",
                "definition": "Structure definition",
                "synonyms": "Pipe-separated list of synonyms"
            }
        }
