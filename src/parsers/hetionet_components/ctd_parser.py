"""
CTD (Comparative Toxicogenomics Database) Parser for AlzKB.

This module parses CTD chemical-gene interaction data to extract expression
relationships (chemicalIncreasesExpression, chemicalDecreasesExpression) for AlzKB.

Data Source: http://ctdbase.org/downloads/

Output:
  - chemical_increases_expression.tsv: chemicalIncreasesExpression relationships
  - chemical_decreases_expression.tsv: chemicalDecreasesExpression relationships
"""

import logging
import gzip
from pathlib import Path
from typing import Dict, List
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)


class CTDParser(BaseParser):
    """
    Parser for CTD (Comparative Toxicogenomics Database).

    Extracts chemical-gene expression relationships for use in AlzKB's
    chemicalIncreasesExpression and chemicalDecreasesExpression relationships.
    """

    # CTD chemical-gene interactions URL
    CTD_URL = "http://ctdbase.org/reports/CTD_chem_gene_ixns.tsv.gz"

    def __init__(self, data_dir: str):
        """
        Initialize the CTD parser.

        Args:
            data_dir: Directory to store downloaded and processed data
        """
        super().__init__(data_dir)
        self.source_name = "ctd"

    def download_data(self) -> bool:
        """
        Download CTD chemical-gene interactions.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading CTD chemical-gene interactions...")

        result = self.download_file(self.CTD_URL, "CTD_chem_gene_ixns.tsv.gz")

        if result:
            logger.info(f"Successfully downloaded CTD to {result}")
            return True
        else:
            logger.error("Failed to download CTD")
            return False

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse CTD chemical-gene interaction data.

        Returns:
            Dictionary with:
              - 'chemical_increases_expression': Increased expression relationships
              - 'chemical_decreases_expression': Decreased expression relationships
        """
        tsv_path = self.source_dir / "CTD_chem_gene_ixns.tsv.gz"

        if not tsv_path.exists():
            logger.error(f"CTD file not found: {tsv_path}")
            return {}

        logger.info(f"Parsing CTD from {tsv_path}")

        try:
            # CTD file has comment lines starting with #
            # Read and skip comments
            df = pd.read_csv(
                tsv_path,
                sep='\t',
                compression='gzip',
                comment='#',
                header=None,
                names=[
                    'ChemicalName', 'ChemicalID', 'CasRN', 'GeneSymbol', 'GeneID',
                    'GeneForms', 'Organism', 'OrganismID', 'Interaction',
                    'InteractionActions', 'PubMedIDs'
                ],
                low_memory=False
            )

            logger.info(f"Loaded {len(df)} CTD interactions")

            # Filter for human interactions (OrganismID 9606)
            df = df[df['OrganismID'] == 9606]
            logger.info(f"Filtered to {len(df)} human interactions")

            # Extract expression relationships
            increases = []
            decreases = []

            for _, row in df.iterrows():
                chemical_name = row.get('ChemicalName', '')
                chemical_id = row.get('ChemicalID', '')
                gene_symbol = row.get('GeneSymbol', '')
                gene_id = row.get('GeneID', '')
                interaction_actions = str(row.get('InteractionActions', ''))
                pubmed_ids = row.get('PubMedIDs', '')

                if not chemical_name or not gene_symbol:
                    continue

                # Parse interaction actions to find expression changes
                # CTD format: "increases^expression|decreases^activity"
                actions = interaction_actions.split('|')

                for action in actions:
                    if '^' not in action:
                        continue

                    direction, target = action.split('^', 1)

                    # Check for expression-related interactions
                    if 'expression' in target.lower() or 'mrna' in target.lower():
                        record = {
                            "chemical_name": chemical_name,
                            "chemical_id": chemical_id.replace('MESH:', ''),
                            "gene_symbol": gene_symbol,
                            "gene_id": str(gene_id),
                            "interaction_type": target,
                            "pubmed_ids": pubmed_ids,
                            "source": "CTD"
                        }

                        if direction == 'increases':
                            record["relationship"] = "chemicalIncreasesExpression"
                            increases.append(record)
                        elif direction == 'decreases':
                            record["relationship"] = "chemicalDecreasesExpression"
                            decreases.append(record)

            # Remove duplicates
            increases = self._deduplicate(increases)
            decreases = self._deduplicate(decreases)

            logger.info(f"Found {len(increases)} increases expression relationships")
            logger.info(f"Found {len(decreases)} decreases expression relationships")

            result = {}
            if increases:
                result["chemical_increases_expression"] = pd.DataFrame(increases)
            if decreases:
                result["chemical_decreases_expression"] = pd.DataFrame(decreases)

            return result

        except Exception as e:
            logger.error(f"Error parsing CTD: {e}")
            return {}

    def _deduplicate(self, records: List[Dict]) -> List[Dict]:
        """Remove duplicate records based on chemical-gene pair."""
        seen = set()
        unique = []
        for r in records:
            key = (r['chemical_id'], r['gene_symbol'])
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for CTD data.

        Returns:
            Dictionary defining the schema for chemical-gene expression relationships
        """
        return {
            "chemical_increases_expression": {
                "chemical_name": "Chemical/drug name",
                "chemical_id": "MeSH ID for chemical",
                "gene_symbol": "Gene symbol",
                "gene_id": "NCBI Gene ID",
                "interaction_type": "Type of interaction (expression, mRNA, etc.)",
                "pubmed_ids": "Supporting PubMed IDs",
                "relationship": "Relationship type (chemicalIncreasesExpression)",
                "source": "Data source (CTD)"
            },
            "chemical_decreases_expression": {
                "chemical_name": "Chemical/drug name",
                "chemical_id": "MeSH ID for chemical",
                "gene_symbol": "Gene symbol",
                "gene_id": "NCBI Gene ID",
                "interaction_type": "Type of interaction (expression, mRNA, etc.)",
                "pubmed_ids": "Supporting PubMed IDs",
                "relationship": "Relationship type (chemicalDecreasesExpression)",
                "source": "Data source (CTD)"
            }
        }
