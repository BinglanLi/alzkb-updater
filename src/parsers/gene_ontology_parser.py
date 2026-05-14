"""
Gene Ontology Parser for the knowledge graph.

Downloads and parses the Gene Ontology (GO) to extract:
- Biological Process (BP) nodes
- Molecular Function (MF) nodes
- Cellular Component (CC) nodes
- Gene-GO associations (BP, MF, CC)

Data Sources:
  - GO OBO: http://purl.obolibrary.org/obo/go.obo
  - GOA Human: http://current.geneontology.org/annotations/goa_human.gaf.gz
  - NCBI gene_info (for symbol→Entrez mapping, reused from ncbigene parser)

Output (6 DataFrames):
  - biological_process_nodes.tsv  (go_id, name, definition)
  - molecular_function_nodes.tsv  (go_id, name, definition)
  - cellular_component_nodes.tsv  (go_id, name, definition)
  - gene_bp_associations.tsv      (entrez_gene_id, go_id, evidence)
  - gene_mf_associations.tsv      (entrez_gene_id, go_id, evidence)
  - gene_cc_associations.tsv      (entrez_gene_id, go_id, evidence)
"""

import gzip
import logging
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

try:
    import obonet
    HAS_OBONET = True
except ImportError:
    HAS_OBONET = False

from .base_parser import BaseParser

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Output name constants — must match source_filename in ontology_mappings.yaml
# ---------------------------------------------------------------------------
BP_NODES = "biological_process_nodes"
MF_NODES = "molecular_function_nodes"
CC_NODES = "cellular_component_nodes"
GENE_BP  = "gene_bp_associations"
GENE_MF  = "gene_mf_associations"
GENE_CC  = "gene_cc_associations"

# GAF column names (17 columns in GAF 2.2)
_GAF_COLUMNS = [
    "DB", "DB_Object_ID", "DB_Object_Symbol", "Qualifier", "GO_ID",
    "DB_Reference", "Evidence_Code", "With_From", "Aspect",
    "DB_Object_Name", "DB_Object_Synonym", "DB_Object_Type",
    "Taxon", "Date", "Assigned_By", "Annotation_Extension",
    "Gene_Product_Form_ID",
]


