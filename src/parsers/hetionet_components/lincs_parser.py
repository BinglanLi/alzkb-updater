"""
LINCS L1000 Parser for AlzKB.

This module parses LINCS L1000 data to extract:
- Compound-upregulates-Gene (CuG) edges from drug perturbations
- Compound-downregulates-Gene (CdG) edges from drug perturbations
- Gene-regulates-Gene (Gr>G) edges from genetic perturbations (knockdown/overexpression)

Data Source: https://github.com/dhimmel/lincs
Commit: abcb12f942f93e3ee839e5e3593f930df2c56845

Output:
  - compound_upregulates_gene.tsv: CuG edges (19,062)
  - compound_downregulates_gene.tsv: CdG edges (21,490)
  - gene_regulates_gene.tsv: Gr>G edges (265,558)
"""

import logging
from pathlib import Path
from typing import Dict, Optional
import pandas as pd

from ..base_parser import BaseParser

logger = logging.getLogger(__name__)


class LINCS1000Parser(BaseParser):
    """
    Parser for LINCS L1000 expression data.

    Extracts drug-gene and gene-gene regulatory relationships from
    LINCS L1000 consensus signatures via the dhimmel/lincs repository.
    """

    # LINCS data from dhimmel GitHub repo
    LINCS_COMMIT = "abcb12f942f93e3ee839e5e3593f930df2c56845"
    LINCS_BASE_URL = f"https://raw.githubusercontent.com/dhimmel/lincs/{LINCS_COMMIT}/data/consensi/signif"

    # File URLs
    DRUG_DYSREG_URL = f"{LINCS_BASE_URL}/dysreg-drugbank.tsv"
    KNOCKDOWN_DYSREG_URL = f"{LINCS_BASE_URL}/dysreg-knockdown.tsv"
    OVEREXPRESSION_DYSREG_URL = f"{LINCS_BASE_URL}/dysreg-overexpression.tsv"

    # Maximum genes per perturbagen-direction-status combination
    MAX_GENES_COMPOUND = 125  # For compound perturbations
    MAX_GENES_GENETIC = 50    # For genetic perturbations

    def __init__(self, data_dir: str):
        """
        Initialize the LINCS L1000 parser.

        Args:
            data_dir: Directory to store downloaded and processed data
        """
        super().__init__(data_dir)
        self.source_name = "lincs"

    def download_data(self) -> bool:
        """
        Download LINCS L1000 data files from dhimmel/lincs GitHub repo.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading LINCS L1000 data...")

        # Download compound dysregulation data
        drug_result = self.download_file(self.DRUG_DYSREG_URL, "dysreg-drugbank.tsv")
        if not drug_result:
            logger.error("Failed to download dysreg-drugbank.tsv")
            return False

        # Download knockdown dysregulation data
        knockdown_result = self.download_file(self.KNOCKDOWN_DYSREG_URL, "dysreg-knockdown.tsv")
        if not knockdown_result:
            logger.error("Failed to download dysreg-knockdown.tsv")
            return False

        # Download overexpression dysregulation data
        overexpr_result = self.download_file(self.OVEREXPRESSION_DYSREG_URL, "dysreg-overexpression.tsv")
        if not overexpr_result:
            logger.error("Failed to download dysreg-overexpression.tsv")
            return False

        logger.info("Successfully downloaded LINCS L1000 data files")
        return True

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse the LINCS L1000 data files.

        Returns:
            Dictionary with:
              - 'compound_upregulates_gene': DataFrame of CuG edges
              - 'compound_downregulates_gene': DataFrame of CdG edges
              - 'gene_regulates_gene': DataFrame of Gr>G edges
        """
        result = {}

        # Parse compound-gene dysregulation (CuG, CdG)
        drug_path = self.source_dir / "dysreg-drugbank.tsv"
        if drug_path.exists():
            cug, cdg = self._parse_compound_gene_dysregulation(drug_path)
            if cug is not None:
                result["compound_upregulates_gene"] = cug
            if cdg is not None:
                result["compound_downregulates_gene"] = cdg
        else:
            logger.error(f"Compound dysregulation file not found: {drug_path}")

        # Parse genetic perturbations (Gr>G)
        knockdown_path = self.source_dir / "dysreg-knockdown.tsv"
        overexpr_path = self.source_dir / "dysreg-overexpression.tsv"

        if knockdown_path.exists() and overexpr_path.exists():
            grg = self._parse_genetic_perturbations(knockdown_path, overexpr_path)
            if grg is not None:
                result["gene_regulates_gene"] = grg
        else:
            logger.error("Genetic perturbation files not found")

        return result

    def _filter_l1000_df(self, df: pd.DataFrame, n: int) -> pd.DataFrame:
        """
        Filter LINCS L1000 differentially expressed genes to at most `n` genes
        per perturbagen-direction-status combination.

        Args:
            df: DataFrame with LINCS data
            n: Maximum number of genes per group

        Returns:
            Filtered DataFrame
        """
        return df.groupby(['perturbagen', 'direction', 'status']).apply(
            lambda x: x.nlargest(n, 'nlog10_bonferroni_pval')
        ).reset_index(drop=True)

    def _parse_compound_gene_dysregulation(self, drug_path: Path) -> tuple:
        """
        Parse compound-gene dysregulation to create CuG and CdG edges.

        Args:
            drug_path: Path to dysreg-drugbank.tsv

        Returns:
            Tuple of (CuG DataFrame, CdG DataFrame)
        """
        logger.info(f"Parsing compound-gene dysregulation from {drug_path}")

        try:
            df = pd.read_csv(drug_path, sep='\t')

            # Filter to top n genes per perturbagen-direction-status
            df = self._filter_l1000_df(df, self.MAX_GENES_COMPOUND)

            # Separate upregulation and downregulation
            up_df = df[df['direction'] == 'up'].copy()
            down_df = df[df['direction'] == 'down'].copy()

            # Create CuG edges
            cug = pd.DataFrame({
                'drugbank_id': up_df['perturbagen'],
                'entrez_gene_id': up_df['entrez_gene_id'],
                'z_score': up_df['z_score'].round(3),
                'method': up_df['status'],
                'unbiased': True,
                'source': 'LINCS L1000',
                'sourceDatabase': 'LINCS'
            })

            # Create CdG edges
            cdg = pd.DataFrame({
                'drugbank_id': down_df['perturbagen'],
                'entrez_gene_id': down_df['entrez_gene_id'],
                'z_score': down_df['z_score'].round(3),
                'method': down_df['status'],
                'unbiased': True,
                'source': 'LINCS L1000',
                'sourceDatabase': 'LINCS'
            })

            logger.info(f"Parsed {len(cug)} Compound-upregulates-Gene edges")
            logger.info(f"Parsed {len(cdg)} Compound-downregulates-Gene edges")

            return cug, cdg

        except Exception as e:
            logger.error(f"Error parsing compound-gene dysregulation: {e}")
            return None, None

    def _parse_genetic_perturbations(self, knockdown_path: Path, overexpr_path: Path) -> Optional[pd.DataFrame]:
        """
        Parse genetic perturbations to create Gene-regulates-Gene edges.

        Args:
            knockdown_path: Path to dysreg-knockdown.tsv
            overexpr_path: Path to dysreg-overexpression.tsv

        Returns:
            DataFrame with Gr>G edge data
        """
        logger.info("Parsing genetic perturbations for Gene-regulates-Gene edges")

        try:
            # Read knockdown data
            kd_df = pd.read_csv(knockdown_path, sep='\t')
            kd_df = self._filter_l1000_df(kd_df, self.MAX_GENES_GENETIC)

            # Map knockdown directions to subtypes
            kd_mapper = {'up': 'knockdown upregulates', 'down': 'knockdown downregulates'}
            kd_df['kind'] = kd_df['direction'].map(kd_mapper)

            # Read overexpression data
            oe_df = pd.read_csv(overexpr_path, sep='\t')
            oe_df = self._filter_l1000_df(oe_df, self.MAX_GENES_GENETIC)

            # Map overexpression directions to subtypes
            oe_mapper = {'up': 'overexpression upregulates', 'down': 'overexpression downregulates'}
            oe_df['kind'] = oe_df['direction'].map(oe_mapper)

            # Combine both datasets
            genetic_df = pd.concat([kd_df, oe_df], ignore_index=True)

            # Filter: both perturbagen and target must be genes (Entrez IDs)
            # The perturbagen column contains gene Entrez IDs for genetic perturbations
            genetic_df = genetic_df.dropna(subset=['perturbagen', 'entrez_gene_id'])

            # Remove self-loops (gene regulating itself)
            genetic_df = genetic_df[genetic_df['perturbagen'] != genetic_df['entrez_gene_id']]

            # Group by perturbagen-target pairs to collect subtypes
            edges = []
            for (pert, gene), group in genetic_df.groupby(['perturbagen', 'entrez_gene_id'], sort=False):
                method = group['status'].iloc[0]  # Take first method
                subtypes = list(group['kind'].unique())
                z_score = group['z_score'].iloc[0]  # Take first z_score

                edges.append({
                    'source_gene': int(pert),
                    'target_gene': int(gene),
                    'z_score': round(z_score, 3),
                    'subtypes': '|'.join(subtypes),
                    'method': method,
                    'unbiased': True,
                    'source': 'LINCS L1000',
                    'sourceDatabase': 'LINCS'
                })

            grg = pd.DataFrame(edges)

            logger.info(f"Parsed {len(grg)} Gene-regulates-Gene edges")
            return grg

        except Exception as e:
            logger.error(f"Error parsing genetic perturbations: {e}")
            return None

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for LINCS L1000 data.

        Returns:
            Dictionary defining the schema for expression edges
        """
        return {
            "compound_upregulates_gene": {
                "drugbank_id": "DrugBank ID of compound",
                "entrez_gene_id": "Entrez Gene ID of upregulated gene",
                "z_score": "Z-score of expression change",
                "method": "Measurement method (measured/imputed)",
                "unbiased": "Whether edge is unbiased (True for LINCS)",
                "source": "Data source (LINCS L1000)",
                "sourceDatabase": "Source database name (LINCS)"
            },
            "compound_downregulates_gene": {
                "drugbank_id": "DrugBank ID of compound",
                "entrez_gene_id": "Entrez Gene ID of downregulated gene",
                "z_score": "Z-score of expression change",
                "method": "Measurement method (measured/imputed)",
                "unbiased": "Whether edge is unbiased (True for LINCS)",
                "source": "Data source (LINCS L1000)",
                "sourceDatabase": "Source database name (LINCS)"
            },
            "gene_regulates_gene": {
                "source_gene": "Entrez Gene ID of regulating gene (perturbagen)",
                "target_gene": "Entrez Gene ID of regulated gene",
                "z_score": "Z-score of expression change",
                "subtypes": "Pipe-separated regulation subtypes",
                "method": "Measurement method",
                "unbiased": "Whether edge is unbiased (True for LINCS)",
                "source": "Data source (LINCS L1000)",
                "sourceDatabase": "Source database name (LINCS)"
            }
        }
