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
from typing import Dict, Optional, List, Tuple
import pandas as pd
import requests
import time
from .base_parser import BaseParser

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

    API_BASE_URL = "https://api.disgenet.com/api/v1"

    def __init__(self, data_dir: str, api_key: Optional[str] = None,
                 disease_scope: Optional[Dict] = None):
        """
        Initialize DisGeNET parser.

        Args:
            data_dir: Directory for storing data files.
            api_key: DisGeNET API key (optional, for API access).
            disease_scope: Disease scope dict from project config. Required key:
                           primary_terms (list of search strings).
        """
        super().__init__(data_dir)
        self.api_key = api_key or os.getenv('DISGENET_API_KEY')
        self.session = requests.Session()

        # Disease scope configuration — required for API-based querying
        if disease_scope and disease_scope.get("primary_terms"):
            self.disease_terms = disease_scope["primary_terms"]
        else:
            raise ValueError(
                "DisGeNETParser requires 'disease_scope.primary_terms' in project.yaml. "
                "Set disease_scope_mode: none in databases.yaml to skip disease filtering."
            )

        if self.api_key:
            self.session.headers.update({
                'Authorization': self.api_key,
                'accept': 'application/json',
            })
            logger.info("DisGeNET API key configured")
        else:
            logger.warning("No DisGeNET API key provided. Will attempt file-based parsing.")
    
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
            f"{DISGENET_DISEASE_MAPPINGS}.tsv"
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

        Retrieves disease IDs matching the configured disease scope, then
        fetches gene-disease associations for each.

        Returns:
            True if successful, False otherwise.
        """
        logger.info(f"Downloading DisGeNET data via API (disease terms: {self.disease_terms})...")

        try:
            # Step 1: Get disease IDs and metadata for configured terms
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

            # Step 2: Get unique disease IDs from disease_mappings
            unique_disease_ids = disease_mappings['diseaseId'].dropna().unique().tolist()
            logger.info(f"✓ Found {len(unique_disease_ids)} unique disease IDs")

            if not unique_disease_ids:
                logger.warning("No disease IDs found to query associations")
                return False

            # Step 3: Fetch gene-disease associations for each disease ID
            all_associations = []
            for disease_id in unique_disease_ids:
                logger.info(f"Fetching associations for disease ID: {disease_id}")
                associations = self._get_disease_associations_by_id(disease_id)

                if associations is not None and len(associations) > 0:
                    all_associations.append(associations)
                    logger.info(f"  ✓ Retrieved {len(associations)} associations")
                else:
                    logger.warning(f"  No associations found for {disease_id}")

                # Rate limiting - be respectful to the API
                time.sleep(0.5)

            # Step 4: Combine all associations
            if all_associations:
                combined_associations = pd.concat(all_associations, ignore_index=True)

                # Remove duplicates if any
                initial_count = len(combined_associations)
                combined_associations = combined_associations.drop_duplicates()
                final_count = len(combined_associations)

                if initial_count != final_count:
                    logger.info(f"Removed {initial_count - final_count} duplicate associations")

                # Save combined associations
                output_path = self.get_file_path(f"api_{DISGENET_GENE_DISEASE_ASSOCIATIONS}.tsv")
                combined_associations.to_csv(output_path, sep='\t', index=False)
                logger.info(f"✓ Downloaded {len(combined_associations)} total gene-disease associations via API")

                return True
            else:
                logger.error("No gene-disease associations retrieved")
                return False

        except Exception as e:
            logger.error(f"API download failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    
    def get_disease_ids(self, search_terms: Optional[List[str]] = None) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Get disease IDs and related information from DisGeNET API using free text search.

        Args:
            search_terms: List of disease search strings (e.g., ["alzheimer"]).
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
        Query DisGeNET API for a single disease search term.

        Args:
            search_term: Free text disease search string.

        Returns:
            Tuple of (classifications_df, mappings_df) or (None, None).
        """
        endpoint = f"{self.API_BASE_URL}/entity/disease"
        params = {
            'disease_free_text_search_string': search_term,
        }

        # Make the API call 
        try:
            response = self.session.get(
                endpoint, 
                params=params, 
                timeout=30)
            response.raise_for_status()

            data = response.json()

            if 'payload' not in data:
                logger.warning("No disease entities found in API response")
                return None, None

            payload = data['payload']
            logger.info(f"✓ Retrieved {len(payload)} disease entities from API")

            # Create disease_classifications DataFrame
            classifications_data = []
            for item in payload:
                # Concatenate disease classes with commas
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
            logger.info(f"✓ Created {DISGENET_DISEASE_CLASSIFICATIONS} with {len(disease_classifications)} rows")

            # Create disease_mappings DataFrame
            mappings_data = []
            for item in payload:
                base_data = {
                    'diseaseName': item.get('name', ''),
                    'diseaseId': item.get('diseaseUMLSCUI', '')
                }

                # Extract disease codes and create columns based on vocabulary
                disease_codes = item.get('diseaseCodes', [])
                code_dict = {}
                for code_item in disease_codes:
                    vocabulary = code_item.get('vocabulary', '')
                    code = code_item.get('code', '')
                    if vocabulary:
                        code_dict[vocabulary] = code

                # Combine base data with code mappings
                row_data = {**base_data, **code_dict}
                mappings_data.append(row_data)

            disease_mappings = pd.DataFrame(mappings_data)
            disease_mappings['sourceDatabase'] = 'DisGeNET'
            logger.info(f"✓ Created {DISGENET_DISEASE_MAPPINGS} with {len(disease_mappings)} rows and {len(disease_mappings.columns)} columns")

            return disease_classifications, disease_mappings

        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None, None
        except Exception as e:
            logger.error(f"Error processing disease entities: {e}")
            return None, None


    def _get_disease_associations_by_id(self, disease_id: str, 
                                         limit: int = 10000) -> Optional[pd.DataFrame]:
        """
        Get disease-gene associations from DisGeNET API using disease ID.
        
        Args:
            disease_id: Disease ID (UMLS CUI, e.g., C0002395 for Alzheimer's)
            limit: Maximum number of results
            
        Returns:
            DataFrame of associations or None if failed
        """
        logger.info(f"Querying DisGeNET API for disease ID: {disease_id}")
        
        # Get gene-disease associations
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
            
            # Create a disease-gene association DataFrame
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
    
    
    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse DisGeNET data.

        Returns:
            Dictionary with 'gene_disease_associations', 'disease_mappings', and 'disease_classifications' DataFrames.
        """
        logger.info("Parsing DisGeNET data...")

        result = {}

        # Try API file first for gene-disease associations
        api_gda_file = self.get_file_path(f"api_{DISGENET_GENE_DISEASE_ASSOCIATIONS}.tsv")
        logger.info("Using API-downloaded gene-disease associations data")
        try:
            assoc_df = self.read_tsv(api_gda_file)
            if assoc_df is not None:
                assoc_df['sourceDatabase'] = 'DisGeNET'
                result['gene_disease_associations'] = assoc_df
                logger.info(f"✓ Parsed {len(assoc_df)} gene-disease associations from API")
        except FileNotFoundError:
            logger.error(f"Gene-disease associations file not found: {api_gda_file}")
        except Exception as e:
            logger.error(f"Failed to parse API gene-disease associations: {e}")

        # Fall back to manual files
        if 'gene_disease_associations' not in result:
            logger.info("Using manually downloaded gene-disease associations data as fallback")
            gda_file = self.get_file_path(f"{DISGENET_GENE_DISEASE_ASSOCIATIONS}.tsv")
            try:
                assoc_df = self.read_tsv(gda_file)
                if assoc_df is not None:
                    assoc_df['sourceDatabase'] = 'DisGeNET'
                    result['gene_disease_associations'] = assoc_df
                    logger.info(f"✓ Parsed {len(assoc_df)} gene-disease associations")
            except FileNotFoundError:
                logger.error(f"Gene-disease associations file not found: {gda_file}")
            except Exception as e:
                logger.error(f"Failed to parse gene-disease associations: {e}")

        # Parse API disease mappings if available
        api_mappings_file = self.get_file_path(f"api_{DISGENET_DISEASE_MAPPINGS}.tsv")
        logger.info("Using API-downloaded disease mappings data")
        try:
            mappings_df = self.read_tsv(api_mappings_file)

            if mappings_df is not None:
                mappings_df['sourceDatabase'] = 'DisGeNET'
                result['disease_mappings'] = mappings_df
            logger.info(f"✓ Parsed {len(mappings_df)} disease mappings from API")

        except FileNotFoundError:
            logger.error(f"Disease mappings file not found: {api_mappings_file}")
        except Exception as e:
            logger.error(f"Failed to parse API disease mappings: {e}")

        # Fall back to manually downloaded disease mappings file
        if 'disease_mappings' not in result:
            logger.info("Using manually downloaded disease mappings data as fallback")
            mappings_file = self.get_file_path(f"{DISGENET_DISEASE_MAPPINGS}.tsv")
            try:
                mappings_df = self.read_tsv(mappings_file)
                if mappings_df is not None:
                    mappings_df['sourceDatabase'] = 'DisGeNET'
                    result['disease_mappings'] = mappings_df
                    logger.info(f"✓ Parsed {len(mappings_df)} disease mappings")
            except FileNotFoundError:
                logger.error(f"Disease mappings file not found: {mappings_file}")
            except Exception as e:
                logger.error(f"Failed to parse disease mappings: {e}")
        
        # Parse API disease classifications if available
        api_classifications_file = self.get_file_path(f"api_{DISGENET_DISEASE_CLASSIFICATIONS}.tsv")
        logger.info("Using API-downloaded disease classifications data")
        try:
            classifications_df = self.read_tsv(api_classifications_file)

            if classifications_df is not None:
                classifications_df['sourceDatabase'] = 'DisGeNET'
                result['disease_classifications'] = classifications_df
                logger.info(f"✓ Parsed {len(classifications_df)} disease classifications from API")

        except FileNotFoundError:
            logger.error(f"Disease classifications file not found: {api_classifications_file}")
        except Exception as e:
                logger.error(f"Failed to parse API disease classifications: {e}")

        # Fall back to manually downloaded disease classifications file
        if 'disease_classifications' not in result:
            logger.info("Using manually downloaded disease classifications data as fallback")
            classifications_file = self.get_file_path(f"{DISGENET_DISEASE_CLASSIFICATIONS}.tsv")
            try:
                classifications_df = self.read_tsv(classifications_file)
                if classifications_df is not None:
                    classifications_df['sourceDatabase'] = 'DisGeNET'
                    result['disease_classifications'] = classifications_df
                    logger.info(f"✓ Parsed {len(classifications_df)} disease classifications")
            except FileNotFoundError:
                logger.error(f"Disease classifications file not found: {classifications_file}")
            except Exception as e:
                logger.error(f"Failed to parse disease classifications: {e}")

        return result
    
    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for DisGeNET data.

        Returns:
            Dictionary describing the schema for associations, mappings, and classifications.
        """
        return {
            f'{DISGENET_GENE_DISEASE_ASSOCIATIONS}': {
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
            f'{DISGENET_DISEASE_MAPPINGS}': {
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
            f'{DISGENET_DISEASE_CLASSIFICATIONS}': {
                'diseaseName': 'Disease name',
                'diseaseId': 'Disease identifier (UMLS CUI)',
                'diseaseClasses_MSH': 'MeSH disease classifications (comma-separated)',
                'diseaseClasses_UMLS_ST': 'UMLS semantic type classifications (comma-separated)',
                'diseaseClasses_DO': 'Disease Ontology classifications (comma-separated)',
                'diseaseClasses_HPO': 'Human Phenotype Ontology classifications (comma-separated)',
                'sourceDatabase': 'Source database',
            }
        }
    
    def filter_associations_by_disease(self, assoc_df: pd.DataFrame,
                                       terms: Optional[List[str]] = None) -> pd.DataFrame:
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

