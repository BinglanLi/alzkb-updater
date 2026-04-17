"""
MeSH Parser for the knowledge graph.

Parses MeSH (Medical Subject Headings) to extract Symptom nodes
from the Signs and Symptoms subtree (MeSH tree C23.888).

Data Source:
  - MeSH XML: https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/

Output:
  - symptom_nodes.tsv: MeSH Signs and Symptoms descriptors (C23.888 subtree)
    Columns: mesh_id, mesh_name, sourceDatabase
"""

import logging
from pathlib import Path
from typing import Dict

import pandas as pd
from lxml import etree

from .base_parser import BaseParser

logger = logging.getLogger(__name__)

# Update MESH_YEAR each January when NLM publishes the new release
MESH_YEAR = 2026
MESH_URL = f"https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc{MESH_YEAR}.xml"
MESH_XML_FILENAME = MESH_URL.rsplit("/", 1)[-1]   # derived; do not edit separately

# Signs and Symptoms subtree root: D012816, tree number C23.888.
# Trailing dot excludes the root node itself.
SYMPTOM_TREE_PREFIX = "C23.888."


class MeSHParser(BaseParser):
    """Parser for MeSH Signs and Symptoms descriptors (C23.888 subtree)."""

    def __init__(self, data_dir: str):
        super().__init__(data_dir)

    def download_data(self) -> bool:
        """Download MeSH XML. Returns True if successful."""
        logger.info("Downloading MeSH XML...")
        result = self.download_file(MESH_URL, MESH_XML_FILENAME)
        if not result:
            logger.error("Failed to download MeSH XML")
            return False
        logger.info(f"Downloaded MeSH XML to {result}")
        return True

    def _parse_xml(self, xml_path: Path) -> list:
        """Parse MeSH XML into a list of descriptor dicts.

        Returns list of {'mesh_id': str, 'mesh_name': str, 'tree_numbers': list[str]}.
        tree_numbers is used internally for filtering; it is not written to output.
        """
        descriptors = []
        context = etree.iterparse(str(xml_path), events=('end',), tag='DescriptorRecord')
        for _, elem in context:
            ui = elem.findtext('.//DescriptorUI')
            name = elem.findtext('.//DescriptorName/String')
            if ui and name:
                tree_numbers = [tn.text for tn in elem.findall('.//TreeNumber') if tn.text]
                descriptors.append({'mesh_id': ui, 'mesh_name': name, 'tree_numbers': tree_numbers})
            elem.clear()
        logger.info(f"Parsed {len(descriptors)} MeSH descriptors")
        return descriptors

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """Parse MeSH XML and return symptom nodes.

        Returns:
            {'symptom_nodes': DataFrame with columns mesh_id, mesh_name, sourceDatabase}
        """
        xml_path = self.source_dir / MESH_XML_FILENAME
        if not xml_path.exists():
            logger.error(f"MeSH XML not found: {xml_path}")
            return {}

        all_terms = self._parse_xml(xml_path)

        # Filter to C23.888 subtree (Signs and Symptoms descendants).
        # Trailing dot in SYMPTOM_TREE_PREFIX excludes the root D012816 itself.
        symptom_terms = [
            t for t in all_terms
            if any(tn.startswith(SYMPTOM_TREE_PREFIX) for tn in t['tree_numbers'])
        ]

        logger.info(f"Extracted {len(symptom_terms)} symptom terms from C23.888 subtree")
        if len(symptom_terms) < 400:
            logger.warning(
                f"Unexpectedly few symptom terms: {len(symptom_terms)} (expected ≥400)"
            )

        symptom_df = pd.DataFrame([
            {'mesh_id': t['mesh_id'], 'mesh_name': t['mesh_name'], 'sourceDatabase': 'MeSH'}
            for t in symptom_terms
        ])

        return {'symptom_nodes': symptom_df}

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        return {
            "symptom_nodes": {
                "mesh_id": "MeSH Descriptor UI (e.g., D005221)",
                "mesh_name": "Symptom name",
                "sourceDatabase": "Source database (MeSH)",
            }
        }
