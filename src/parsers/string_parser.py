"""
STRING Protein-Protein Interaction Parser for the knowledge graph.

Downloads human (taxon 9606) protein-protein interaction data from the
STRING database and maps Ensembl protein IDs to NCBI Gene IDs via the
STRING aliases file.

Data Sources (STRING v12.0):
  - protein.links.v12.0: protein1, protein2, combined_score (space-sep)
  - protein.info.v12.0:  string_protein_id, preferred_name, protein_size, annotation
  - protein.aliases.v12.0: string_protein_id, alias, source

Outputs:
  - genes.tsv              : Gene nodes (only genes with >= 1 surviving interaction)
  - gene_interactions.tsv  : geneInteractsWithGene edges (combined_score >= min_combined_score)
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Set

import pandas as pd

from .base_parser import BaseParser

logger = logging.getLogger(__name__)

STRING_VERSION = "v12.0"
TAXON = "9606"

LINKS_URL = (
    "https://stringdb-downloads.org/download/protein.links." + STRING_VERSION + "/"
    + TAXON + ".protein.links." + STRING_VERSION + ".txt.gz"
)
INFO_URL = (
    "https://stringdb-downloads.org/download/protein.info." + STRING_VERSION + "/"
    + TAXON + ".protein.info." + STRING_VERSION + ".txt.gz"
)
ALIASES_URL = (
    "https://stringdb-downloads.org/download/protein.aliases." + STRING_VERSION + "/"
    + TAXON + ".protein.aliases." + STRING_VERSION + ".txt.gz"
)

LINKS_GZ   = TAXON + ".protein.links." + STRING_VERSION + ".txt.gz"
INFO_GZ    = TAXON + ".protein.info." + STRING_VERSION + ".txt.gz"
ALIASES_GZ = TAXON + ".protein.aliases." + STRING_VERSION + ".txt.gz"

LINKS_FILE   = LINKS_GZ[:-3]
INFO_FILE    = INFO_GZ[:-3]
ALIASES_FILE = ALIASES_GZ[:-3]

ENTREZ_SOURCES = {"Ensembl_HGNC_entrez_id", "UniProt_DR_GeneID", "KEGG_GENEID"}

OUTPUT_GENES        = "genes"
OUTPUT_INTERACTIONS = "gene_interactions"

SOURCE_DB = "STRING"


class StringParser(BaseParser):
    """
    Parser for STRING protein-protein interaction data (human, taxon 9606).

    Maps Ensembl protein IDs to NCBI Gene IDs using the STRING aliases file,
    preferring Ensembl_HGNC_entrez_id, UniProt_DR_GeneID, and KEGG_GENEID sources.

    Parameters
    ----------
    data_dir : str
        Root directory for raw data downloads.
    min_combined_score : int
        Minimum STRING combined score (0-1000) for retaining an interaction.
        Interactions below this threshold are discarded. Default is 700.
    """

    def __init__(self, data_dir: str, min_combined_score: int = 700):
        super().__init__(data_dir)
        self.min_combined_score = int(min_combined_score)

    def download_data(self) -> bool:
        logger.info("Downloading STRING data (human, taxon 9606)...")
        success = True
        for url, gz_name in [
            (LINKS_URL,   LINKS_GZ),
            (INFO_URL,    INFO_GZ),
            (ALIASES_URL, ALIASES_GZ),
        ]:
            gz_path = self.download_file(url, gz_name)
            if not gz_path:
                logger.error("Failed to download: " + url)
                success = False
                continue
            extracted = self.extract_gzip(gz_path)
            if not extracted:
                logger.error("Failed to extract: " + gz_path)
                success = False
        if success:
            logger.info("All STRING files ready.")
        else:
            logger.warning("One or more STRING downloads failed.")
        return success

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        logger.info("Parsing STRING data (min_combined_score=%d)...", self.min_combined_score)

        protein_to_gene = self._build_protein_to_gene_map()
        if protein_to_gene is None:
            return {}
        logger.info("  Proteins with NCBI Gene ID: %d", len(protein_to_gene))

        protein_info = self._build_protein_info_map()
        if protein_info is None:
            return {}

        # Build all gene nodes first (before score filtering)
        genes_df_all = self._build_genes_df(protein_to_gene, protein_info)
        if genes_df_all is None or genes_df_all.empty:
            logger.error("No gene records produced.")
            return {}

        # Build interactions with score filter applied
        interactions_df = self._build_interactions_df(protein_to_gene)
        if interactions_df is None or interactions_df.empty:
            logger.error("No interaction records produced after score filtering.")
            return {}

        # Regenerate genes.tsv: keep only genes that appear in at least one surviving interaction
        surviving_gene_ids: Set[str] = (
            set(interactions_df["gene_id_1"].astype(str))
            | set(interactions_df["gene_id_2"].astype(str))
        )
        before_genes = len(genes_df_all)
        genes_df = genes_df_all[
            genes_df_all["ncbi_gene_id"].astype(str).isin(surviving_gene_ids)
        ].copy().reset_index(drop=True)
        logger.info(
            "  Gene nodes after interaction-based filter: %d -> %d",
            before_genes,
            len(genes_df),
        )

        return {
            OUTPUT_GENES:        genes_df,
            OUTPUT_INTERACTIONS: interactions_df,
        }

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        return {
            OUTPUT_GENES: {
                "ncbi_gene_id":       "NCBI Entrez Gene identifier",
                "ensembl_protein_id": "Ensembl protein identifier (ENSP...)",
                "gene_symbol":        "Official gene symbol from STRING preferred_name",
                "gene_name":          "Gene/protein annotation text from STRING",
            },
            OUTPUT_INTERACTIONS: {
                "gene_id_1":       "NCBI Entrez Gene ID of the first interaction partner",
                "gene_id_2":       "NCBI Entrez Gene ID of the second interaction partner",
                "combined_score":  "STRING combined interaction score (0-1000)",
                "source_database": "Source database name (STRING)",
            },
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_protein_to_gene_map(self) -> Optional[Dict[str, str]]:
        aliases_path = self.get_file_path(ALIASES_FILE)
        if not Path(aliases_path).exists():
            logger.error("Aliases file not found: " + aliases_path)
            return None

        logger.info("Reading aliases file: " + aliases_path)
        aliases_df = pd.read_csv(aliases_path, sep="\t", dtype=str, low_memory=False)
        aliases_df.columns = [c.lstrip("#") for c in aliases_df.columns]
        logger.info("  Total alias rows: %d", len(aliases_df))
        logger.info("  Columns: %s", list(aliases_df.columns))

        present = set(aliases_df["source"].unique())
        matched = ENTREZ_SOURCES & present
        logger.info("  Matched Entrez sources: %s", matched)

        mask = aliases_df["source"].isin(ENTREZ_SOURCES)
        entrez_df = aliases_df[mask].copy()
        logger.info("  Entrez alias rows: %d", len(entrez_df))

        if entrez_df.empty:
            logger.warning("Falling back to substring search for entrez/ncbi in source.")
            mask2 = aliases_df["source"].str.lower().str.contains(
                "hgnc_entrez|geneid|dr_geneid", na=False
            )
            entrez_df = aliases_df[mask2].copy()
            logger.info("  Alias rows after fallback: %d", len(entrez_df))

        entrez_df["protein_id"] = entrez_df["string_protein_id"].str.replace(
            "^" + TAXON + r"\.", "", regex=True
        )

        # Priority ordering: prefer Ensembl_HGNC_entrez_id, then UniProt_DR_GeneID, then KEGG_GENEID
        priority = {src: i for i, src in enumerate(
            ["Ensembl_HGNC_entrez_id", "UniProt_DR_GeneID", "KEGG_GENEID"]
        )}
        entrez_df["_priority"] = entrez_df["source"].map(lambda s: priority.get(s, 99))
        entrez_df = entrez_df.sort_values("_priority")

        protein_to_gene = (
            entrez_df.drop_duplicates(subset="protein_id", keep="first")
            .set_index("protein_id")["alias"]
            .to_dict()
        )
        return protein_to_gene

    def _build_protein_info_map(self) -> Optional[Dict[str, tuple]]:
        info_path = self.get_file_path(INFO_FILE)
        if not Path(info_path).exists():
            logger.error("Info file not found: " + info_path)
            return None

        logger.info("Reading protein info file: " + info_path)
        info_df = pd.read_csv(info_path, sep="\t", dtype=str, low_memory=False)
        info_df.columns = [c.lstrip("#") for c in info_df.columns]
        logger.info("  Total info rows: %d", len(info_df))
        logger.info("  Columns: %s", list(info_df.columns))

        info_df["protein_id"] = info_df["string_protein_id"].str.replace(
            "^" + TAXON + r"\.", "", regex=True
        )

        protein_info = {}
        for _, row in info_df.iterrows():
            pid = row["protein_id"]
            symbol = str(row.get("preferred_name", "") or "")
            name   = str(row.get("annotation", "") or "")
            protein_info[pid] = (symbol, name)
        return protein_info

    def _build_genes_df(
        self,
        protein_to_gene: Dict[str, str],
        protein_info: Dict[str, tuple],
    ) -> Optional[pd.DataFrame]:
        records = []
        for protein_id, ncbi_gene_id in protein_to_gene.items():
            gene_symbol, gene_name = protein_info.get(protein_id, ("", ""))
            records.append({
                "ncbi_gene_id":       str(ncbi_gene_id),
                "ensembl_protein_id": protein_id,
                "gene_symbol":        gene_symbol,
                "gene_name":          gene_name,
            })
        if not records:
            return None
        genes_df = pd.DataFrame(records)
        before = len(genes_df)
        genes_df = genes_df.drop_duplicates(subset="ncbi_gene_id", keep="first")
        logger.info("  Gene nodes: %d -> %d after dedup", before, len(genes_df))
        return genes_df.reset_index(drop=True)

    def _build_interactions_df(
        self,
        protein_to_gene: Dict[str, str],
    ) -> Optional[pd.DataFrame]:
        links_path = self.get_file_path(LINKS_FILE)
        if not Path(links_path).exists():
            logger.error("Links file not found: " + links_path)
            return None

        logger.info("Reading protein links file: " + links_path)
        links_df = pd.read_csv(
            links_path,
            sep=" ",
            dtype={"protein1": str, "protein2": str, "combined_score": "Int64"},
            low_memory=False,
        )
        total_before_filter = len(links_df)
        logger.info("  Total PPI rows (before score filter): %d", total_before_filter)

        # Apply combined-score threshold filter
        links_df = links_df[links_df["combined_score"] >= self.min_combined_score].copy()
        logger.info(
            "  After combined_score >= %d filter: %d -> %d rows",
            self.min_combined_score,
            total_before_filter,
            len(links_df),
        )

        links_df["p1"] = links_df["protein1"].str.replace(
            "^" + TAXON + r"\.", "", regex=True
        )
        links_df["p2"] = links_df["protein2"].str.replace(
            "^" + TAXON + r"\.", "", regex=True
        )

        links_df["gene_id_1"] = links_df["p1"].map(protein_to_gene)
        links_df["gene_id_2"] = links_df["p2"].map(protein_to_gene)

        before_ncbi = len(links_df)
        links_df = links_df.dropna(subset=["gene_id_1", "gene_id_2"])
        logger.info(
            "  After NCBI Gene ID filter: %d -> %d",
            before_ncbi,
            len(links_df),
        )

        interactions_df = links_df[["gene_id_1", "gene_id_2", "combined_score"]].copy()
        interactions_df["source_database"] = SOURCE_DB

        before_dedup = len(interactions_df)
        interactions_df = interactions_df.drop_duplicates(
            subset=["gene_id_1", "gene_id_2"]
        )
        logger.info(
            "  After dedup: %d -> %d",
            before_dedup,
            len(interactions_df),
        )
        return interactions_df.reset_index(drop=True)
