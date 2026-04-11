"""
Disease Ontology Parser for the knowledge graph.

This module parses the Disease Ontology (DO) to extract disease nodes
and disease-anatomy relationships for the knowledge graph.

Data Sources:
  - Full DO: https://github.com/DiseaseOntology/HumanDiseaseOntology
  - DO Slim: https://github.com/dhimmel/disease-ontology (137 curated diseases for Hetionet)

Output:
  - disease_nodes.tsv: DOID, name, definition, xrefs (full DO)
  - slim_terms.tsv: DOID, name, source, pathophysiology (137 Hetionet diseases)
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


class DiseaseOntologyParser(BaseParser):
    """
    Parser for the Disease Ontology (DO).

    Extracts disease concepts from the Disease Ontology OBO file.
    """

    # Disease Ontology OBO URL (full ontology)
    DO_URL = "https://raw.githubusercontent.com/DiseaseOntology/HumanDiseaseOntology/main/src/ontology/doid.obo"

    # DO Slim terms from dhimmel/disease-ontology (137 curated diseases for Hetionet)
    # This is the curated subset used by Hetionet
    DO_SLIM_COMMIT = "72614ade9f1cc5a5317b8f6836e1e464b31d5587"
    DO_SLIM_URL = f"https://raw.githubusercontent.com/dhimmel/disease-ontology/{DO_SLIM_COMMIT}/data/slim-terms.tsv"

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
        Download Disease Ontology files.

        Downloads both the full OBO file and the curated slim terms file
        used by Hetionet.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading Disease Ontology files...")

        # Download full OBO file
        obo_result = self.download_file(self.DO_URL, "doid.obo")
        if not obo_result:
            logger.error("Failed to download Disease Ontology OBO file")
            return False
        logger.info(f"Successfully downloaded full Disease Ontology to {obo_result}")

        # Download slim terms (137 curated diseases for Hetionet)
        slim_result = self.download_file(self.DO_SLIM_URL, "slim-terms.tsv")
        if not slim_result:
            logger.warning("Failed to download DO slim terms - continuing without slim data")
        else:
            logger.info(f"Successfully downloaded DO slim terms to {slim_result}")

        return True

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse Disease Ontology files.

        Returns:
            Dictionary with:
              - 'disease_nodes': DataFrame of all disease concepts (full DO)
              - 'slim_terms': DataFrame of 137 curated diseases (Hetionet subset)
              - 'disease_anatomy': DataFrame of disease-anatomy relationships
        """
        result = {}

        # Parse slim terms first (this is what Hetionet uses)
        slim_path = self.source_dir / "slim-terms.tsv"
        if slim_path.exists():
            slim_df = self._parse_slim_terms(slim_path)
            if slim_df is not None:
                result["slim_terms"] = slim_df
        else:
            logger.warning(f"DO slim terms file not found: {slim_path}")

        # Parse full OBO file
        obo_path = self.source_dir / "doid.obo"
        if obo_path.exists():
            logger.info(f"Parsing Disease Ontology from {obo_path}")

            # Try obonet first, then pronto
            if obonet:
                obo_result = self._parse_with_obonet(obo_path)
            elif pronto:
                obo_result = self._parse_with_pronto(obo_path)
            else:
                logger.error("Neither obonet nor pronto is installed. Cannot parse OBO file.")
                obo_result = {}

            result.update(obo_result)
        else:
            logger.error(f"Disease Ontology file not found: {obo_path}")

        return result

    def _parse_slim_terms(self, slim_path: Path) -> Optional[pd.DataFrame]:
        """
        Parse DO slim terms file.

        Args:
            slim_path: Path to slim-terms.tsv

        Returns:
            DataFrame with slim disease terms
        """
        logger.info(f"Parsing DO slim terms from {slim_path}")

        try:
            df = pd.read_csv(slim_path, sep='\t')

            # Expected columns: doid, name, source, pathophysiology
            logger.info(f"Parsed {len(df)} slim disease terms")

            # Add metadata columns
            df['license'] = 'CC BY 3.0'
            df['sourceDatabase'] = 'Disease Ontology'

            return df

        except Exception as e:
            logger.error(f"Error parsing DO slim terms: {e}")
            return None

    def _parse_with_obonet(self, obo_path: Path) -> Dict[str, pd.DataFrame]:
        """Parse using obonet library."""
        logger.info("Parsing with obonet...")

        if not Path(obo_path).exists():
            logger.error(f"Disease Ontology file not found: {obo_path}")
            return {}

        try:
            graph = obonet.read_obo(str(obo_path))

            # Extract disease nodes
            diseases = []
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

            logger.info(f"Parsed {len(diseases)} disease terms")

            result = {
                "disease_nodes": pd.DataFrame(diseases),
            }

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

            logger.info(f"Parsed {len(diseases)} disease terms")

            result = {
                "disease_nodes": pd.DataFrame(diseases),
            }

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

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for Disease Ontology data.

        Returns:
            Dictionary defining the schema for disease nodes and relationships
        """
        return {
            "slim_terms": {
                "doid": "Disease Ontology ID (e.g., DOID:10652)",
                "name": "Disease name",
                "source": "Slim source (DOcancerslim, etc.)",
                "pathophysiology": "Disease pathophysiology category",
                "license": "License (CC BY 3.0)",
                "sourceDatabase": "Source database (Disease Ontology)"
            },
            "disease_nodes": {
                "doid": "Disease Ontology ID (e.g., DOID:10652)",
                "name": "Disease name",
                "definition": "Disease definition",
                "synonyms": "Pipe-separated list of synonyms"
            },
            "disease_xrefs": {
                "doid": "Disease Ontology ID",
                "xref": "Cross-reference to external database"
            }
        }
