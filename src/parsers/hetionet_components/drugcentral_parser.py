"""
DrugCentral Parser for AlzKB.

This module parses DrugCentral data to extract:
- Drug-disease treatment relationships (drugTreatsDisease, drugPalliatesDisease)
- Pharmacologic Class nodes (PC)
- Pharmacologic Class includes Compound edges (PCiC)

Data Source: https://unmtid-dbs.net/download/drugcentral.dump.sql.gz

Output:
  - drug_treats_disease.tsv: drugTreatsDisease (CtD) relationships
  - drug_palliates_disease.tsv: drugPalliatesDisease (CpD) relationships
  - pharmacologic_classes.tsv: Pharmacologic Class nodes (478)
  - pharmacologic_class_includes_compound.tsv: PCiC edges (1,948)
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

    Extracts drug-disease treatment relationships and pharmacologic class
    information from DrugCentral for use in AlzKB.
    """

    # DrugCentral SQL dump URL
    DRUGCENTRAL_URL = "https://unmtid-dbs.net/download/drugcentral.dump.01012025.sql.gz"

    # Valid pharmacologic class types for hetionet
    VALID_CLASS_TYPES = {
        'Physiologic Effect',
        'Mechanism of Action',
        'Chemical/Ingredient',
        'Chemical Structure'
    }

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
            Dictionary with drug-disease relationships and pharmacologic classes
        """
        sql_path = self.source_dir / "drugcentral.sql.gz"

        if not sql_path.exists():
            logger.error(f"DrugCentral file not found: {sql_path}")
            return {}

        logger.info(f"Parsing DrugCentral from {sql_path}")

        result = {}

        try:
            # Parse the SQL dump to extract relevant tables
            omop_relationships = self._parse_omop_relationships(sql_path)

            if omop_relationships:
                # Separate by relationship type
                treats = [r for r in omop_relationships if r.get('relationship_name') == 'indication']
                palliates = [r for r in omop_relationships if r.get('relationship_name') == 'off-label use']

                logger.info(f"Found {len(treats)} treatment relationships")
                logger.info(f"Found {len(palliates)} palliation relationships")

                if treats:
                    result["drug_treats_disease"] = pd.DataFrame(treats)

                if palliates:
                    result["drug_palliates_disease"] = pd.DataFrame(palliates)
            else:
                logger.warning("No drug-disease relationships found")

            # Parse pharmacologic classes
            pharma_classes, drug_to_class = self._parse_pharmacologic_classes(sql_path)

            if pharma_classes is not None and len(pharma_classes) > 0:
                result["pharmacologic_classes"] = pharma_classes
                logger.info(f"Found {len(pharma_classes)} pharmacologic classes")

            if drug_to_class is not None and len(drug_to_class) > 0:
                result["pharmacologic_class_includes_compound"] = drug_to_class
                logger.info(f"Found {len(drug_to_class)} drug-class relationships")

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

    def _parse_pharmacologic_classes(self, sql_path: Path) -> tuple:
        """
        Parse pharmacologic class tables from SQL dump.

        Extracts:
        - pharma_class table: class definitions
        - struct2atc table: drug-class mappings via ATC codes
        - identifier table: DrugBank ID mappings

        Args:
            sql_path: Path to SQL dump file

        Returns:
            Tuple of (pharmacologic_classes DataFrame, drug_to_class DataFrame)
        """
        logger.info("Parsing pharmacologic classes from DrugCentral SQL dump")

        pharma_classes = []
        struct2atc = []
        identifiers = {}  # struct_id -> drugbank_id mapping

        # Track which table we're parsing
        current_table = None

        try:
            with gzip.open(sql_path, 'rt', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line_lower = line.lower()

                    # Detect table context from COPY statements (PostgreSQL)
                    if line_lower.startswith('copy '):
                        if 'pharma_class' in line_lower and 'struct_id' not in line_lower:
                            current_table = 'pharma_class'
                        elif 'struct2atc' in line_lower:
                            current_table = 'struct2atc'
                        elif 'identifier' in line_lower:
                            current_table = 'identifier'
                        else:
                            current_table = None
                        continue

                    # End of COPY data
                    if line.strip() == '\\.' or line.startswith('--'):
                        current_table = None
                        continue

                    # Parse data rows
                    if current_table and line.strip() and not line.startswith('--'):
                        parts = line.strip().split('\t')

                        if current_table == 'pharma_class' and len(parts) >= 4:
                            # pharma_class: class_id, class_name, class_source, class_type
                            class_type = parts[3] if len(parts) > 3 else ''
                            if class_type in self.VALID_CLASS_TYPES:
                                pharma_classes.append({
                                    'class_id': parts[0],
                                    'class_name': parts[1],
                                    'class_source': parts[2],
                                    'class_type': class_type,
                                    'source': f'{parts[2]} via DrugCentral',
                                    'license': 'CC BY 4.0',
                                    'sourceDatabase': 'DrugCentral'
                                })

                        elif current_table == 'identifier' and len(parts) >= 4:
                            # identifier: id, identifier, id_type, struct_id
                            if parts[2] == 'DRUGBANK_ID':
                                struct_id = parts[3]
                                drugbank_id = parts[1]
                                identifiers[struct_id] = drugbank_id

                        elif current_table == 'struct2atc' and len(parts) >= 2:
                            # struct2atc: struct_id, atc_code
                            struct2atc.append({
                                'struct_id': parts[0],
                                'atc_code': parts[1]
                            })

        except Exception as e:
            logger.error(f"Error parsing pharmacologic classes: {e}")
            return None, None

        # Create pharmacologic classes DataFrame
        if pharma_classes:
            classes_df = pd.DataFrame(pharma_classes)
            classes_df = classes_df.drop_duplicates(subset=['class_id'])

            # Add URL based on NDFRT ontology
            classes_df['url'] = classes_df['class_id'].apply(
                lambda x: f'http://purl.bioontology.org/ontology/NDFRT/{x}'
            )

            logger.info(f"Parsed {len(classes_df)} pharmacologic classes")
        else:
            classes_df = None
            logger.warning("No pharmacologic classes found")

        # Create drug-to-class relationships
        # Note: The original hetionet uses a more complex mapping through ATC codes
        # For simplicity, we'll try to map directly using struct_id to DrugBank ID
        if pharma_classes and identifiers:
            # Parse struct2pharma_class table for direct mappings
            drug_class_edges = self._parse_struct_pharma_class(sql_path, identifiers, classes_df)
            if drug_class_edges is not None and len(drug_class_edges) > 0:
                logger.info(f"Parsed {len(drug_class_edges)} drug-class relationships")
                return classes_df, drug_class_edges

        return classes_df, None

    def _parse_struct_pharma_class(self, sql_path: Path, identifiers: Dict, classes_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Parse struct2pharma_class table for drug-class relationships.

        Args:
            sql_path: Path to SQL dump file
            identifiers: Dict mapping struct_id to drugbank_id
            classes_df: DataFrame of valid pharmacologic classes

        Returns:
            DataFrame with drug-class relationships
        """
        drug_class_edges = []
        current_table = None
        valid_class_ids = set(classes_df['class_id'].values) if classes_df is not None else set()

        try:
            with gzip.open(sql_path, 'rt', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line_lower = line.lower()

                    # Detect struct2pharma_class table
                    if line_lower.startswith('copy ') and 'struct2pharma_class' in line_lower:
                        current_table = 'struct2pharma_class'
                        continue

                    if line.strip() == '\\.' or line.startswith('--'):
                        if current_table == 'struct2pharma_class':
                            break  # Found what we need
                        current_table = None
                        continue

                    if current_table == 'struct2pharma_class' and line.strip():
                        parts = line.strip().split('\t')
                        if len(parts) >= 2:
                            struct_id = parts[0]
                            class_id = parts[1]

                            # Only include if we have a DrugBank ID and valid class
                            if struct_id in identifiers and class_id in valid_class_ids:
                                drug_class_edges.append({
                                    'drugbank_id': identifiers[struct_id],
                                    'class_id': class_id,
                                    'source': 'DrugCentral',
                                    'license': 'CC BY 4.0',
                                    'unbiased': False,
                                    'sourceDatabase': 'DrugCentral'
                                })

        except Exception as e:
            logger.error(f"Error parsing struct2pharma_class: {e}")
            return None

        if drug_class_edges:
            edges_df = pd.DataFrame(drug_class_edges)
            edges_df = edges_df.drop_duplicates(subset=['drugbank_id', 'class_id'])
            return edges_df

        return None

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for DrugCentral data.

        Returns:
            Dictionary defining the schema for drug-disease relationships and pharmacologic classes
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
            },
            "pharmacologic_classes": {
                "class_id": "NDFRT class identifier (e.g., N0000175503)",
                "class_name": "Class name",
                "class_source": "Source of class definition (FDA, etc.)",
                "class_type": "Type: Physiologic Effect, Mechanism of Action, etc.",
                "source": "Data source description",
                "url": "URL to ontology entry",
                "license": "License (CC BY 4.0)",
                "sourceDatabase": "Source database name (DrugCentral)"
            },
            "pharmacologic_class_includes_compound": {
                "drugbank_id": "DrugBank ID of compound",
                "class_id": "NDFRT class identifier",
                "source": "Data source (DrugCentral)",
                "license": "License (CC BY 4.0)",
                "unbiased": "Whether edge is unbiased (False)",
                "sourceDatabase": "Source database name (DrugCentral)"
            }
        }
