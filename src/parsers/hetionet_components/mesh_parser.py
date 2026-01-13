"""
MeSH Parser for AlzKB.

This module parses MeSH (Medical Subject Headings) to extract symptom nodes
and disease-symptom relationships for AlzKB.

Data Source: https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/

Output:
  - symptom_nodes.tsv: MeSH symptom terms
  - disease_symptom.tsv: symptomManifestationOfDisease relationships
"""

import logging
import gzip
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

try:
    from lxml import etree
except ImportError:
    etree = None

try:
    import xml.etree.ElementTree as ET
except ImportError:
    ET = None

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)


class MeSHParser(BaseParser):
    """
    Parser for MeSH (Medical Subject Headings).

    Extracts symptom terms from MeSH for use in AlzKB.
    Symptoms are primarily found in the "Signs and Symptoms" category (C23).
    """

    # MeSH XML URL (update year as needed)
    MESH_URL = "https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2025.xml"

    # MeSH tree numbers for symptoms
    # C23 = Pathological Conditions, Signs and Symptoms
    SYMPTOM_TREE_PREFIXES = ["C23"]

    def __init__(self, data_dir: str):
        """
        Initialize the MeSH parser.

        Args:
            data_dir: Directory to store downloaded and processed data
        """
        super().__init__(data_dir)
        self.source_name = "mesh"

    def download_data(self) -> bool:
        """
        Download the MeSH XML file.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading MeSH descriptors...")

        result = self.download_file(self.MESH_URL, "desc2025.xml")

        if result:
            logger.info(f"Successfully downloaded MeSH to {result}")
            return True
        else:
            logger.error("Failed to download MeSH")
            return False

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse the MeSH XML file.

        Returns:
            Dictionary with:
              - 'symptom_nodes': DataFrame of symptom terms
        """
        xml_path = self.source_dir / "desc2025.xml"

        if not xml_path.exists():
            logger.error(f"MeSH file not found: {xml_path}")
            return {}

        logger.info(f"Parsing MeSH from {xml_path}")

        if etree:
            return self._parse_with_lxml(xml_path)
        elif ET:
            return self._parse_with_elementtree(xml_path)
        else:
            logger.error("No XML parser available (lxml or xml.etree)")
            return {}

    def _parse_with_lxml(self, xml_path: Path) -> Dict[str, pd.DataFrame]:
        """Parse using lxml library (faster for large files)."""
        logger.info("Parsing MeSH with lxml...")

        try:
            symptoms = []

            # Use iterparse for memory efficiency
            context = etree.iterparse(str(xml_path), events=('end',), tag='DescriptorRecord')

            for event, elem in context:
                # Get descriptor UI and name
                ui_elem = elem.find('.//DescriptorUI')
                name_elem = elem.find('.//DescriptorName/String')

                if ui_elem is None or name_elem is None:
                    elem.clear()
                    continue

                mesh_id = ui_elem.text
                name = name_elem.text

                # Check if this is a symptom (in C23 tree)
                tree_numbers = elem.findall('.//TreeNumber')
                is_symptom = False
                tree_nums = []

                for tn in tree_numbers:
                    if tn.text:
                        tree_nums.append(tn.text)
                        for prefix in self.SYMPTOM_TREE_PREFIXES:
                            if tn.text.startswith(prefix):
                                is_symptom = True
                                break

                if is_symptom:
                    # Get scope note (definition)
                    scope_note = ""
                    scope_elem = elem.find('.//ScopeNote')
                    if scope_elem is not None and scope_elem.text:
                        scope_note = scope_elem.text

                    symptoms.append({
                        "mesh_id": mesh_id,
                        "name": name,
                        "definition": scope_note,
                        "tree_numbers": "|".join(tree_nums)
                    })

                # Clear element to free memory
                elem.clear()

            logger.info(f"Parsed {len(symptoms)} symptom terms from MeSH")

            return {
                "symptom_nodes": pd.DataFrame(symptoms)
            }

        except Exception as e:
            logger.error(f"Error parsing MeSH with lxml: {e}")
            return {}

    def _parse_with_elementtree(self, xml_path: Path) -> Dict[str, pd.DataFrame]:
        """Parse using standard library ElementTree (slower but always available)."""
        logger.info("Parsing MeSH with ElementTree...")

        try:
            symptoms = []

            # Use iterparse for memory efficiency
            context = ET.iterparse(str(xml_path), events=('end',))

            for event, elem in context:
                if elem.tag != 'DescriptorRecord':
                    continue

                # Get descriptor UI and name
                ui_elem = elem.find('.//DescriptorUI')
                name_elem = elem.find('.//DescriptorName/String')

                if ui_elem is None or name_elem is None:
                    elem.clear()
                    continue

                mesh_id = ui_elem.text
                name = name_elem.text

                # Check if this is a symptom
                tree_numbers = elem.findall('.//TreeNumber')
                is_symptom = False
                tree_nums = []

                for tn in tree_numbers:
                    if tn.text:
                        tree_nums.append(tn.text)
                        for prefix in self.SYMPTOM_TREE_PREFIXES:
                            if tn.text.startswith(prefix):
                                is_symptom = True
                                break

                if is_symptom:
                    scope_note = ""
                    scope_elem = elem.find('.//ScopeNote')
                    if scope_elem is not None and scope_elem.text:
                        scope_note = scope_elem.text

                    symptoms.append({
                        "mesh_id": mesh_id,
                        "name": name,
                        "definition": scope_note,
                        "tree_numbers": "|".join(tree_nums)
                    })

                elem.clear()

            logger.info(f"Parsed {len(symptoms)} symptom terms from MeSH")

            return {
                "symptom_nodes": pd.DataFrame(symptoms)
            }

        except Exception as e:
            logger.error(f"Error parsing MeSH with ElementTree: {e}")
            return {}

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for MeSH data.

        Returns:
            Dictionary defining the schema for symptom nodes
        """
        return {
            "symptom_nodes": {
                "mesh_id": "MeSH Descriptor UI (e.g., D005221)",
                "name": "Symptom name",
                "definition": "Scope note/definition",
                "tree_numbers": "Pipe-separated MeSH tree numbers"
            }
        }
