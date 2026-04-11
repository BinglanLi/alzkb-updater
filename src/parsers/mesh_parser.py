"""
MeSH Parser for the knowledge graph.

This module parses MeSH (Medical Subject Headings) to extract symptom nodes
and disease-symptom relationships for the knowledge graph.

Data Sources:
  - Full MeSH: https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/
  - Hetionet Symptoms: https://github.com/dhimmel/mesh (505 symptoms with HSDN flag)

Output:
  - symptom_nodes.tsv: MeSH symptom terms (from full XML)
  - hetio_symptoms.tsv: 505 symptoms used in Hetionet with in_hsdn flag
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

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class MeSHParser(BaseParser):
    """
    Parser for MeSH (Medical Subject Headings).

    Extracts symptom terms from MeSH for use in the knowledge graph.
    Includes the Hetionet symptom subset with HSDN (Human Symptom Disease Network) flag.
    """

    # Full MeSH XML URL (update year as needed)
    MESH_URL = "https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2025.xml"

    # Hetionet symptoms from dhimmel/mesh (505 symptoms with HSDN flag)
    MESH_SYMPTOMS_COMMIT = "1d771be97ddaa1dd9c21adc89d1002b6f4a62a25"
    MESH_SYMPTOMS_URL = f"https://raw.githubusercontent.com/dhimmel/mesh/{MESH_SYMPTOMS_COMMIT}/data/symptoms.tsv"

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
        Download MeSH files.

        Downloads both the full MeSH XML and the Hetionet symptoms file.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading MeSH files...")

        # Download Hetionet symptoms first (this is what Hetionet uses)
        symptoms_result = self.download_file(self.MESH_SYMPTOMS_URL, "symptoms.tsv")
        if not symptoms_result:
            logger.warning("Failed to download Hetionet symptoms file")
        else:
            logger.info(f"Successfully downloaded Hetionet symptoms to {symptoms_result}")

        # Download full MeSH XML (optional, for extended parsing)
        xml_result = self.download_file(self.MESH_URL, "desc2025.xml")
        if not xml_result:
            logger.warning("Failed to download full MeSH XML - continuing with Hetionet symptoms only")
        else:
            logger.info(f"Successfully downloaded MeSH XML to {xml_result}")

        # Success if at least the symptoms file was downloaded
        return symptoms_result is not None

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse MeSH files.

        Returns:
            Dictionary with:
              - 'hetio_symptoms': DataFrame of 505 Hetionet symptoms with in_hsdn flag
              - 'symptom_nodes': DataFrame of all symptom terms (if XML available)
        """
        result = {}

        # Parse Hetionet symptoms first (this is what Hetionet uses)
        symptoms_path = self.source_dir / "symptoms.tsv"
        if symptoms_path.exists():
            symptoms_df = self._parse_hetio_symptoms(symptoms_path)
            if symptoms_df is not None:
                result["hetio_symptoms"] = symptoms_df
        else:
            logger.warning(f"Hetionet symptoms file not found: {symptoms_path}")

        # Parse full MeSH XML if available
        xml_path = self.source_dir / "desc2025.xml"
        if xml_path.exists():
            logger.info(f"Parsing MeSH from {xml_path}")

            if etree:
                xml_result = self._parse_with_lxml(xml_path)
            elif ET:
                xml_result = self._parse_with_elementtree(xml_path)
            else:
                logger.warning("No XML parser available (lxml or xml.etree)")
                xml_result = {}

            result.update(xml_result)

        return result

    def _parse_hetio_symptoms(self, symptoms_path: Path) -> Optional[pd.DataFrame]:
        """
        Parse Hetionet symptoms file.

        Args:
            symptoms_path: Path to symptoms.tsv

        Returns:
            DataFrame with symptom terms and HSDN flag
        """
        logger.info(f"Parsing Hetionet symptoms from {symptoms_path}")

        try:
            df = pd.read_csv(symptoms_path, sep='\t')

            # Expected columns: mesh_id, mesh_name, in_hsdn
            logger.info(f"Parsed {len(df)} Hetionet symptom terms")

            # Add metadata columns
            df['license'] = 'CC0 1.0'
            df['source'] = 'MeSH'
            df['sourceDatabase'] = 'MeSH'

            return df

        except Exception as e:
            logger.error(f"Error parsing Hetionet symptoms: {e}")
            return None

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
            "hetio_symptoms": {
                "mesh_id": "MeSH Descriptor UI (e.g., D005221)",
                "mesh_name": "Symptom name",
                "in_hsdn": "In Human Symptom Disease Network (1 or 0)",
                "license": "License (CC0 1.0)",
                "source": "Data source (MeSH)",
                "sourceDatabase": "Source database (MeSH)"
            },
            "symptom_nodes": {
                "mesh_id": "MeSH Descriptor UI (e.g., D005221)",
                "name": "Symptom name",
                "definition": "Scope note/definition",
                "tree_numbers": "Pipe-separated MeSH tree numbers"
            }
        }
