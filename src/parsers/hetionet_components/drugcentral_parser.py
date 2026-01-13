"""
DrugCentral Parser for AlzKB.

This module parses DrugCentral data to extract drug-disease treatment
relationships (drugTreatsDisease, drugPalliatesDisease) for AlzKB.

Data Source: https://unmtid-dbs.net/download/drugcentral.dump.sql.gz

Output:
  - drug_treats_disease.tsv: drugTreatsDisease (CtD) relationships
  - drug_palliates_disease.tsv: drugPalliatesDisease (CpD) relationships
"""

import logging
import gzip
import re
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)


class DrugCentralParser(BaseParser):
    """
    Parser for DrugCentral database.

    Extracts drug-disease treatment relationships from DrugCentral
    for use in AlzKB.
    """

    # DrugCentral SQL dump URL
    DRUGCENTRAL_URL = "https://unmtid-dbs.net/download/drugcentral.dump.01012025.sql.gz"

    def __init__(self, data_dir: str):
        """
        Initialize the DrugCentral parser.

        Args:
            data_dir: Directory to store downloaded and processed data
        """
        super().__init__(data_dir)
        self.source_name = "drugcentral"

    def download_data(self) -> bool:
        """
        Download the DrugCentral SQL dump.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading DrugCentral...")

        result = self.download_file(self.DRUGCENTRAL_URL, "drugcentral.sql.gz")

        if result:
            logger.info(f"Successfully downloaded DrugCentral to {result}")
            return True
        else:
            logger.error("Failed to download DrugCentral")
            return False

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse DrugCentral SQL dump.

        Returns:
            Dictionary with drug-disease relationships
        """
        sql_path = self.source_dir / "drugcentral.sql.gz"

        if not sql_path.exists():
            logger.error(f"DrugCentral file not found: {sql_path}")
            return {}

        logger.info(f"Parsing DrugCentral from {sql_path}")

        try:
            # Parse the SQL dump to extract relevant tables
            omop_relationships = self._parse_omop_relationships(sql_path)

            if not omop_relationships:
                logger.warning("No drug-disease relationships found")
                return {}

            # Separate by relationship type
            treats = [r for r in omop_relationships if r.get('relationship_name') == 'indication']
            palliates = [r for r in omop_relationships if r.get('relationship_name') == 'off-label use']

            logger.info(f"Found {len(treats)} treatment relationships")
            logger.info(f"Found {len(palliates)} palliation relationships")

            result = {}

            if treats:
                result["drug_treats_disease"] = pd.DataFrame(treats)

            if palliates:
                result["drug_palliates_disease"] = pd.DataFrame(palliates)

            return result

        except Exception as e:
            logger.error(f"Error parsing DrugCentral: {e}")
            return {}

    def _parse_omop_relationships(self, sql_path: Path) -> List[Dict]:
        """
        Parse OMOP relationship table from SQL dump.

        Args:
            sql_path: Path to SQL dump file

        Returns:
            List of drug-disease relationship dictionaries
        """
        relationships = []
        in_table = False
        table_name = None

        # Regex to match INSERT statements
        insert_pattern = re.compile(r"INSERT INTO (\w+) VALUES")
        values_pattern = re.compile(r"\(([^)]+)\)")

        try:
            with gzip.open(sql_path, 'rt', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # Check for relevant table inserts
                    if 'omop_relationship' in line.lower():
                        in_table = True

                    if in_table and line.strip().startswith('('):
                        # Parse VALUES
                        matches = values_pattern.findall(line)
                        for match in matches:
                            parts = self._parse_sql_values(match)
                            if len(parts) >= 5:
                                rel = {
                                    "struct_id": parts[0],
                                    "concept_id": parts[1],
                                    "relationship_name": parts[2],
                                    "concept_name": parts[3],
                                    "umls_cui": parts[4] if len(parts) > 4 else "",
                                    "snomed_full_name": parts[5] if len(parts) > 5 else "",
                                    "source": "DrugCentral"
                                }
                                relationships.append(rel)

                    # Check for end of table
                    if in_table and line.strip() == ');':
                        in_table = False

        except Exception as e:
            logger.error(f"Error reading SQL dump: {e}")

        return relationships

    def _parse_sql_values(self, values_str: str) -> List[str]:
        """
        Parse SQL VALUES string into list of values.

        Args:
            values_str: Comma-separated values string

        Returns:
            List of parsed values
        """
        values = []
        current = ""
        in_quote = False

        for char in values_str:
            if char == "'" and not in_quote:
                in_quote = True
            elif char == "'" and in_quote:
                in_quote = False
            elif char == ',' and not in_quote:
                values.append(current.strip().strip("'"))
                current = ""
            else:
                current += char

        if current:
            values.append(current.strip().strip("'"))

        return values

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for DrugCentral data.

        Returns:
            Dictionary defining the schema for drug-disease relationships
        """
        return {
            "drug_treats_disease": {
                "struct_id": "DrugCentral structure ID",
                "concept_id": "OMOP concept ID for disease",
                "relationship_name": "Relationship type (indication)",
                "concept_name": "Disease/condition name",
                "umls_cui": "UMLS Concept Unique Identifier",
                "snomed_full_name": "SNOMED-CT term",
                "source": "Data source (DrugCentral)"
            },
            "drug_palliates_disease": {
                "struct_id": "DrugCentral structure ID",
                "concept_id": "OMOP concept ID for disease",
                "relationship_name": "Relationship type (off-label use)",
                "concept_name": "Disease/condition name",
                "umls_cui": "UMLS Concept Unique Identifier",
                "snomed_full_name": "SNOMED-CT term",
                "source": "Data source (DrugCentral)"
            }
        }
