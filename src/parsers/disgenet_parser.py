"""
DisGeNETParser: Parser for DisGeNET data with API support.

DisGeNET is a comprehensive database of gene-disease associations
from various sources including literature and databases.

Source: https://www.disgenet.org/
API Documentation: https://www.disgenet.org/api/
"""

import logging
import os
from typing import Dict, Optional, List, Tuple
import pandas as pd
import requests
import time
from .base_parser import BaseParser
from pathlib import Path
from ontology_configs import (
    DISGENET_DISEASE_CLASSIFICATIONS,
    DISGENET_DISEASE_MAPPINGS,
    DISGENET_GENE_DISEASE_ASSOCIATIONS,
)

logger = logging.getLogger(__name__)


class DisGeNETParser(BaseParser):
    """
    Parser for DisGeNET gene-disease association data with API support.

    Supports both API-based retrieval and manual file-based parsing.
    """

    API_BASE_URL = "https://api.disgenet.com/api/v1"
    
    def __init__(self, data_dir: str, api_key: Optional[str] = None):
        """
        Initialize DisGeNET parser.
        
        Args:
            data_dir: Directory for storing data files
            api_key: DisGeNET API key (optional, for API access)
        """
        super().__init__(data_dir)
        self.api_key = api_key or os.getenv('DISGENET_API_KEY')
        self.session = requests.Session()
        
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

        First retrieves Alzheimer's disease IDs and metadata, then fetches gene-disease associations.

        Returns:
            True if successful, False otherwise.
        """
        logger.info("Downloading DisGeNET data via API...")

        try:
            # Step 1: Get Alzheimer's disease IDs and metadata
            disease_classifications, disease_mappings = self.get_alzheimer_disease_ids()

            if disease_classifications is None or disease_mappings is None:
                logger.error("Failed to retrieve Alzheimer's disease IDs from API")
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
    
    
    def get_alzheimer_disease_ids(self) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Get Alzheimer's disease IDs and related information from DisGeNET API using free text search.

        Returns:
            Tuple of two DataFrames:
            - {{DISGENET_DISEASE_CLASSIFICATIONS}}: Contains disease classification information across ontology systems
            - {{DISGENET_DISEASE_MAPPINGS}}: Contains disease code mappings across vocabularies
        """
        logger.info("Querying DisGeNET API for Alzheimer's disease entities...")

        # API endpoint for disease entity search
        endpoint = f"{self.API_BASE_URL}/entity/disease"
        params = {
            'disease_free_text_search_string': 'alzheimer',
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
    
    def filter_alzheimer_associations(self, assoc_df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter associations for Alzheimer's disease.
        
        Args:
            assoc_df: DataFrame of all gene-disease associations
        
        Returns:
            Filtered DataFrame of Alzheimer's-related associations
        """
        logger.info("Filtering for Alzheimer's disease associations...")
        
        # Search for Alzheimer's in disease name
        mask = assoc_df['diseaseName'].str.contains(
            'Alzheimer', case=False, na=False
        )
        
        alzheimer_assoc = assoc_df[mask].copy()
        
        logger.info(f"✓ Found {len(alzheimer_assoc)} Alzheimer's gene-disease associations")
        
        if len(alzheimer_assoc) > 0:
            # Show unique diseases
            unique_diseases = alzheimer_assoc['diseaseName'].unique()
            logger.info(f"Unique Alzheimer's diseases: {len(unique_diseases)}")
            for disease in unique_diseases[:5]:
                logger.info(f"  - {disease}")
            
            # Show top associated genes
            top_genes = alzheimer_assoc['geneSymbol'].value_counts().head(10)
            logger.info(f"Top associated genes: {dict(top_genes)}")
        
        return alzheimer_assoc
