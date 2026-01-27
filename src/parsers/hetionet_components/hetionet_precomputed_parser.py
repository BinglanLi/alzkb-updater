"""
Hetionet Precomputed Relationships Parser for AlzKB.

This module parses pre-computed relationships from Hetionet that are
difficult to recreate from source (geneCovariesWithGene, geneRegulatesGene,
geneInteractsWithGene, drugCausesEffect).

Data Source: https://github.com/hetio/hetionet

Output:
  - gene_covaries.tsv: geneCovariesWithGene relationships
  - gene_regulates.tsv: geneRegulatesGene relationships
  - gene_interacts.tsv: geneInteractsWithGene relationships
  - drug_causes_effect.tsv: drugCausesEffect relationships
"""

import logging
import gzip
import json
from pathlib import Path
from typing import Dict, List
import pandas as pd

from ..base_parser import BaseParser

logger = logging.getLogger(__name__)


class HetionetPrecomputedParser(BaseParser):
    """
    Parser for pre-computed Hetionet relationships.

    Extracts relationships that are pre-computed in Hetionet and difficult
    to recreate from source data, including gene covariation and regulation.
    """

    # Hetionet edges SIF URL
    HETIONET_EDGES_URL = "https://github.com/hetio/hetionet/raw/main/hetnet/tsv/hetionet-v1.0-edges.sif.gz"

    # Hetionet JSON URL (for full data with properties)
    HETIONET_JSON_URL = "https://github.com/hetio/hetionet/raw/main/hetnet/json/hetionet-v1.0.json.bz2"

    def __init__(self, data_dir: str):
        """
        Initialize the Hetionet precomputed parser.

        Args:
            data_dir: Directory to store downloaded and processed data
        """
        super().__init__(data_dir)
        self.source_name = "hetionet_precomputed"

    def download_data(self) -> bool:
        """
        Download Hetionet edge data.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading Hetionet precomputed edges...")

        result = self.download_file(self.HETIONET_EDGES_URL, "hetionet-v1.0-edges.sif.gz")

        if result:
            logger.info(f"Successfully downloaded Hetionet edges to {result}")
            return True
        else:
            logger.error("Failed to download Hetionet edges")
            return False

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse Hetionet edge data.

        Returns:
            Dictionary with DataFrames for each relationship type
        """
        sif_path = self.source_dir / "hetionet-v1.0-edges.sif.gz"

        if not sif_path.exists():
            logger.error(f"Hetionet edges file not found: {sif_path}")
            return {}

        logger.info(f"Parsing Hetionet edges from {sif_path}")

        try:
            # Read SIF format: source\trelationship\ttarget
            df = pd.read_csv(
                sif_path,
                sep='\t',
                compression='gzip',
                names=['source', 'metaedge', 'target'],
                header=None
            )

            logger.info(f"Loaded {len(df)} Hetionet edges")

            # Extract specific relationship types
            result = {}

            # Gene covaries with gene (GcG)
            gcg = df[df['metaedge'] == 'GcG'].copy()
            if len(gcg) > 0:
                result["gene_covaries"] = self._format_gene_gene(gcg, "geneCovariesWithGene")
                logger.info(f"Found {len(gcg)} geneCovariesWithGene relationships")

            # Gene regulates gene (Gr>G)
            grg = df[df['metaedge'].isin(['Gr>G', 'GrG'])].copy()
            if len(grg) > 0:
                result["gene_regulates"] = self._format_gene_gene(grg, "geneRegulatesGene")
                logger.info(f"Found {len(grg)} geneRegulatesGene relationships")

            # Gene interacts with gene (GiG)
            gig = df[df['metaedge'] == 'GiG'].copy()
            if len(gig) > 0:
                result["gene_interacts"] = self._format_gene_gene(gig, "geneInteractsWithGene")
                logger.info(f"Found {len(gig)} geneInteractsWithGene relationships")

            # Compound causes side effect (CcSE)
            ccse = df[df['metaedge'] == 'CcSE'].copy()
            if len(ccse) > 0:
                result["drug_causes_effect"] = self._format_drug_effect(ccse)
                logger.info(f"Found {len(ccse)} drugCausesEffect relationships")

            return result

        except Exception as e:
            logger.error(f"Error parsing Hetionet edges: {e}")
            return {}

    def _format_gene_gene(self, df: pd.DataFrame, relationship: str) -> pd.DataFrame:
        """
        Format gene-gene relationships.

        Args:
            df: DataFrame with source, metaedge, target columns
            relationship: Relationship type name

        Returns:
            Formatted DataFrame
        """
        records = []
        for _, row in df.iterrows():
            # Parse Hetionet node format: "Gene::SYMBOL"
            source_gene = self._parse_hetionet_id(row['source'], 'Gene')
            target_gene = self._parse_hetionet_id(row['target'], 'Gene')

            if source_gene and target_gene:
                records.append({
                    "gene1_symbol": source_gene,
                    "gene2_symbol": target_gene,
                    "relationship": relationship,
                    "source": "Hetionet"
                })

        return pd.DataFrame(records)

    def _format_drug_effect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Format drug causes effect relationships.

        Args:
            df: DataFrame with source, metaedge, target columns

        Returns:
            Formatted DataFrame
        """
        records = []
        for _, row in df.iterrows():
            # Parse Hetionet node format: "Compound::DRUGBANK_ID" and "Side Effect::UMLS_ID"
            drug_id = self._parse_hetionet_id(row['source'], 'Compound')
            effect_id = self._parse_hetionet_id(row['target'], 'Side Effect')

            if drug_id and effect_id:
                records.append({
                    "drug_id": drug_id,
                    "effect_id": effect_id,
                    "relationship": "drugCausesEffect",
                    "source": "Hetionet"
                })

        return pd.DataFrame(records)

    def _parse_hetionet_id(self, node_str: str, expected_type: str) -> str:
        """
        Parse Hetionet node ID format.

        Hetionet format: "NodeType::Identifier"

        Args:
            node_str: Hetionet node string
            expected_type: Expected node type

        Returns:
            Identifier string or None
        """
        if '::' not in str(node_str):
            return None

        parts = str(node_str).split('::', 1)
        if len(parts) != 2:
            return None

        node_type, identifier = parts
        if node_type == expected_type:
            return identifier

        return None

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for Hetionet precomputed data.

        Returns:
            Dictionary defining the schema for relationship types
        """
        return {
            "gene_covaries": {
                "gene1_symbol": "First gene symbol",
                "gene2_symbol": "Second gene symbol",
                "relationship": "Relationship type (geneCovariesWithGene)",
                "source": "Data source (Hetionet)"
            },
            "gene_regulates": {
                "gene1_symbol": "Regulator gene symbol",
                "gene2_symbol": "Regulated gene symbol",
                "relationship": "Relationship type (geneRegulatesGene)",
                "source": "Data source (Hetionet)"
            },
            "gene_interacts": {
                "gene1_symbol": "First gene symbol",
                "gene2_symbol": "Second gene symbol",
                "relationship": "Relationship type (geneInteractsWithGene)",
                "source": "Data source (Hetionet)"
            },
            "drug_causes_effect": {
                "drug_id": "DrugBank ID",
                "effect_id": "Side effect UMLS ID",
                "relationship": "Relationship type (drugCausesEffect)",
                "source": "Data source (Hetionet)"
            }
        }
