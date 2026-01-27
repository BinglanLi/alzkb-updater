"""
MEDLINE Cooccurrence Parser for AlzKB.

This module parses MEDLINE co-occurrence data to extract:
- Disease-Symptom (presents) edges (DpS) via PubMed co-occurrence
- Disease-Anatomy (localizes) edges (DlA) via PubMed co-occurrence
- Disease-Disease (resembles) edges (DrD) via PubMed co-occurrence

Data Source: https://github.com/dhimmel/medline
Pre-computed cooccurrence files are used when available.

Output:
  - disease_symptom_cooccurrence.tsv: DpS edges (3,758)
  - disease_anatomy_cooccurrence.tsv: DlA edges (4,335)
  - disease_disease_cooccurrence.tsv: DrD edges (250)
"""

import logging
from pathlib import Path
from typing import Dict, Optional
import pandas as pd

from ..base_parser import BaseParser

logger = logging.getLogger(__name__)


class MEDLINECooccurrenceParser(BaseParser):
    """
    Parser for MEDLINE literature co-occurrence data.

    Extracts disease-symptom, disease-anatomy, and disease-disease
    relationships based on PubMed co-occurrence analysis with
    Fisher's exact test for statistical significance.
    """

    # MEDLINE co-occurrence data from dhimmel hetionet repository
    HETIONET_COMMIT = "2cc3e1d7d9c0d3a6be3ed3b2c8b6f1e37be04a1a"
    MEDLINE_BASE_URL = "https://raw.githubusercontent.com/dhimmel/medline"

    # Pre-computed cooccurrence file URLs (from dhimmel/medline repo)
    # These files contain pre-computed Fisher's exact test results
    DISEASE_SYMPTOM_URL = f"{MEDLINE_BASE_URL}/master/data/disease-symptom-cooccurrence.tsv.gz"
    DISEASE_ANATOMY_URL = f"{MEDLINE_BASE_URL}/master/data/disease-uberon-cooccurrence.tsv.gz"
    DISEASE_DISEASE_URL = f"{MEDLINE_BASE_URL}/master/data/disease-disease-cooccurrence.tsv.gz"

    # P-value threshold for significant co-occurrence
    P_FISHER_THRESHOLD = 0.005

    def __init__(self, data_dir: str):
        """
        Initialize the MEDLINE cooccurrence parser.

        Args:
            data_dir: Directory to store downloaded and processed data
        """
        super().__init__(data_dir)
        self.source_name = "medline"

    def download_data(self) -> bool:
        """
        Download MEDLINE co-occurrence data files.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading MEDLINE co-occurrence data...")

        success = True

        # Download disease-symptom cooccurrence
        result = self.download_file(self.DISEASE_SYMPTOM_URL, "disease-symptom-cooccurrence.tsv.gz")
        if result:
            self.extract_gzip(result)
        else:
            logger.warning("Failed to download disease-symptom cooccurrence")
            success = False

        # Download disease-anatomy cooccurrence
        result = self.download_file(self.DISEASE_ANATOMY_URL, "disease-uberon-cooccurrence.tsv.gz")
        if result:
            self.extract_gzip(result)
        else:
            logger.warning("Failed to download disease-anatomy cooccurrence")
            success = False

        # Download disease-disease cooccurrence
        result = self.download_file(self.DISEASE_DISEASE_URL, "disease-disease-cooccurrence.tsv.gz")
        if result:
            self.extract_gzip(result)
        else:
            logger.warning("Failed to download disease-disease cooccurrence")
            success = False

        if success:
            logger.info("Successfully downloaded MEDLINE co-occurrence data")
        else:
            logger.warning("Some MEDLINE files could not be downloaded")

        return success

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse the MEDLINE co-occurrence data files.

        Returns:
            Dictionary with:
              - 'disease_symptom_cooccurrence': DataFrame of DpS edges
              - 'disease_anatomy_cooccurrence': DataFrame of DlA edges
              - 'disease_disease_cooccurrence': DataFrame of DrD edges
        """
        result = {}

        # Parse disease-symptom cooccurrence (DpS)
        dps = self._parse_disease_symptom()
        if dps is not None:
            result["disease_symptom_cooccurrence"] = dps

        # Parse disease-anatomy cooccurrence (DlA)
        dla = self._parse_disease_anatomy()
        if dla is not None:
            result["disease_anatomy_cooccurrence"] = dla

        # Parse disease-disease cooccurrence (DrD)
        drd = self._parse_disease_disease()
        if drd is not None:
            result["disease_disease_cooccurrence"] = drd

        return result

    def _parse_disease_symptom(self) -> Optional[pd.DataFrame]:
        """
        Parse disease-symptom co-occurrence to create DpS (presents) edges.

        Returns:
            DataFrame with Disease-presents-Symptom edge data
        """
        # Try multiple file paths
        possible_paths = [
            self.source_dir / "disease-symptom-cooccurrence.tsv",
            self.source_dir / "disease-symptom-cooccurrence.tsv.gz",
        ]

        for file_path in possible_paths:
            if file_path.exists():
                logger.info(f"Parsing disease-symptom cooccurrence from {file_path}")
                try:
                    df = pd.read_csv(file_path, sep='\t', compression='infer')

                    # Filter by p-value threshold
                    df = df[df['p_fisher'] < self.P_FISHER_THRESHOLD]

                    # Create edge DataFrame
                    edges = pd.DataFrame({
                        'doid_code': df['doid_code'],
                        'mesh_id': df['mesh_id'],
                        'p_fisher': df['p_fisher'],
                        'cooccurrence': df['cooccurrence'] if 'cooccurrence' in df.columns else None,
                        'enrichment': df['enrichment'] if 'enrichment' in df.columns else None,
                        'source': 'MEDLINE cooccurrence',
                        'unbiased': False,
                        'license': 'CC0 1.0',
                        'sourceDatabase': 'MEDLINE'
                    })

                    logger.info(f"Parsed {len(edges)} Disease-presents-Symptom edges")
                    return edges

                except Exception as e:
                    logger.error(f"Error parsing disease-symptom cooccurrence: {e}")

        logger.warning("Disease-symptom cooccurrence file not found")
        return None

    def _parse_disease_anatomy(self) -> Optional[pd.DataFrame]:
        """
        Parse disease-anatomy co-occurrence to create DlA (localizes) edges.

        Returns:
            DataFrame with Disease-localizes-Anatomy edge data
        """
        # Try multiple file paths
        possible_paths = [
            self.source_dir / "disease-uberon-cooccurrence.tsv",
            self.source_dir / "disease-uberon-cooccurrence.tsv.gz",
        ]

        for file_path in possible_paths:
            if file_path.exists():
                logger.info(f"Parsing disease-anatomy cooccurrence from {file_path}")
                try:
                    df = pd.read_csv(file_path, sep='\t', compression='infer')

                    # Filter by p-value threshold
                    df = df[df['p_fisher'] < self.P_FISHER_THRESHOLD]

                    # Create edge DataFrame
                    edges = pd.DataFrame({
                        'doid_code': df['doid_code'],
                        'uberon_id': df['uberon_id'],
                        'p_fisher': df['p_fisher'],
                        'cooccurrence': df['cooccurrence'] if 'cooccurrence' in df.columns else None,
                        'enrichment': df['enrichment'] if 'enrichment' in df.columns else None,
                        'source': 'MEDLINE cooccurrence',
                        'unbiased': False,
                        'license': 'CC0 1.0',
                        'sourceDatabase': 'MEDLINE'
                    })

                    logger.info(f"Parsed {len(edges)} Disease-localizes-Anatomy edges")
                    return edges

                except Exception as e:
                    logger.error(f"Error parsing disease-anatomy cooccurrence: {e}")

        logger.warning("Disease-anatomy cooccurrence file not found")
        return None

    def _parse_disease_disease(self) -> Optional[pd.DataFrame]:
        """
        Parse disease-disease co-occurrence to create DrD (resembles) edges.

        Returns:
            DataFrame with Disease-resembles-Disease edge data
        """
        # Try multiple file paths
        possible_paths = [
            self.source_dir / "disease-disease-cooccurrence.tsv",
            self.source_dir / "disease-disease-cooccurrence.tsv.gz",
        ]

        for file_path in possible_paths:
            if file_path.exists():
                logger.info(f"Parsing disease-disease cooccurrence from {file_path}")
                try:
                    df = pd.read_csv(file_path, sep='\t', compression='infer')

                    # Filter by p-value threshold
                    df = df[df['p_fisher'] < self.P_FISHER_THRESHOLD]

                    # Remove duplicate pairs (keep only one direction)
                    df['pair'] = df.apply(
                        lambda row: frozenset([row['doid_code_0'], row['doid_code_1']]),
                        axis=1
                    )
                    df = df.drop_duplicates(subset=['pair'])
                    df = df.drop(columns=['pair'])

                    # Create edge DataFrame
                    edges = pd.DataFrame({
                        'doid_code_0': df['doid_code_0'],
                        'doid_code_1': df['doid_code_1'],
                        'p_fisher': df['p_fisher'],
                        'cooccurrence': df['cooccurrence'] if 'cooccurrence' in df.columns else None,
                        'enrichment': df['enrichment'] if 'enrichment' in df.columns else None,
                        'source': 'MEDLINE cooccurrence',
                        'unbiased': False,
                        'license': 'CC0 1.0',
                        'sourceDatabase': 'MEDLINE'
                    })

                    logger.info(f"Parsed {len(edges)} Disease-resembles-Disease edges")
                    return edges

                except Exception as e:
                    logger.error(f"Error parsing disease-disease cooccurrence: {e}")

        logger.warning("Disease-disease cooccurrence file not found")
        return None

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for MEDLINE cooccurrence data.

        Returns:
            Dictionary defining the schema for cooccurrence edges
        """
        return {
            "disease_symptom_cooccurrence": {
                "doid_code": "Disease Ontology ID",
                "mesh_id": "MeSH ID of symptom",
                "p_fisher": "Fisher's exact test p-value",
                "cooccurrence": "Number of co-occurring PubMed articles",
                "enrichment": "Enrichment ratio",
                "source": "Data source (MEDLINE cooccurrence)",
                "unbiased": "Whether edge is unbiased (False)",
                "license": "License (CC0 1.0)",
                "sourceDatabase": "Source database name (MEDLINE)"
            },
            "disease_anatomy_cooccurrence": {
                "doid_code": "Disease Ontology ID",
                "uberon_id": "UBERON anatomy ID",
                "p_fisher": "Fisher's exact test p-value",
                "cooccurrence": "Number of co-occurring PubMed articles",
                "enrichment": "Enrichment ratio",
                "source": "Data source (MEDLINE cooccurrence)",
                "unbiased": "Whether edge is unbiased (False)",
                "license": "License (CC0 1.0)",
                "sourceDatabase": "Source database name (MEDLINE)"
            },
            "disease_disease_cooccurrence": {
                "doid_code_0": "Disease Ontology ID of first disease",
                "doid_code_1": "Disease Ontology ID of second disease",
                "p_fisher": "Fisher's exact test p-value",
                "cooccurrence": "Number of co-occurring PubMed articles",
                "enrichment": "Enrichment ratio",
                "source": "Data source (MEDLINE cooccurrence)",
                "unbiased": "Whether edge is unbiased (False)",
                "license": "License (CC0 1.0)",
                "sourceDatabase": "Source database name (MEDLINE)"
            }
        }
