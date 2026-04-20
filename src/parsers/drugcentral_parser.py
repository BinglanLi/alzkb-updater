"""
DrugCentral Parser for the knowledge graph.

This module parses DrugCentral data to extract:
- Drug-disease treatment relationships (drugTreatsDisease, drugPalliatesDisease)
- Pharmacologic Class nodes (PC)
- Pharmacologic Class includes Compound edges (PCiC)

Output:
  - drug_treats_disease.tsv: drugTreatsDisease (CtD) relationships
  - drug_palliates_disease.tsv: drugPalliatesDisease (CpD) relationships
  - pharmacologic_classes.tsv: Pharmacologic Class nodes
  - pharmacologic_class_includes_compound.tsv: PCiC edges

Requires a local PostgreSQL instance with the DrugCentral dump loaded:
  createdb drugcentral
  gunzip -c drugcentral.sql.gz | psql drugcentral
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class DrugCentralParser(BaseParser):
    """Parser for DrugCentral PostgreSQL database."""

    DRUGCENTRAL_URL = "https://unmtid-dbs.net/download/drugcentral.dump.11012023.sql.gz"

    VALID_CLASS_TYPES = {
        'Physiologic Effect',
        'Mechanism of Action',
        'Chemical/Ingredient',
        'Chemical Structure'
    }

    def __init__(self, data_dir: str = None,
                 pg_config: Optional[Dict[str, str]] = None):
        """
        Args:
            data_dir: Directory for cached data
            pg_config: PostgreSQL connection config with keys:
                       'host', 'port', 'dbname', 'user', 'password'
        """
        super().__init__(data_dir)
        self.source_name = "drugcentral"
        self.pg_config = pg_config or {}
        self._pg_available = False

        try:
            import psycopg2
            self._pg_available = True
            logger.info("psycopg2 is available")
        except ImportError:
            logger.warning("psycopg2 not available. Install with: pip install psycopg2-binary")

    def _connect(self):
        import psycopg2
        defaults = {"host": "localhost", "port": 5432, "dbname": "drugcentral",
                    "options": "-c search_path=public"}
        config = {**defaults, **self.pg_config}
        return psycopg2.connect(**config)

    def _query(self, conn, query: str, params=None) -> pd.DataFrame:
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                cols = [desc[0] for desc in cur.description]
                return pd.DataFrame(cur.fetchall(), columns=cols)
        except Exception:
            conn.rollback()
            raise

    def download_data(self) -> bool:
        logger.info("Downloading DrugCentral...")
        result = self.download_file(self.DRUGCENTRAL_URL, "drugcentral.sql.gz")
        if result:
            logger.info(f"Successfully downloaded DrugCentral to {result}")
            logger.info("Load into PostgreSQL with: gunzip -c drugcentral.sql.gz | psql drugcentral")
            return True
        logger.error("Failed to download DrugCentral")
        return False

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        if not self._pg_available:
            logger.error("psycopg2 is required. Install with: pip install psycopg2-binary")
            return {}

        result = {}

        try:
            with self._connect() as conn:
                omop_df = self._query_omop_relationships(conn)
                if omop_df is not None and len(omop_df) > 0:
                    treats = omop_df[omop_df['relationship_name'] == 'indication']
                    palliates = omop_df[omop_df['relationship_name'] == 'off-label use']

                    logger.info(f"Found {len(treats)} treatment relationships")
                    logger.info(f"Found {len(palliates)} palliation relationships")

                    if len(treats) > 0:
                        result["drug_treats_disease"] = treats.reset_index(drop=True)
                    if len(palliates) > 0:
                        result["drug_palliates_disease"] = palliates.reset_index(drop=True)
                else:
                    logger.warning("No drug-disease relationships found")

                classes_df = self._query_pharmacologic_classes(conn)
                if classes_df is not None and len(classes_df) > 0:
                    result["pharmacologic_classes"] = classes_df
                    logger.info(f"Found {len(classes_df)} pharmacologic classes")
                else:
                    logger.warning("No pharmacologic classes found")

                if classes_df is not None:
                    valid_class_codes = set(classes_df['class_code'].values)
                    edges_df = self._query_drug_class_edges(conn, valid_class_codes)
                    if edges_df is not None and len(edges_df) > 0:
                        result["pharmacologic_class_includes_compound"] = edges_df
                        logger.info(f"Found {len(edges_df)} drug-class relationships")

        except Exception as e:
            logger.error(f"Error connecting to DrugCentral database: {e}")
            logger.error("Ensure PostgreSQL is running and the dump is loaded: "
                         "gunzip -c drugcentral.sql.gz | psql drugcentral")
            return {}

        return result

    def _query_omop_relationships(self, conn) -> Optional[pd.DataFrame]:
        query = """
            SELECT struct_id, concept_id, relationship_name, concept_name,
                   umls_cui, snomed_full_name
            FROM omop_relationship
            WHERE relationship_name IN ('indication', 'off-label use')
        """
        try:
            df = self._query(conn, query)
            df['source'] = 'DrugCentral'
            return df
        except Exception as e:
            logger.error(f"Error querying omop_relationship: {e}")
            return None

    def _query_pharmacologic_classes(self, conn) -> Optional[pd.DataFrame]:
        placeholders = ','.join(['%s'] * len(self.VALID_CLASS_TYPES))
        query = f"""
            SELECT DISTINCT class_code, name, type, source
            FROM pharma_class
            WHERE type IN ({placeholders})
              AND class_code IS NOT NULL
        """
        try:
            df = self._query(conn, query, list(self.VALID_CLASS_TYPES))
            df = df.rename(columns={'name': 'class_name', 'type': 'class_type',
                                    'source': 'class_source'})
            df = df.drop_duplicates(subset=['class_code'])
            df['url'] = df['class_code'].apply(
                lambda x: f'http://purl.bioontology.org/ontology/NDFRT/{x}'
            )
            df['license'] = 'CC BY 4.0'
            df['sourceDatabase'] = 'DrugCentral'
            df['source'] = df['class_source'].apply(lambda x: f'{x} via DrugCentral')
            return df
        except Exception as e:
            logger.error(f"Error querying pharma_class: {e}")
            return None

    def _query_drug_class_edges(self, conn, valid_class_codes: set) -> Optional[pd.DataFrame]:
        placeholders = ','.join(['%s'] * len(self.VALID_CLASS_TYPES))
        query = f"""
            SELECT i.identifier AS drugbank_id, pc.class_code
            FROM pharma_class pc
            JOIN identifier i ON pc.struct_id = i.struct_id
            WHERE i.id_type = 'DRUGBANK_ID'
              AND pc.type IN ({placeholders})
              AND pc.class_code IS NOT NULL
        """
        try:
            df = self._query(conn, query, list(self.VALID_CLASS_TYPES))
            df = df[df['class_code'].isin(valid_class_codes)]
            df = df.drop_duplicates(subset=['drugbank_id', 'class_code'])
            df['source'] = 'DrugCentral'
            df['license'] = 'CC BY 4.0'
            df['unbiased'] = False
            df['sourceDatabase'] = 'DrugCentral'
            return df
        except Exception as e:
            logger.error(f"Error querying drug-class edges: {e}")
            return None

    def get_schema(self) -> Dict[str, Dict[str, str]]:
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
                "class_code": "NDFRT class identifier (e.g., N0000175503)",
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
                "class_code": "NDFRT class identifier",
                "source": "Data source (DrugCentral)",
                "license": "License (CC BY 4.0)",
                "unbiased": "Whether edge is unbiased (False)",
                "sourceDatabase": "Source database name (DrugCentral)"
            }
        }
