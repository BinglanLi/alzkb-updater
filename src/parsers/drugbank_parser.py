"""
DrugBankParser: Parser for DrugBank data with authentication support.

DrugBank is a comprehensive database of drug information including
drug targets, interactions, and pharmacology.

Source: https://go.drugbank.com/releases/latest
Note: Requires free academic account for access.
"""

import logging
import os
from typing import Dict, Optional, List
import pandas as pd
import requests
from bs4 import BeautifulSoup
import zipfile
import io
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class DrugBankParser(BaseParser):
    """
    Parser for DrugBank data with authentication support.
    
    Supports both authenticated download and manual file-based parsing.
    """
    
    LOGIN_URL = "https://go.drugbank.com/public_users/log_in"
    DOWNLOAD_URL = "https://go.drugbank.com/releases/latest"
    
    def __init__(self, data_dir: str, username: Optional[str] = None, 
                 password: Optional[str] = None):
        """
        Initialize DrugBank parser.
        
        Args:
            data_dir: Directory for storing data files
            username: DrugBank username (optional)
            password: DrugBank password (optional)
        """
        super().__init__(data_dir)
        self.username = username or os.getenv('DRUGBANK_USERNAME')
        self.password = password or os.getenv('DRUGBANK_PASSWORD')
        self.session = requests.Session()
        
        if self.username and self.password:
            logger.info("DrugBank credentials configured")
        else:
            logger.warning("No DrugBank credentials provided. Will attempt file-based parsing.")
    
    def download_data(self) -> bool:
        """
        Download or check for DrugBank data.
        
        If credentials are available, attempts authenticated download.
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
        logger.info("Note: DrugBank data must be downloaded manually from:")
        logger.info("  https://go.drugbank.com/releases/latest")
        logger.info("  Required file: drug_links.csv (from External Links section)")
        
        # Check for drug_links file
        drug_links_path = self.get_file_path("drug_links.csv")
        
        if os.path.exists(drug_links_path):
            logger.info(f"✓ Found drug_links.csv")
            return True
        else:
            logger.error(f"✗ drug_links.csv not found at: {drug_links_path}")
            logger.error("Please download manually or provide credentials")
            return False
    
    def _login(self) -> bool:
        """
        Login to DrugBank.
        
        Returns:
            True if login successful, False otherwise.
        """
        logger.info("Logging in to DrugBank...")
        
        try:
            # Get login page to extract CSRF token
            response = self.session.get(self.LOGIN_URL, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            csrf_token = soup.find('meta', {'name': 'csrf-token'})
            
            if csrf_token:
                csrf_token = csrf_token.get('content')
            else:
                logger.warning("Could not find CSRF token")
                csrf_token = None
            
            # Prepare login data
            login_data = {
                'user[email]': self.username,
                'user[password]': self.password,
            }
            
            if csrf_token:
                login_data['authenticity_token'] = csrf_token
            
            # Perform login
            response = self.session.post(
                self.LOGIN_URL,
                data=login_data,
                timeout=30,
                allow_redirects=True
            )
            
            # Check if login was successful
            if 'logout' in response.text.lower() or response.url != self.LOGIN_URL:
                logger.info("✓ Successfully logged in to DrugBank")
                return True
            else:
                logger.error("Login failed - invalid credentials or CSRF issue")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Login request failed: {e}")
            return False
    
    def _download_with_auth(self) -> bool:
        """
        Download DrugBank data with authentication.
        
        Returns:
            True if successful, False otherwise.
        """
        logger.info("Downloading DrugBank data with authentication...")
        
        # Login first
        if not self._login():
            logger.error("Failed to login to DrugBank")
            return False
        
        try:
            # Navigate to downloads page
            response = self.session.get(self.DOWNLOAD_URL, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find download link for external drug links
            # The exact selector may need adjustment based on DrugBank's current HTML structure
            download_links = soup.find_all('a', href=True)
            
            drug_links_url = None
            for link in download_links:
                href = link.get('href', '')
                text = link.get_text().lower()
                
                if 'external' in text and 'link' in text:
                    drug_links_url = href
                    break
                elif 'drug_links' in href:
                    drug_links_url = href
                    break
            
            if not drug_links_url:
                logger.error("Could not find drug links download URL")
                logger.info("Available download links:")
                for link in download_links[:10]:
                    logger.info(f"  - {link.get_text()}: {link.get('href')}")
                return False
            
            # Make URL absolute if needed
            if not drug_links_url.startswith('http'):
                drug_links_url = f"https://go.drugbank.com{drug_links_url}"
            
            logger.info(f"Downloading from: {drug_links_url}")
            
            # Download the file
            response = self.session.get(drug_links_url, timeout=60)
            response.raise_for_status()
            
            # Save to file
            output_path = self.get_file_path("drug_links.csv")
            
            # Check if response is a zip file
            if drug_links_url.endswith('.zip') or response.headers.get('content-type') == 'application/zip':
                # Extract zip file
                with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                    # Find CSV file in zip
                    csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
                    if csv_files:
                        with zf.open(csv_files[0]) as csv_file:
                            with open(output_path, 'wb') as out_file:
                                out_file.write(csv_file.read())
                        logger.info(f"✓ Extracted and saved to {output_path}")
                    else:
                        logger.error("No CSV file found in zip archive")
                        return False
            else:
                # Save directly
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"✓ Downloaded to {output_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            logger.info("You may need to download manually from DrugBank website")
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
        drug_links_file = self.get_file_path("drug_links.csv")
        
        if not os.path.exists(drug_links_file):
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
                    'PubChem Compound ID': 'pubchem_cid',
                    'PubChem Substance ID': 'pubchem_sid',
                    'ChEMBL ID': 'chembl_id',
                    'ChEBI ID': 'chebi_id',
                    'KEGG Compound ID': 'kegg_compound_id',
                    'KEGG Drug ID': 'kegg_drug_id'
                }
                
                # Rename columns that exist
                existing_cols = {k: v for k, v in column_mapping.items() if k in drugs_df.columns}
                drugs_df = drugs_df.rename(columns=existing_cols)
                
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
            'drugs': {
                'drugbank_id': 'DrugBank identifier',
                'drug_name': 'Drug name',
                'cas_number': 'CAS Registry Number',
                'pubchem_cid': 'PubChem Compound ID',
                'chembl_id': 'ChEMBL identifier',
                'chebi_id': 'ChEBI identifier',
                'kegg_compound_id': 'KEGG Compound ID',
                'kegg_drug_id': 'KEGG Drug ID'
            }
        }
    
    def filter_alzheimer_drugs(self, drugs_df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter drugs for those used in Alzheimer's disease.
        
        Args:
            drugs_df: DataFrame of all drugs
        
        Returns:
            Filtered DataFrame of Alzheimer's-related drugs
        """
        logger.info("Filtering for Alzheimer's-related drugs...")
        
        # Known Alzheimer's drugs
        known_ad_drugs = [
            'donepezil', 'rivastigmine', 'galantamine', 'memantine',
            'aducanumab', 'lecanemab', 'tacrine', 'solanezumab',
            'gantenerumab', 'donanemab'
        ]
        
        mask = drugs_df['drug_name'].str.lower().isin(known_ad_drugs)
        
        alzheimer_drugs = drugs_df[mask].copy()
        
        logger.info(f"✓ Found {len(alzheimer_drugs)} known Alzheimer's drugs")
        
        if len(alzheimer_drugs) > 0:
            logger.info("Drugs found:")
            for _, drug in alzheimer_drugs.iterrows():
                logger.info(f"  - {drug.get('drug_name', 'Unknown')}")
        
        return alzheimer_drugs
    
    def export_to_tsv(self, data: Dict[str, pd.DataFrame], output_dir: str) -> List[str]:
        """
        Export parsed data to TSV files for ista.
        
        Args:
            data: Dictionary of DataFrames
            output_dir: Output directory path
            
        Returns:
            List of created file paths
        """
        logger.info("Exporting DrugBank data to TSV for ista...")
        
        os.makedirs(output_dir, exist_ok=True)
        created_files = []
        
        # Export drugs
        if 'drugs' in data:
            drugs_df = data['drugs']
            
            # Filter for Alzheimer's drugs
            alzheimer_drugs = self.filter_alzheimer_drugs(drugs_df)
            
            # Export all drugs
            output_path = os.path.join(output_dir, 'drugbank_drugs.tsv')
            drugs_df.to_csv(output_path, sep='\t', index=False)
            created_files.append(output_path)
            logger.info(f"✓ Exported {len(drugs_df)} drugs to {output_path}")
            
            # Export Alzheimer's drugs separately
            if len(alzheimer_drugs) > 0:
                ad_output_path = os.path.join(output_dir, 'drugbank_alzheimer_drugs.tsv')
                alzheimer_drugs.to_csv(ad_output_path, sep='\t', index=False)
                created_files.append(ad_output_path)
                logger.info(f"✓ Exported {len(alzheimer_drugs)} Alzheimer's drugs to {ad_output_path}")
        
        return created_files
