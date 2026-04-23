"""
Uberon Anatomy Parser for the knowledge graph.

This module parses the Uberon anatomy ontology to extract anatomical structure
nodes (Anatomy) for the knowledge graph.

Data Sources:
  - Full Uberon: http://purl.obolibrary.org/obo/uberon.obo

Output:
  - anatomy_nodes.tsv: UBERON ID, name, definition (full ontology)
  - uberon_mesh_xrefs.tsv: UBERON ID, name, MeSH ID (from OBO xref entries)
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
    Extracts anatomy nodes and UBERON→MeSH xrefs from the OBO file.
    """

    # Full Uberon OBO URL
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
        """Download the full Uberon OBO file."""
        logger.info("Downloading Uberon ontology files...")
        obo_result = self.download_file(self.UBERON_URL, "uberon.obo")
        if not obo_result:
            logger.error("Failed to download Uberon OBO file")
            return False
        logger.info(f"Successfully downloaded Uberon OBO to {obo_result}")
        return True

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse Uberon OBO file.

        Returns:
            Dictionary with:
              - 'anatomy_nodes': DataFrame of all anatomical concepts
              - 'uberon_mesh_xrefs': DataFrame of UBERON→MeSH xref pairs
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
            mesh_xref_rows = []

            for node_id, node_data in graph.nodes(data=True):
                if not node_id.startswith("UBERON:"):
                    continue
                if node_data.get("is_obsolete", False):
                    continue

                name = node_data.get("name", "")
                anatomy_terms.append({
                    "uberon_id": node_id,
                    "name": name,
                    "definition": self._clean_definition(node_data.get("def", "")),
                    "synonyms": "|".join(node_data.get("synonym", [])),
                })

                for xref in node_data.get("xref", []):
                    if xref.startswith("MESH:"):
                        mesh_xref_rows.append({
                            "uberon_id": node_id,
                            "uberon_name": name,
                            "mesh_id": xref.split(":", 1)[1],
                        })

            logger.info(f"Parsed {len(anatomy_terms)} Uberon anatomy terms")
            logger.info(f"Extracted {len(mesh_xref_rows)} UBERON→MeSH xref pairs")

            return {
                "anatomy_nodes": pd.DataFrame(anatomy_terms),
                "uberon_mesh_xrefs": pd.DataFrame(mesh_xref_rows),
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
            mesh_xref_rows = []

            for term in ontology.terms():
                if not term.id.startswith("UBERON:"):
                    continue
                if term.obsolete:
                    continue

                name = term.name or ""
                anatomy_terms.append({
                    "uberon_id": term.id,
                    "name": name,
                    "definition": str(term.definition) if term.definition else "",
                    "synonyms": "|".join(str(s) for s in term.synonyms),
                })

                for xref in term.xrefs:
                    xref_id = str(xref.id)
                    if xref_id.startswith("MESH:"):
                        mesh_xref_rows.append({
                            "uberon_id": term.id,
                            "uberon_name": name,
                            "mesh_id": xref_id.split(":", 1)[1],
                        })

            logger.info(f"Parsed {len(anatomy_terms)} Uberon anatomy terms")
            logger.info(f"Extracted {len(mesh_xref_rows)} UBERON→MeSH xref pairs")

            return {
                "anatomy_nodes": pd.DataFrame(anatomy_terms),
                "uberon_mesh_xrefs": pd.DataFrame(mesh_xref_rows),
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
        return {
            "anatomy_nodes": {
                "uberon_id": "Uberon ID (e.g., UBERON:0000955)",
                "name": "Anatomical structure name",
                "definition": "Structure definition",
                "synonyms": "Pipe-separated list of synonyms",
            },
            "uberon_mesh_xrefs": {
                "uberon_id": "Uberon ID",
                "uberon_name": "Anatomical structure name",
                "mesh_id": "MeSH descriptor ID",
            },
        }
