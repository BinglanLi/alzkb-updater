"""
Disease Ontology Parser for AlzKB.

This module parses the Disease Ontology (DO) to extract disease nodes
and disease-anatomy relationships for AlzKB.

Data Source: https://github.com/DiseaseOntology/HumanDiseaseOntology
Output:
  - disease_nodes.tsv: DOID, name, definition, xrefs
  - disease_anatomy.tsv: disease_id, anatomy_id (diseaseLocalizesToAnatomy)
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

from ..base_parser import BaseParser

logger = logging.getLogger(__name__)


class DiseaseOntologyParser(BaseParser):
    """
    Parser for the Disease Ontology (DO).

    Extracts disease concepts and their relationships to anatomy
    from the Disease Ontology OBO file.
    """

    # Disease Ontology OBO URL
    DO_URL = "https://raw.githubusercontent.com/DiseaseOntology/HumanDiseaseOntology/main/src/ontology/doid.obo"

    def __init__(self, data_dir: str):
        """
        Initialize the Disease Ontology parser.

        Args:
            data_dir: Directory to store downloaded and processed data
        """
        super().__init__(data_dir)
        self.source_name = "disease_ontology"

    def download_data(self) -> bool:
        """
        Download the Disease Ontology OBO file.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading Disease Ontology...")

        result = self.download_file(self.DO_URL, "doid.obo")

        if result:
            logger.info(f"Successfully downloaded Disease Ontology to {result}")
            return True
        else:
            logger.error("Failed to download Disease Ontology")
            return False

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse the Disease Ontology OBO file.

        Returns:
            Dictionary with:
              - 'disease_nodes': DataFrame of disease concepts
              - 'disease_anatomy': DataFrame of disease-anatomy relationships
        """
        obo_path = self.source_dir / "doid.obo"

        if not obo_path.exists():
            logger.error(f"Disease Ontology file not found: {obo_path}")
            return {}

        logger.info(f"Parsing Disease Ontology from {obo_path}")

        # Try obonet first, then pronto
        if obonet:
            return self._parse_with_obonet(obo_path)
        elif pronto:
            return self._parse_with_pronto(obo_path)
        else:
            logger.error("Neither obonet nor pronto is installed. Cannot parse OBO file.")
            return {}

    def _parse_with_obonet(self, obo_path: Path) -> Dict[str, pd.DataFrame]:
        """Parse using obonet library."""
        logger.info("Parsing with obonet...")

        try:
            graph = obonet.read_obo(str(obo_path))

            # Extract disease nodes
            diseases = []
            disease_anatomy = []
            disease_xrefs = []

            for node_id, node_data in graph.nodes(data=True):
                if not node_id.startswith("DOID:"):
                    continue

                # Skip obsolete terms
                if node_data.get("is_obsolete", False):
                    continue

                # Extract basic information
                disease = {
                    "doid": node_id,
                    "name": node_data.get("name", ""),
                    "definition": self._clean_definition(node_data.get("def", "")),
                    "synonyms": "|".join(node_data.get("synonym", [])),
                }
                diseases.append(disease)

                # Extract cross-references
                for xref in node_data.get("xref", []):
                    disease_xrefs.append({
                        "doid": node_id,
                        "xref": xref
                    })

                # Extract anatomy relationships (diseaseLocalizesToAnatomy)
                # Look for relationships to UBERON terms
                for rel_type, targets in node_data.items():
                    if rel_type in ["relationship", "intersection_of"]:
                        if isinstance(targets, list):
                            for target in targets:
                                if "UBERON:" in str(target):
                                    uberon_id = self._extract_uberon_id(target)
                                    if uberon_id:
                                        disease_anatomy.append({
                                            "disease_id": node_id,
                                            "anatomy_id": uberon_id,
                                            "relationship": "diseaseLocalizesToAnatomy"
                                        })

            logger.info(f"Parsed {len(diseases)} disease terms")
            logger.info(f"Found {len(disease_anatomy)} disease-anatomy relationships")

            result = {
                "disease_nodes": pd.DataFrame(diseases),
            }

            if disease_anatomy:
                result["disease_anatomy"] = pd.DataFrame(disease_anatomy)

            if disease_xrefs:
                result["disease_xrefs"] = pd.DataFrame(disease_xrefs)

            return result

        except Exception as e:
            logger.error(f"Error parsing with obonet: {e}")
            return {}

    def _parse_with_pronto(self, obo_path: Path) -> Dict[str, pd.DataFrame]:
        """Parse using pronto library."""
        logger.info("Parsing with pronto...")

        try:
            ontology = pronto.Ontology(str(obo_path))

            diseases = []
            disease_anatomy = []
            disease_xrefs = []

            for term in ontology.terms():
                if not term.id.startswith("DOID:"):
                    continue

                if term.obsolete:
                    continue

                disease = {
                    "doid": term.id,
                    "name": term.name or "",
                    "definition": term.definition or "",
                    "synonyms": "|".join(str(s) for s in term.synonyms),
                }
                diseases.append(disease)

                # Extract cross-references
                for xref in term.xrefs:
                    disease_xrefs.append({
                        "doid": term.id,
                        "xref": str(xref)
                    })

                # Extract relationships to anatomy
                for rel in term.relationships:
                    for target in term.relationships[rel]:
                        if target.id.startswith("UBERON:"):
                            disease_anatomy.append({
                                "disease_id": term.id,
                                "anatomy_id": target.id,
                                "relationship": "diseaseLocalizesToAnatomy"
                            })

            logger.info(f"Parsed {len(diseases)} disease terms")
            logger.info(f"Found {len(disease_anatomy)} disease-anatomy relationships")

            result = {
                "disease_nodes": pd.DataFrame(diseases),
            }

            if disease_anatomy:
                result["disease_anatomy"] = pd.DataFrame(disease_anatomy)

            if disease_xrefs:
                result["disease_xrefs"] = pd.DataFrame(disease_xrefs)

            return result

        except Exception as e:
            logger.error(f"Error parsing with pronto: {e}")
            return {}

    def _clean_definition(self, definition: str) -> str:
        """Clean up definition string from OBO format."""
        if not definition:
            return ""
        # Remove quotes and trailing references
        definition = definition.strip('"')
        if " [" in definition:
            definition = definition.split(" [")[0]
        return definition

    def _extract_uberon_id(self, text: str) -> Optional[str]:
        """Extract UBERON ID from relationship text."""
        import re
        match = re.search(r'(UBERON:\d+)', str(text))
        if match:
            return match.group(1)
        return None

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for Disease Ontology data.

        Returns:
            Dictionary defining the schema for disease nodes and relationships
        """
        return {
            "disease_nodes": {
                "doid": "Disease Ontology ID (e.g., DOID:10652)",
                "name": "Disease name",
                "definition": "Disease definition",
                "synonyms": "Pipe-separated list of synonyms"
            },
            "disease_anatomy": {
                "disease_id": "Disease Ontology ID",
                "anatomy_id": "UBERON anatomy ID",
                "relationship": "Relationship type (diseaseLocalizesToAnatomy)"
            },
            "disease_xrefs": {
                "doid": "Disease Ontology ID",
                "xref": "Cross-reference to external database"
            }
        }