class GeneOntologyParser(BaseParser):
    """
    Parser for the Gene Ontology (GO).

    Extracts GO terms (BP, MF, CC) and human gene-GO associations from
    the GO OBO file and GOA human annotation file.
    """

    # Official GO data sources (as specified by task)
    GO_OBO_URL   = "http://purl.obolibrary.org/obo/go.obo"
    GOA_HUMAN_URL = "http://current.geneontology.org/annotations/goa_human.gaf.gz"

    # Fallback OBO (already cached from previous runs)
    GO_BASIC_OBO = "go-basic.obo"
    GO_OBO_FILE  = "go.obo"
    GAF_FILE     = "goa_human.gaf.gz"

    # Human NCBI taxonomy ID
    HUMAN_TAX_ID = 9606

    def __init__(self, data_dir: str):
        super().__init__(data_dir)
        # BaseParser sets source_name = "geneontology" (from class name).
        # Override to "gene_ontology" so it matches the databases.yaml key.
        # Note: source_dir stays as data_dir/geneontology (where raw files live).
        self.source_name = "gene_ontology"

    # ------------------------------------------------------------------
    # download_data
    # ------------------------------------------------------------------

    def download_data(self) -> bool:
        """Download GO OBO and GOA human annotation files."""
        logger.info("Downloading Gene Ontology files …")
        success = True

        # 1. GO OBO (full ontology)
        obo_path = self.source_dir / self.GO_OBO_FILE
        basic_path = self.source_dir / self.GO_BASIC_OBO
        if not obo_path.exists() and not basic_path.exists():
            result = self.download_file(self.GO_OBO_URL, self.GO_OBO_FILE)
            if not result:
                logger.error("Failed to download GO OBO file")
                success = False
        else:
            logger.info(f"GO OBO already cached — skipping download")

        # 2. GOA human annotation (GAF)
        gaf_path = self.source_dir / self.GAF_FILE
        if not gaf_path.exists():
            result = self.download_file(self.GOA_HUMAN_URL, self.GAF_FILE)
            if not result:
                logger.error("Failed to download GOA human annotation file")
                success = False
        else:
            logger.info(f"GOA human annotation already cached — skipping download")

        return success

    # ------------------------------------------------------------------
    # parse_data
    # ------------------------------------------------------------------

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """Parse GO OBO and GOA annotation files; return 6 DataFrames."""
        result: Dict[str, pd.DataFrame] = {}

        # --- GO terms ---
        obo_path = self._find_obo_file()
        if obo_path is None:
            logger.error("No GO OBO file found — cannot parse GO terms")
        else:
            go_dfs = self._parse_go_ontology(obo_path)
            result.update(go_dfs)

        # --- Gene-GO associations ---
        symbol_to_entrez = self._build_symbol_to_entrez_map()
        gaf_path = self.source_dir / self.GAF_FILE
        if gaf_path.exists():
            assoc_dfs = self._parse_goa_annotations(gaf_path, symbol_to_entrez)
            result.update(assoc_dfs)
        else:
            logger.error(f"GOA annotation file not found: {gaf_path}")

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_obo_file(self) -> Optional[Path]:
        """Return the path to the best available OBO file."""
        for fname in (self.GO_OBO_FILE, self.GO_BASIC_OBO):
            p = self.source_dir / fname
            if p.exists():
                logger.info(f"Using OBO file: {p}")
                return p
        return None

    def _parse_go_ontology(self, obo_path: Path) -> Dict[str, pd.DataFrame]:
        """Parse GO OBO file and return BP/MF/CC node DataFrames."""
        if not HAS_OBONET:
            logger.error("obonet is not installed — cannot parse OBO file")
            return {}

        logger.info(f"Parsing GO ontology from {obo_path} …")
        try:
            graph = obonet.read_obo(str(obo_path))
        except Exception as exc:
            logger.error(f"Failed to read OBO file: {exc}")
            return {}

        bp_terms, mf_terms, cc_terms = [], [], []

        for node_id, node_data in graph.nodes(data=True):
            if not node_id.startswith("GO:"):
                continue
            if node_data.get("is_obsolete", False):
                continue

            namespace = node_data.get("namespace", "")
            term = {
                "go_id":       node_id,
                "name":        node_data.get("name", ""),
                "definition":  self._clean_definition(node_data.get("def", "")),
            }

            if namespace == "biological_process":
                bp_terms.append(term)
            elif namespace == "molecular_function":
                mf_terms.append(term)
            elif namespace == "cellular_component":
                cc_terms.append(term)

        logger.info(
            f"Parsed {len(bp_terms)} BP, {len(mf_terms)} MF, {len(cc_terms)} CC terms"
        )

        return {
            BP_NODES: pd.DataFrame(bp_terms).assign(source_database="Gene Ontology"),
            MF_NODES: pd.DataFrame(mf_terms).assign(source_database="Gene Ontology"),
            CC_NODES: pd.DataFrame(cc_terms).assign(source_database="Gene Ontology"),
        }

    def _build_symbol_to_entrez_map(self) -> Dict[str, int]:
        """
        Build a gene-symbol → Entrez Gene ID mapping from NCBI gene_info.

        Looks first in the ncbigene raw directory (reusing data already
        downloaded by NCBIGeneParser), then falls back to the local
        source directory.
        """
        candidates = [
            self.data_dir / "ncbigene" / "Homo_sapiens.gene_info",
            self.source_dir / "Homo_sapiens.gene_info",
        ]
        gene_info_path: Optional[Path] = None
        for p in candidates:
            if p.exists():
                gene_info_path = p
                break

        if gene_info_path is None:
            logger.warning(
                "Homo_sapiens.gene_info not found — "
                "gene-symbol → Entrez mapping will be empty; "
                "run ncbigene parser first or place the file in data/raw/ncbigene/"
            )
            return {}

        logger.info(f"Loading gene_info from {gene_info_path} …")
        try:
            df = pd.read_csv(
                gene_info_path,
                sep="\t",
                usecols=["#tax_id", "GeneID", "Symbol"],
                dtype={"#tax_id": int, "GeneID": int, "Symbol": str},
            )
            df = df[df["#tax_id"] == self.HUMAN_TAX_ID]
            mapping = dict(zip(df["Symbol"], df["GeneID"]))
            logger.info(f"Loaded {len(mapping):,} symbol→Entrez mappings")
            return mapping
        except Exception as exc:
            logger.error(f"Failed to read gene_info: {exc}")
            return {}

    def _parse_goa_annotations(
        self,
        gaf_path: Path,
        symbol_to_entrez: Dict[str, int],
    ) -> Dict[str, pd.DataFrame]:
        """
        Parse GOA human GAF file and return gene-BP/MF/CC association DataFrames.

        Columns: entrez_gene_id, go_id, evidence
        """
        logger.info(f"Parsing GOA annotations from {gaf_path} …")

        rows = []
        try:
            with gzip.open(gaf_path, "rt", encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("!"):
                        continue
                    parts = line.rstrip("\n").split("\t")
                    if len(parts) < 15:
                        continue
                    # Pad to 17 columns if needed
                    while len(parts) < 17:
                        parts.append("")
                    rows.append(parts[:17])
        except Exception as exc:
            logger.error(f"Failed to read GAF file: {exc}")
            return {}

        df = pd.DataFrame(rows, columns=_GAF_COLUMNS)
        logger.info(f"Loaded {len(df):,} raw GAF records")

        # Keep only human annotations
        df = df[df["Taxon"].str.contains("taxon:9606", na=False)]
        logger.info(f"After human filter: {len(df):,} records")

        # Map gene symbol → Entrez Gene ID
        if symbol_to_entrez:
            df["entrez_gene_id"] = df["DB_Object_Symbol"].map(symbol_to_entrez)
            df = df.dropna(subset=["entrez_gene_id"])
            df["entrez_gene_id"] = df["entrez_gene_id"].astype(int)
        else:
            logger.warning(
                "No symbol→Entrez mapping available; "
                "association DataFrames will be empty"
            )
            return {GENE_BP: pd.DataFrame(columns=["entrez_gene_id", "go_id", "evidence"]),
                    GENE_MF: pd.DataFrame(columns=["entrez_gene_id", "go_id", "evidence"]),
                    GENE_CC: pd.DataFrame(columns=["entrez_gene_id", "go_id", "evidence"])}

        # Split by GO aspect: P=BP, F=MF, C=CC
        def _extract(aspect_code: str) -> pd.DataFrame:
            sub = df[df["Aspect"] == aspect_code][
                ["entrez_gene_id", "GO_ID", "Evidence_Code"]
            ].copy()
            sub.columns = ["entrez_gene_id", "go_id", "evidence"]
            sub = sub.drop_duplicates(subset=["entrez_gene_id", "go_id"])
            sub = sub.reset_index(drop=True)
            return sub

        bp_df = _extract("P")
        mf_df = _extract("F")
        cc_df = _extract("C")

        logger.info(
            f"Associations — BP: {len(bp_df):,}, MF: {len(mf_df):,}, CC: {len(cc_df):,}"
        )

        for df in [bp_df, mf_df, cc_df]:
            df["source_database"] = "Gene Ontology"
        return {GENE_BP: bp_df, GENE_MF: mf_df, GENE_CC: cc_df}

    @staticmethod
    def _clean_definition(definition: str) -> str:
        """Strip OBO-format quotes and citation brackets from a definition.

        OBO format: "Definition text." [citation]
        """
        if not definition:
            return ""
        # Remove leading quote
        if definition.startswith('"'):
            definition = definition[1:]
        # Remove citation bracket and everything after it
        if " [" in definition:
            definition = definition.split(" [")[0]
        # Remove trailing quote (left after stripping the citation)
        if definition.endswith('"'):
            definition = definition[:-1]
        # Replace any embedded tab characters with a space to prevent TSV field splitting
        definition = definition.replace('\t', ' ')
        return definition.strip()

    # ------------------------------------------------------------------
    # get_schema
    # ------------------------------------------------------------------

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """Return the schema for all 6 output DataFrames."""
        node_schema = {
            "go_id":       "Gene Ontology ID (e.g. GO:0008150)",
            "name":        "Human-readable GO term name",
            "definition":  "Text definition of the GO term",
        }
        assoc_schema = {
            "entrez_gene_id": "NCBI Entrez Gene ID (integer)",
            "go_id":          "Gene Ontology ID",
            "evidence":       "GO evidence code (e.g. IDA, IEA, TAS)",
        }
        return {
            BP_NODES: node_schema,
            MF_NODES: node_schema,
            CC_NODES: node_schema,
            GENE_BP:  assoc_schema,
            GENE_MF:  assoc_schema,
            GENE_CC:  assoc_schema,
        }
