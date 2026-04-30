"""
Bgee Expression Parser for the knowledge graph.

This module parses Bgee gene expression data to extract gene-anatomy
expression relationships for the knowledge graph.

Data Source: https://www.bgee.org/
Format: BGEE presence/absence expression calls (Homo_sapiens_expr_simple.tsv.gz)

The file contains columns:
  Gene ID, Gene name, Anatomical entity ID, Anatomical entity name,
  Expression, Call quality, FDR, Expression score, Expression rank

Output:
  - anatomy_expresses_gene.tsv: AeG edges (Anatomy expresses Gene)
"""

import logging
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Set

import pandas as pd

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class BgeeParser(BaseParser):
    """
    Parser for Bgee gene expression database.

    Extracts gene expression data from BGEE using the presence/absence
    expression calls format with quality metrics (FDR, expression score, rank).

    Constructor args (passed from databases.yaml):
        source_url  : URL to the Homo_sapiens_expr_simple.tsv.gz file.
        tissue_filter: Optional list of UBERON IDs to restrict output to.
                       When None, all UBERON anatomies are included.
    """

    def __init__(
        self,
        data_dir: str,
        source_url: str,
        tissue_filter: Optional[List[str]] = None,
    ):
        """
        Initialize the Bgee parser.

        Args:
            data_dir     : Directory to store downloaded and processed data.
            source_url   : URL of the BGEE expression-calls TSV.gz file.
            tissue_filter: Optional list of UBERON IDs to keep.
                           When None, all UBERON anatomies are included.
        """
        super().__init__(data_dir)
        self.source_name = "bgee"
        # Re-derive source_dir after overriding source_name
        self.source_dir = self.data_dir / self.source_name
        self.source_dir.mkdir(parents=True, exist_ok=True)

        self.source_url = source_url
        self.tissue_filter = tissue_filter  # None → include all; list → restrict

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download_data(self) -> bool:
        """
        Download Bgee expression calls data from the configured source_url.

        Returns:
            True if the file is available (downloaded or cached), else False.
        """
        logger.info("Downloading Bgee expression calls data...")
        result = self.download_file(self.source_url, "expr_calls.tsv.gz")
        if result:
            logger.info(f"Bgee expr_calls available at: {result}")
            return True
        logger.error("Failed to download Bgee expression calls data.")
        return False

    # ------------------------------------------------------------------
    # Ensembl → Entrez mapping helper
    # ------------------------------------------------------------------

    def _build_ensembl_to_entrez_map(self) -> Dict[str, str]:
        """
        Build an Ensembl Gene ID → Entrez Gene ID mapping from the NCBI
        gene-info file (Homo_sapiens.gene_info or .gz) in data/raw/ncbigene/.

        Returns:
            Dict mapping Ensembl ID (str) to Entrez Gene ID (str).
            Empty dict if the file cannot be found or read.
        """
        ncbigene_dir = self.data_dir / "ncbigene"
        candidates = [
            ncbigene_dir / "Homo_sapiens.gene_info",
            ncbigene_dir / "Homo_sapiens.gene_info.gz",
        ]

        gene_info_path = None
        for c in candidates:
            if c.exists():
                gene_info_path = c
                break

        if gene_info_path is None:
            logger.warning(
                "NCBI gene-info file not found in %s; "
                "Ensembl → Entrez mapping unavailable.",
                ncbigene_dir,
            )
            return {}

        try:
            compression = "gzip" if str(gene_info_path).endswith(".gz") else None
            df = pd.read_csv(
                gene_info_path,
                sep="\t",
                compression=compression,
                low_memory=False,
            )
            # The header line starts with '#tax_id'; strip the leading '#'
            df.columns = [c.lstrip("#") for c in df.columns]

            mapping: Dict[str, str] = {}
            for _, row in df.iterrows():
                xrefs = str(row.get("dbXrefs", "-"))
                if xrefs in ("-", "nan"):
                    continue
                for xref in xrefs.split("|"):
                    if xref.startswith("Ensembl:"):
                        ensembl_id = xref[len("Ensembl:"):]
                        mapping[ensembl_id] = str(int(row["GeneID"]))

            logger.info(
                "Built Ensembl → Entrez mapping: %d entries.", len(mapping)
            )
            return mapping

        except Exception as exc:
            logger.error("Failed to build Ensembl → Entrez mapping: %s", exc)
            logger.debug(traceback.format_exc())
            return {}

    # ------------------------------------------------------------------
    # Parse
    # ------------------------------------------------------------------

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse Bgee presence/absence expression calls.

        Workflow:
          1. Read expr_calls.tsv.gz.
          2. Keep only 'present' expression calls.
          3. Keep only rows whose Anatomical entity ID starts with 'UBERON:'.
          4. Apply tissue_filter if configured.
          5. Map Ensembl Gene IDs to Entrez Gene IDs via NCBI gene-info.
          6. Return anatomy_expresses_gene DataFrame.

        Returns:
            Dict with key 'anatomy_expresses_gene' → DataFrame of AeG edges.
        """
        expr_calls_path = self.source_dir / "expr_calls.tsv.gz"

        if not expr_calls_path.exists():
            logger.error("Bgee expr_calls file not found: %s", expr_calls_path)
            return {}

        logger.info("Parsing Bgee expression calls from %s", expr_calls_path)

        try:
            # ---- 1. Load raw data ----------------------------------------
            df = pd.read_csv(
                expr_calls_path,
                sep="\t",
                compression="gzip",
                low_memory=False,
                quotechar='"',
            )
            logger.info("Loaded %d raw records; columns: %s", len(df), list(df.columns))

            # ---- 2. Filter for 'present' calls only ----------------------
            present = df[df["Expression"] == "present"].copy()
            logger.info("%d 'present' expression calls.", len(present))

            # ---- 3. Keep only UBERON anatomies ---------------------------
            uberon_mask = present["Anatomical entity ID"].str.startswith(
                "UBERON:", na=False
            )
            present = present[uberon_mask].copy()
            logger.info(
                "%d records after keeping UBERON anatomies.", len(present)
            )

            # ---- 4. Apply tissue_filter (optional) -----------------------
            if self.tissue_filter:
                present = present[
                    present["Anatomical entity ID"].isin(self.tissue_filter)
                ].copy()
                logger.info(
                    "%d records after tissue_filter.", len(present)
                )

            if present.empty:
                logger.warning("No records remain after filtering; returning empty.")
                return {}

            # ---- 5. Map Ensembl → Entrez ---------------------------------
            ensembl_to_entrez = self._build_ensembl_to_entrez_map()

            if ensembl_to_entrez:
                present["entrez_gene_id"] = present["Gene ID"].map(ensembl_to_entrez)
                before = len(present)
                present = present.dropna(subset=["entrez_gene_id"]).copy()
                logger.info(
                    "Entrez mapping: retained %d / %d records.", len(present), before
                )
            else:
                # Fallback: use Ensembl IDs directly
                present["entrez_gene_id"] = present["Gene ID"]
                logger.warning(
                    "No Entrez mapping available; using Ensembl IDs as gene identifier."
                )

            if present.empty:
                logger.warning("No records after Entrez mapping; returning empty.")
                return {}

            # ---- 6. Build output DataFrame --------------------------------
            aeg = pd.DataFrame(
                {
                    "uberon_id": present["Anatomical entity ID"].values,
                    "entrez_gene_id": present["entrez_gene_id"].values,
                    "expression_call": present["Expression"].values,
                    "call_quality": present["Call quality"].values,
                    "fdr": present["FDR"].values,
                    "expression_score": present["Expression score"].values,
                    "expression_rank": present["Expression rank"].values,
                    "source": "Bgee",
                    "unbiased": True,
                    "sourceDatabase": "Bgee",
                }
            )

            logger.info(
                "Parsed %d Anatomy-expresses-Gene edges.", len(aeg)
            )
            return {"anatomy_expresses_gene": aeg}

        except Exception as exc:
            logger.error("Error parsing Bgee expression calls: %s", exc)
            logger.error(traceback.format_exc())
            return {}

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Return the schema for Bgee output DataFrames.
        """
        return {
            "anatomy_expresses_gene": {
                "uberon_id": "UBERON anatomy ID (BodyPart source node)",
                "entrez_gene_id": "Entrez Gene ID (Gene target node)",
                "expression_call": "Expression call: 'present' or 'absent'",
                "call_quality": "Call quality (e.g., 'gold quality', 'silver quality')",
                "fdr": "False Discovery Rate",
                "expression_score": "Expression score (0–100)",
                "expression_rank": "Expression rank (lower = higher expression)",
                "source": "Data source label ('Bgee')",
                "unbiased": "Whether the edge is unbiased (True for Bgee)",
                "sourceDatabase": "Source database name ('Bgee')",
            }
        }
