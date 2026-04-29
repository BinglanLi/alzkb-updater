"""
DisGeNETParser: Parser for DisGeNET gene-disease association data.

DisGeNET is a comprehensive database of gene-disease associations
from various sources including literature and databases.

Source: https://www.disgenet.org/
API Documentation: https://www.disgenet.org/api/

Disease scope is configurable via the disease_scope parameter, which
is read from config/project.yaml by the pipeline.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import pandas as pd
import requests
import time
from .base_parser import BaseParser
from config_loader import get_disease_scope

DISGENET_DISEASE_CLASSIFICATIONS = 'disease_classifications'
DISGENET_DISEASE_MAPPINGS = 'disease_mappings'
DISGENET_GENE_DISEASE_ASSOCIATIONS = 'gene_disease_associations'

logger = logging.getLogger(__name__)


class DisGeNETParser(BaseParser):
    """
    Parser for DisGeNET gene-disease association data.

    Supports both API-based retrieval and manual file-based parsing.
    Disease search terms are configurable via the disease_scope parameter.
    """

    def __init__(
        self,
        data_dir: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        disease_scope: Optional[Dict] = None,
    ):
        """
        Initialize DisGeNET parser.

        Args:
            data_dir: Directory for storing data files.
            api_key: DisGeNET API key (optional, for API access).
            base_url: Base URL for the DisGeNET REST API.
                      Defaults to https://api.disgenet.com/api/v1.
            disease_scope: Disease scope dict from project config.
                           Recognised keys: primary_terms, umls_cuis.
                           Falls back to values from config/project.yaml when absent.
        """
        super().__init__(data_dir)
        self.api_key = api_key or os.getenv('DISGENET_API_KEY')

        # Use base_url from config (databases.yaml) or fall back to the
        # current DisGeNET v1 endpoint.  The config value is forwarded
        # verbatim; if it points to the legacy host we still try it.
        self.API_BASE_URL = (base_url or "https://api.disgenet.com/api/v1").rstrip("/")

        self.session = requests.Session()

        # Disease scope — prefer the caller-supplied dict (forwarded from
        # main.py / databases.yaml), then fall back to config/project.yaml.
        # No disease-specific values are ever hard-coded in this file.
        _cfg_scope = disease_scope if disease_scope else get_disease_scope()

        self.disease_terms: List[str] = _cfg_scope.get("primary_terms", [])
        self.umls_cuis: List[str] = _cfg_scope.get("umls_cuis", [])

        if not self.disease_terms:
            logger.warning(
                "No primary_terms found in disease_scope or config/project.yaml. "
                "API search will be skipped."
            )
        if not self.umls_cuis:
            logger.warning(
                "No umls_cuis found in disease_scope or config/project.yaml. "
                "Direct CUI queries will be skipped."
            )

        if self.api_key:
            self.session.headers.update({
                'Authorization': self.api_key,
                'accept': 'application/json',
            })
            logger.info("DisGeNET API key configured")
        else:
            logger.warning("No DisGeNET API key provided. Will attempt file-based parsing.")

    # ------------------------------------------------------------------
    # download_data
    # ------------------------------------------------------------------

    def download_data(self) -> bool:
        """
        Download or check for DisGeNET data.

        If API key is available, downloads data via API.
        Otherwise, checks for manually downloaded files.

        Returns:
            True if data is available, False otherwise.
        """
        if self.api_key:
            return self._download_via_api()
        else:
            return self._check_manual_files()

    def _check_manual_files(self) -> bool:
        """Check for manually downloaded DisGeNET files."""
        logger.info("Checking for DisGeNET data files...")
        logger.info("Note: DisGeNET data must be downloaded manually from:")
        logger.info("  https://www.disgenet.org/downloads")
        logger.info("  Required files:")
        logger.info("    - curated_gene_disease_associations.tsv")
        logger.info("    - disease_classifications.tsv")
        logger.info("    - disease_mappings.tsv")

        required_files = [
            f"{DISGENET_GENE_DISEASE_ASSOCIATIONS}.tsv",
            f"{DISGENET_DISEASE_CLASSIFICATIONS}.tsv",
            f"{DISGENET_DISEASE_MAPPINGS}.tsv",
        ]

        all_exist = True
        for filename in required_files:
            filepath = self.get_file_path(filename)
            if os.path.exists(filepath):
                logger.info(f"✓ Found {filename}")
            else:
                logger.error(f"✗ {filename} not found at: {filepath}")
                all_exist = False

        if not all_exist:
            logger.error("Please download manually or provide API key")
            return False

        return True

    def _download_via_api(self) -> bool:
        """
        Download DisGeNET data via API.

        Strategy:
          1. Search by primary_terms to discover disease entities and their CUIs.
          2. Supplement with any explicit umls_cuis from project.yaml.
          3. Fetch gene-disease associations for each unique CUI.

        Returns:
            True if successful, False otherwise.
        """
        logger.info(
            f"Downloading DisGeNET data via API "
            f"(disease terms: {self.disease_terms}, CUIs: {self.umls_cuis})..."
        )

        output_files = [
            self.get_file_path(f"api_{DISGENET_DISEASE_CLASSIFICATIONS}.tsv"),
            self.get_file_path(f"api_{DISGENET_DISEASE_MAPPINGS}.tsv"),
            self.get_file_path(f"api_{DISGENET_GENE_DISEASE_ASSOCIATIONS}.tsv"),
        ]
        if all(Path(f).exists() for f in output_files) and not self.force:
            logger.info("All DisGeNET API files already present, skipping download")
            return True

        try:
            # Step 1: Get disease metadata for configured search terms
            disease_classifications, disease_mappings = self.get_disease_ids(self.disease_terms)

            if disease_classifications is None or disease_mappings is None:
                logger.error("Failed to retrieve disease IDs from API")
                return False

            # Save disease data frames
            classifications_path = self.get_file_path(f"api_{DISGENET_DISEASE_CLASSIFICATIONS}.tsv")
            disease_classifications.to_csv(classifications_path, sep='\t', index=False)
            logger.info(f"✓ Saved disease classifications: {classifications_path}")

            mappings_path = self.get_file_path(f"api_{DISGENET_DISEASE_MAPPINGS}.tsv")
            disease_mappings.to_csv(mappings_path, sep='\t', index=False)
            logger.info(f"✓ Saved disease mappings: {mappings_path}")

            # Step 2: Collect unique disease CUIs — from API response + explicit list
            api_cuis = disease_mappings['diseaseId'].dropna().unique().tolist()
            all_cuis = list(dict.fromkeys(api_cuis + self.umls_cuis))  # preserve order, dedupe
            logger.info(f"✓ Querying associations for {len(all_cuis)} unique disease CUIs")

            if not all_cuis:
                logger.warning("No disease IDs found to query associations")
                return False

            # Step 3: Fetch gene-disease associations for each CUI
            all_associations = []
            for disease_id in all_cuis:
                logger.info(f"Fetching associations for disease ID: {disease_id}")
                associations = self._get_disease_associations_by_id(disease_id)

                if associations is not None and len(associations) > 0:
                    all_associations.append(associations)
                    logger.info(f"  ✓ Retrieved {len(associations)} associations")
                else:
                    logger.warning(f"  No associations found for {disease_id}")

                # Rate limiting — be respectful to the API
                time.sleep(0.5)

            # Step 4: Combine and deduplicate
            if all_associations:
                combined_associations = pd.concat(all_associations, ignore_index=True)
                initial_count = len(combined_associations)
                combined_associations = combined_associations.drop_duplicates()
                final_count = len(combined_associations)
                if initial_count != final_count:
                    logger.info(f"Removed {initial_count - final_count} duplicate associations")

                output_path = self.get_file_path(f"api_{DISGENET_GENE_DISEASE_ASSOCIATIONS}.tsv")
                combined_associations.to_csv(output_path, sep='\t', index=False)
                logger.info(
                    f"✓ Downloaded {len(combined_associations)} total "
                    "gene-disease associations via API"
                )
                return True
            else:
                logger.error("No gene-disease associations retrieved")
                return False

        except Exception as e:
            logger.error(f"API download failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    # ------------------------------------------------------------------
    # Disease entity discovery
    # ------------------------------------------------------------------

    def get_disease_ids(
        self, search_terms: Optional[List[str]] = None
    ) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Get disease IDs and related information from DisGeNET API using free text search.

        Args:
            search_terms: List of disease search strings (e.g., ["diabetes"]).
                          If None, uses self.disease_terms.

        Returns:
            Tuple of two DataFrames:
            - disease_classifications: disease classification information
            - disease_mappings: disease code mappings across vocabularies
        """
        if search_terms is None:
            search_terms = self.disease_terms

        all_classifications = []
        all_mappings = []

        for term in search_terms:
            logger.info(f"Querying DisGeNET API for disease term: '{term}'...")
            c, m = self._query_disease_term(term)
            if c is not None:
                all_classifications.append(c)
            if m is not None:
                all_mappings.append(m)

        if not all_classifications:
            return None, None

        classifications = pd.concat(all_classifications, ignore_index=True).drop_duplicates()
        mappings = pd.concat(all_mappings, ignore_index=True).drop_duplicates()

        logger.info(f"Total: {len(classifications)} classifications, {len(mappings)} mappings")
        return classifications, mappings

    def _query_disease_term(self, search_term: str) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Query the DisGeNET API for a single disease search term.

        Returns:
            Tuple of (classifications_df, mappings_df) or (None, None).
        """
        endpoint = f"{self.API_BASE_URL}/entity/disease"
        params = {
            'disease_free_text_search_string': search_term,
        }

        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if 'payload' not in data:
                logger.warning("No disease entities found in API response")
                return None, None

            payload = data['payload']
            logger.info(f"✓ Retrieved {len(payload)} disease entities from API")

            # Build disease_classifications DataFrame
            classifications_data = []
            for item in payload:
                disease_classes_msh = ','.join(item.get('diseaseClasses_MSH', []))
                disease_classes_umls_st = ','.join(item.get('diseaseClasses_UMLS_ST', []))
                disease_classes_do = ','.join(item.get('diseaseClasses_DO', []))
                disease_classes_hpo = ','.join(item.get('diseaseClasses_HPO', []))
                classifications_data.append({
                    'diseaseName': item.get('name', ''),
                    'diseaseId': item.get('diseaseUMLSCUI', ''),
                    'diseaseClasses_MSH': disease_classes_msh,
                    'diseaseClasses_UMLS_ST': disease_classes_umls_st,
                    'diseaseClasses_DO': disease_classes_do,
                    'diseaseClasses_HPO': disease_classes_hpo,
                })

            disease_classifications = pd.DataFrame(classifications_data)
            disease_classifications['sourceDatabase'] = 'DisGeNET'
            logger.info(
                f"✓ Created {DISGENET_DISEASE_CLASSIFICATIONS} "
                f"with {len(disease_classifications)} rows"
            )

            # Build disease_mappings DataFrame
            mappings_data = []
            for item in payload:
                base_data = {
                    'diseaseName': item.get('name', ''),
                    'diseaseId': item.get('diseaseUMLSCUI', ''),
                }
                code_dict: Dict[str, str] = {}
                for code_item in item.get('diseaseCodes', []):
                    vocabulary = code_item.get('vocabulary', '')
                    code = code_item.get('code', '')
                    if vocabulary:
                        code_dict[vocabulary] = code
                mappings_data.append({**base_data, **code_dict})

            disease_mappings = pd.DataFrame(mappings_data)
            disease_mappings['sourceDatabase'] = 'DisGeNET'
            logger.info(
                f"✓ Created {DISGENET_DISEASE_MAPPINGS} "
                f"with {len(disease_mappings)} rows and {len(disease_mappings.columns)} columns"
            )

            return disease_classifications, disease_mappings

        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None, None
        except Exception as e:
            logger.error(f"Error processing disease entities: {e}")
            return None, None

    def _get_disease_associations_by_id(
        self, disease_id: str, limit: int = 10000
    ) -> Optional[pd.DataFrame]:
        """
        Get gene-disease associations from DisGeNET API using a UMLS CUI.

        Args:
            disease_id: UMLS CUI (e.g., C0011849 for Diabetes Mellitus).
            limit: Maximum number of results.

        Returns:
            DataFrame of associations or None if failed.
        """
        logger.info(f"Querying DisGeNET API for disease ID: {disease_id}")

        endpoint = f"{self.API_BASE_URL}/gda/summary"
        params = {
            'disease': f'UMLS_{disease_id}',
            'source': 'CURATED',
        }

        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if 'payload' not in data:
                logger.warning("No disease-gene associations found in API response")
                return None

            payload = data['payload']
            logger.info(f"✓ Retrieved {len(payload)} disease-gene associations from API")

            gda_data = []
            for item in payload:
                gda_data.append({
                    'geneId': item.get('geneNcbiID', ''),
                    'geneSymbol': item.get('symbolOfGene', ''),
                    'geneType': item.get('geneNcbiType', ''),
                    'diseaseId': item.get('diseaseUMLSCUI', ''),
                    'diseaseName': item.get('diseaseName', ''),
                    'diseaseClasses_MSH': ','.join(item.get('diseaseClasses_MSH', [])),
                    'diseaseClasses_UMLS_ST': ','.join(item.get('diseaseClasses_UMLS_ST', [])),
                    'diseaseClasses_DO': ','.join(item.get('diseaseClasses_DO', [])),
                    'diseaseClasses_HPO': ','.join(item.get('diseaseClasses_HPO', [])),
                    'diseaseMapping': ','.join(item.get('diseaseVocabularies', [])),
                    'diseaseType': item.get('diseaseType', ''),
                    'score': item.get('score', ''),
                })

            gda_df = pd.DataFrame(gda_data)
            gda_df['sourceDatabase'] = 'DisGeNET'
            logger.info(f"✓ Retrieved {len(gda_df)} gene-disease associations")
            return gda_df

        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None

    # ------------------------------------------------------------------
    # parse_data
    # ------------------------------------------------------------------

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse DisGeNET data.

        Returns:
            Dictionary with 'gene_disease_associations', 'disease_mappings',
            and 'disease_classifications' DataFrames.
        """
        logger.info("Parsing DisGeNET data...")
        result: Dict[str, pd.DataFrame] = {}

        # --- gene_disease_associations ---
        api_gda_file = self.get_file_path(f"api_{DISGENET_GENE_DISEASE_ASSOCIATIONS}.tsv")
        manual_gda_file = self.get_file_path(f"{DISGENET_GENE_DISEASE_ASSOCIATIONS}.tsv")
        for path, label in [(api_gda_file, "API"), (manual_gda_file, "manual")]:
            if DISGENET_GENE_DISEASE_ASSOCIATIONS in result:
                break
            if os.path.exists(path):
                logger.info(f"Using {label} gene-disease associations: {path}")
                df = self.read_tsv(path)
                if df is not None:
                    df['sourceDatabase'] = 'DisGeNET'
                    result[DISGENET_GENE_DISEASE_ASSOCIATIONS] = df
                    logger.info(f"✓ Parsed {len(df)} gene-disease associations from {label}")

        # --- disease_mappings ---
        api_map_file = self.get_file_path(f"api_{DISGENET_DISEASE_MAPPINGS}.tsv")
        manual_map_file = self.get_file_path(f"{DISGENET_DISEASE_MAPPINGS}.tsv")
        for path, label in [(api_map_file, "API"), (manual_map_file, "manual")]:
            if DISGENET_DISEASE_MAPPINGS in result:
                break
            if os.path.exists(path):
                logger.info(f"Using {label} disease mappings: {path}")
                df = self.read_tsv(path)
                if df is not None:
                    df['sourceDatabase'] = 'DisGeNET'
                    result[DISGENET_DISEASE_MAPPINGS] = df
                    logger.info(f"✓ Parsed {len(df)} disease mappings from {label}")

        # --- disease_classifications ---
        api_cls_file = self.get_file_path(f"api_{DISGENET_DISEASE_CLASSIFICATIONS}.tsv")
        manual_cls_file = self.get_file_path(f"{DISGENET_DISEASE_CLASSIFICATIONS}.tsv")
        for path, label in [(api_cls_file, "API"), (manual_cls_file, "manual")]:
            if DISGENET_DISEASE_CLASSIFICATIONS in result:
                break
            if os.path.exists(path):
                logger.info(f"Using {label} disease classifications: {path}")
                df = self.read_tsv(path)
                if df is not None:
                    df['sourceDatabase'] = 'DisGeNET'
                    result[DISGENET_DISEASE_CLASSIFICATIONS] = df
                    logger.info(f"✓ Parsed {len(df)} disease classifications from {label}")

        if not result:
            logger.warning(
                "No DisGeNET data files found. "
                "Run with an API key or download files manually."
            )

        return result

    # ------------------------------------------------------------------
    # get_schema
    # ------------------------------------------------------------------

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for DisGeNET data.

        Returns:
            Dictionary describing the schema for associations, mappings,
            and classifications.
        """
        return {
            DISGENET_GENE_DISEASE_ASSOCIATIONS: {
                'geneId': 'NCBI Gene ID',
                'geneSymbol': 'Gene symbol',
                'geneType': 'Gene NCBI type',
                'diseaseId': 'Disease identifier (UMLS CUI)',
                'diseaseName': 'Disease name',
                'diseaseClasses_MSH': 'MeSH disease classifications (comma-separated)',
                'diseaseClasses_UMLS_ST': 'UMLS semantic type classifications (comma-separated)',
                'diseaseClasses_DO': 'Disease Ontology classifications (comma-separated)',
                'diseaseClasses_HPO': 'Human Phenotype Ontology classifications (comma-separated)',
                'diseaseMapping': 'Disease codes across various vocabularies (comma-separated)',
                'diseaseType': 'Disease type',
                'score': 'Association score',
                'sourceDatabase': 'Source database',
            },
            DISGENET_DISEASE_MAPPINGS: {
                'diseaseName': 'Disease name',
                'diseaseId': 'Disease identifier (UMLS CUI)',
                'MSH': 'MeSH disease code',
                'ICD10': 'ICD-10 code',
                'NCI': 'NCI Thesaurus code',
                'OMIM': 'OMIM code',
                'ICD9CM': 'ICD-9-CM code',
                'HPO': 'Human Phenotype Ontology code',
                'DO': 'Disease Ontology code',
                'MONDO': 'MONDO code',
                'UMLS': 'UMLS semantic type code',
                'ORDO': 'Orphanet code',
                'EFO': 'Experimental Factor Ontology code',
                'sourceDatabase': 'Source database',
            },
            DISGENET_DISEASE_CLASSIFICATIONS: {
                'diseaseName': 'Disease name',
                'diseaseId': 'Disease identifier (UMLS CUI)',
                'diseaseClasses_MSH': 'MeSH disease classifications (comma-separated)',
                'diseaseClasses_UMLS_ST': 'UMLS semantic type classifications (comma-separated)',
                'diseaseClasses_DO': 'Disease Ontology classifications (comma-separated)',
                'diseaseClasses_HPO': 'Human Phenotype Ontology classifications (comma-separated)',
                'sourceDatabase': 'Source database',
            },
        }

    # ------------------------------------------------------------------
    # filter_associations_by_disease
    # ------------------------------------------------------------------

    def filter_associations_by_disease(
        self,
        assoc_df: pd.DataFrame,
        terms: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Filter associations by disease terms.

        Args:
            assoc_df: DataFrame of all gene-disease associations.
            terms: List of disease name substrings to match (case-insensitive).
                   If None, uses self.disease_terms.

        Returns:
            Filtered DataFrame of matching associations.
        """
        if terms is None:
            terms = self.disease_terms

        logger.info(f"Filtering associations for disease terms: {terms}")
        pattern = "|".join(terms)
        mask = assoc_df['diseaseName'].str.contains(pattern, case=False, na=False)
        filtered = assoc_df[mask].copy()

        logger.info(f"Found {len(filtered)} matching gene-disease associations")
        if len(filtered) > 0:
            unique_diseases = filtered['diseaseName'].unique()
            logger.info(f"Unique diseases matched: {len(unique_diseases)}")
            for disease in unique_diseases[:5]:
                logger.info(f"  - {disease}")

        return filtered
