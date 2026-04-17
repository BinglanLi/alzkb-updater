"""
DrugBankParser: Parser for DrugBank drug data with authentication support.

DrugBank is a comprehensive database of drug information including
drug targets, interactions, and pharmacology.

Source: https://go.drugbank.com/releases/latest
Note: Requires free academic account for access.

Download Example:
    curl -Lfv -o filename.zip -u username:password \\
        https://go.drugbank.com/releases/5-1-14/downloads/all-drug-links

Disease-specific drug filtering is configurable via the disease_scope parameter.
"""

import logging
import os
import pandas as pd
import requests
import zipfile
import io

from pathlib import Path
from typing import Dict, Optional, List
from .base_parser import BaseParser

DRUGBANK_DRUGS = 'drugs'

logger = logging.getLogger(__name__)


class DrugBankParser(BaseParser):
    """
    Parser for DrugBank data with HTTP Basic Authentication support.

    Supports both authenticated download and manual file-based parsing.
    Uses HTTP Basic Auth as shown in DrugBank's curl examples.
    """

    BASE_URL = "https://go.drugbank.com"

    def __init__(self, data_dir: str, username: Optional[str] = None,
                 password: Optional[str] = None, version: str = "latest",
                 disease_scope: Optional[Dict] = None):
        """
        Initialize DrugBank parser.

        Args:
            data_dir: Directory for storing data files.
            username: DrugBank username/email (optional).
            password: DrugBank password (optional).
            version: DrugBank release version (e.g., "5-1-14" or "latest").
            disease_scope: Disease scope dict from project config. If provided,
                           filter_drugs_by_indication() reads drug_names from it.
        """
        super().__init__(data_dir)
        self.username = username or os.getenv('DRUGBANK_USERNAME')
        self.password = password or os.getenv('DRUGBANK_PASSWORD')
        self.version = version
        self.disease_scope = disease_scope
        self.session = requests.Session()

        if self.username and self.password:
            self.session.auth = (self.username, self.password)
            logger.info("DrugBank credentials configured with HTTP Basic Auth")
        else:
            logger.warning("No DrugBank credentials provided. Will attempt file-based parsing.")
    
    def download_data(self) -> bool:
        """
        Download or check for DrugBank data.

        If credentials are available, attempts authenticated download using HTTP Basic Auth.
        Otherwise, checks for manually downloaded files.

        Returns:
            True if data is available, False otherwise.
        """
        if self.username and self.password:
            return self._download_with_auth()
        else:
            return self._check_manual_files()

    def _check_manual_files(self) -> bool:
        """Check for manually downloaded DrugBank files."""
        logger.info("Checking for DrugBank data files...")
        logger.info("Note: DrugBank data must be downloaded manually using curl:")
        logger.info(f"  curl -Lfv -o {DRUGBANK_DRUGS}.zip -u username:password \\")
        logger.info(f"    {self.BASE_URL}/releases/latest/downloads/all-drug-links")
        logger.info(f"  Required file: {DRUGBANK_DRUGS}.csv (extract from zip)")

        # Check for drug_links file
        drug_links_path = self.get_file_path(f"{DRUGBANK_DRUGS}.csv")

        if os.path.exists(drug_links_path):
            logger.info(f"✓ Found {DRUGBANK_DRUGS}.csv")
            return True
        else:
            logger.error(f"✗ {DRUGBANK_DRUGS}.csv not found at: {drug_links_path}")
            logger.error("Please download manually or provide credentials")
            return False

    def _download_with_auth(self) -> bool:
        """
        Download DrugBank data with HTTP Basic Authentication.

        Uses the same approach as the curl command:
        curl -Lfv -o filename.zip -u username:password URL

        Returns:
            True if successful, False otherwise.
        """
        output_path = Path(self.get_file_path(f"{DRUGBANK_DRUGS}.csv"))
        if output_path.exists() and not self.force:
            logger.info(f"File already exists: {output_path}")
            return True

        logger.info("Downloading DrugBank data with HTTP Basic Authentication...")

        # Construct download URL
        download_url = f"{self.BASE_URL}/releases/{self.version}/downloads/all-drug-links"
        logger.info(f"Downloading from: {download_url}")

        try:
            # Download the file using HTTP Basic Auth
            # The session already has auth set up in __init__
            response = self.session.get(
                download_url,
                timeout=120,
                allow_redirects=True,  # Like curl's -L flag
                stream=True  # For large files
            )
            response.raise_for_status()

            logger.info(f"✓ Download successful (Content-Type: {response.headers.get('content-type', 'unknown')})")

            # Check if response is a zip file
            content_type = response.headers.get('content-type', '')
            if 'zip' in content_type or download_url.endswith('.zip'):
                logger.info("Extracting ZIP archive...")
                # Extract zip file
                with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                    # Find CSV file in zip
                    csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
                    if csv_files:
                        logger.info(f"Found CSV file: {csv_files[0]}")
                        with zf.open(csv_files[0]) as csv_file:
                            with open(output_path, 'wb') as out_file:
                                out_file.write(csv_file.read())
                        logger.info(f"✓ Extracted and saved to {output_path}")
                    else:
                        logger.error("No CSV file found in zip archive")
                        logger.info(f"Files in archive: {zf.namelist()}")
                        return False
            else:
                # Save directly as CSV
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"✓ Downloaded to {output_path}")

            return True

        except requests.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed - invalid username or password")
            elif e.response.status_code == 403:
                logger.error("Access forbidden - check account permissions")
            elif e.response.status_code == 404:
                logger.error(f"File not found at {download_url}")
                logger.info("Try using a specific version instead of 'latest'")
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e}")
            return False
        except requests.RequestException as e:
            logger.error(f"Download failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse DrugBank data.
        
        Returns:
            Dictionary with 'drugs' DataFrame.
        """
        logger.info("Parsing DrugBank data...")
        
        result = {}
        
        # Parse drug links file
        drug_links_file = self.get_file_path(f"{DRUGBANK_DRUGS}.csv")
        
        if not Path(drug_links_file).exists():
            logger.error(f"Drug links file not found: {drug_links_file}")
            return result
        
        try:
            drugs_df = self.read_csv(drug_links_file)
            
            if drugs_df is not None:
                # Rename columns for consistency
                column_mapping = {
                    'DrugBank ID': 'drugbank_id',
                    'Name': 'drug_name',
                    'CAS Number': 'cas_number',
                    'Drug Type': 'drug_type',
                    'PubChem Compound ID': 'pubchem_cid',
                    'PubChem Substance ID': 'pubchem_sid',
                    'ChEMBL ID': 'chembl_id',
                    'ChEBI ID': 'chebi_id',
                    'KEGG Compound ID': 'kegg_compound_id',
                    'KEGG Drug ID': 'kegg_drug_id',
                    'PharmGKB ID': 'pharmgkb_id',
                    'Uniprot Title': 'uniprot_title',
                    'UniProt ID': 'uniprot_id',
                    'GenBank ID': 'genbank_id',
                }
                
                # Rename columns that exist
                existing_cols = {k: v for k, v in column_mapping.items() if k in drugs_df.columns}
                drugs_df = drugs_df.rename(columns=existing_cols)
                
                # Add source database column
                drugs_df['source_database'] = 'DrugBank'
                
                result['drugs'] = drugs_df
                logger.info(f"✓ Parsed {len(drugs_df)} drugs")
                
        except Exception as e:
            logger.error(f"Failed to parse DrugBank data: {e}")
        
        return result
    
    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for DrugBank data.
        
        Returns:
            Dictionary describing the schema for drugs.
        """
        return {
            f'{DRUGBANK_DRUGS}': {
                'drugbank_id': 'DrugBank identifier',
                'drug_name': 'Drug name',
                'cas_number': 'CAS Registry Number',
                'drug_type': 'Drug type',
                'pubchem_cid': 'PubChem Compound ID',
                'pubchem_sid': 'PubChem Substance ID',
                'chembl_id': 'ChEMBL identifier',
                'chebi_id': 'ChEBI identifier',
                'kegg_compound_id': 'KEGG Compound ID',
                'kegg_drug_id': 'KEGG Drug ID',
                'pharmgkb_id': 'PharmGKB ID',
                'uniprot_title': 'Uniprot Title',
                'uniprot_id': 'UniProt ID',
                'genbank_id': 'GenBank ID',
                'source_database': 'Source database (DrugBank)',
            }
        }
    
    def filter_drugs_by_indication(self, drugs_df: pd.DataFrame,
                                    drug_names: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Filter drugs by known indication drug names.

        Args:
            drugs_df: DataFrame of all drugs.
            drug_names: List of drug names to filter for (case-insensitive).
                        If None, reads from disease_scope.drug_names in project config.
                        If no drug_names configured, returns unfiltered.

        Returns:
            Filtered DataFrame of matching drugs.
        """
        if drug_names is None:
            if self.disease_scope and self.disease_scope.get("drug_names"):
                drug_names = self.disease_scope["drug_names"]
            else:
                logger.warning(
                    "No drug_names in disease_scope; returning unfiltered drug list. "
                    "Add disease_scope.drug_names to project.yaml to filter by indication."
                )
                return drugs_df

        logger.info(f"Filtering for {len(drug_names)} known drugs...")

        drug_names_lower = [n.lower() for n in drug_names]
        mask = drugs_df['drug_name'].str.lower().isin(drug_names_lower)
        filtered = drugs_df[mask].copy()

        logger.info(f"Found {len(filtered)} matching drugs")

        if len(filtered) > 0:
            for _, drug in filtered.iterrows():
                logger.info(f"  - {drug.get('drug_name', 'Unknown')}")

        return filtered
