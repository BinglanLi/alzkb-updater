"""
MEDLINE Cooccurrence Parser for the knowledge graph.

Queries PubMed via NCBI E-utilities for disease, symptom, and anatomy terms,
then computes Fisher's exact test co-occurrence statistics.

Data Sources:
  - disease_xrefs.tsv (from DiseaseOntologyParser) — disease→MeSH mapping
  - MeSH XML (from MeSHParser) — MeSH ID→name lookup and symptom subtree
  - uberon_mesh_xrefs.tsv (from UberonParser) — UBERON→MeSH anatomy mapping

Intermediate files cached in data/raw/medline/:
  - disease-pmids.tsv.gz
  - symptom-pmids.tsv.gz
  - uberon-pmids.tsv.gz

Outputs:
  - disease_symptom_cooccurrence.tsv  (symptomManifestationOfDisease edges)
  - disease_anatomy_cooccurrence.tsv  (diseaseLocalizesToAnatomy edges)
  - disease_disease_cooccurrence.tsv  (diseaseAssociatesWithDisease edges)
"""

import itertools
import logging
import time
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

import pandas as pd
import requests
import scipy.stats
from lxml import etree

from .base_parser import BaseParser

logger = logging.getLogger(__name__)

MESH_YEAR = 2026
SYMPTOM_TREE_PREFIX = "C23.888."

# Problematic DO↔MeSH cross-references flagged in
# https://github.com/obophenotype/human-disease-ontology/issues/45
EXCLUDED_MESH_IDS = {"D003327", "D017202"}

P_FISHER_THRESHOLD = 0.005
EUTILS_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
# 3 requests/sec NCBI rate limit for unauthenticated users
EUTILS_SLEEP = 0.34


class MEDLINECooccurrenceParser(BaseParser):
    """
    Parser for MEDLINE literature co-occurrence data.

    Queries PubMed via NCBI E-utilities for each disease (MeSH Major Topic),
    symptom, and anatomy term (MeSH Terms:noexp), then computes pairwise
    Fisher's exact test co-occurrence statistics.
    """

    def __init__(self, data_dir: str):
        super().__init__(data_dir)
        self.source_name = "medline"
        self._mesh_dir = self.data_dir / "mesh"
        # processed/ sits alongside raw/ under the project data/ root
        self._processed_dir = self.data_dir.parent / "processed"

    # ------------------------------------------------------------------
    # BaseParser interface
    # ------------------------------------------------------------------

    def download_data(self) -> bool:
        """No direct downloads; depends on MeSHParser and UberonParser outputs."""
        return True

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Compute disease-symptom, disease-anatomy, and disease-disease co-occurrence.

        Returns:
            Dictionary with disease_symptom_cooccurrence, disease_anatomy_cooccurrence,
            and disease_disease_cooccurrence DataFrames.
        """
        mesh_terms = self._parse_mesh_xml()
        if not mesh_terms:
            return {}
        mesh_names = {t["mesh_id"]: t["mesh_name"] for t in mesh_terms}

        disease_df = self._load_disease_list(mesh_names)
        symptom_df = self._load_symptom_list(mesh_terms)
        anatomy_df = self._load_anatomy_list(mesh_names)

        for label, df in [("disease", disease_df), ("symptom", symptom_df), ("anatomy", anatomy_df)]:
            if df is None or df.empty:
                logger.error(f"Empty {label} list; aborting")
                return {}

        disease_pmids_path = self.source_dir / "disease-pmids.tsv.gz"
        symptom_pmids_path = self.source_dir / "symptom-pmids.tsv.gz"
        uberon_pmids_path = self.source_dir / "uberon-pmids.tsv.gz"

        self._compute_pmids_file(
            disease_df, "doid_code", "mesh_name",
            "{name}[MeSH Major Topic]", disease_pmids_path,
        )
        self._compute_pmids_file(
            symptom_df, "mesh_id", "mesh_name",
            "{name}[MeSH Terms:noexp]", symptom_pmids_path,
        )
        self._compute_pmids_file(
            anatomy_df, "uberon_id", "mesh_name",
            "{name}[MeSH Terms:noexp]", uberon_pmids_path,
        )

        disease_meta, disease_to_pmids = self._read_pmids_tsv(disease_pmids_path, "doid_code")
        symptom_meta, symptom_to_pmids = self._read_pmids_tsv(symptom_pmids_path, "mesh_id")
        anatomy_meta, anatomy_to_pmids = self._read_pmids_tsv(uberon_pmids_path, "uberon_id")

        result = {}

        dps = self._score_pmid_cooccurrence(disease_to_pmids, symptom_to_pmids, "doid_code", "mesh_id")
        if not dps.empty:
            dps = symptom_meta[["mesh_id", "mesh_name"]].drop_duplicates().merge(dps)
            dps = disease_meta[["doid_code", "doid_name"]].drop_duplicates().merge(dps)
            dps = dps[dps["p_fisher"] < P_FISHER_THRESHOLD].sort_values(["doid_name", "p_fisher"])
            result["disease_symptom_cooccurrence"] = dps

        dla = self._score_pmid_cooccurrence(disease_to_pmids, anatomy_to_pmids, "doid_code", "uberon_id")
        if not dla.empty:
            dla = anatomy_meta[["uberon_id", "uberon_name"]].drop_duplicates().merge(dla)
            dla = disease_meta[["doid_code", "doid_name"]].drop_duplicates().merge(dla)
            dla = dla[dla["p_fisher"] < P_FISHER_THRESHOLD].sort_values(["doid_name", "p_fisher"])
            result["disease_anatomy_cooccurrence"] = dla

        drd = self._score_pmid_cooccurrence(disease_to_pmids, disease_to_pmids, "doid_code_0", "doid_code_1")
        if not drd.empty:
            drd = drd[drd["doid_code_0"] != drd["doid_code_1"]]
            doid_names = disease_meta[["doid_code", "doid_name"]].drop_duplicates()
            drd = doid_names.rename(columns={"doid_code": "doid_code_1", "doid_name": "doid_name_1"}).merge(drd)
            drd = doid_names.rename(columns={"doid_code": "doid_code_0", "doid_name": "doid_name_0"}).merge(drd)
            drd["_pair"] = drd.apply(
                lambda r: frozenset([r["doid_code_0"], r["doid_code_1"]]), axis=1
            )
            drd = drd.drop_duplicates(subset=["_pair"]).drop(columns=["_pair"])
            drd = drd[drd["p_fisher"] < P_FISHER_THRESHOLD].sort_values(["doid_name_0", "p_fisher"])
            result["disease_disease_cooccurrence"] = drd

        return result

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        return {
            "disease_symptom_cooccurrence": {
                "doid_code": "Disease Ontology ID",
                "doid_name": "Disease name",
                "mesh_id": "MeSH symptom ID",
                "mesh_name": "MeSH symptom name",
                "cooccurrence": "Co-occurring PubMed articles",
                "expected": "Expected co-occurrences under independence",
                "enrichment": "Observed/expected ratio",
                "odds_ratio": "Fisher's odds ratio",
                "p_fisher": "Fisher's exact test p-value (one-sided greater)",
                "n_source": "Disease article count",
                "n_target": "Symptom article count",
            },
            "disease_anatomy_cooccurrence": {
                "doid_code": "Disease Ontology ID",
                "doid_name": "Disease name",
                "uberon_id": "UBERON anatomy ID",
                "uberon_name": "Anatomy name",
                "cooccurrence": "Co-occurring PubMed articles",
                "expected": "Expected co-occurrences under independence",
                "enrichment": "Observed/expected ratio",
                "odds_ratio": "Fisher's odds ratio",
                "p_fisher": "Fisher's exact test p-value (one-sided greater)",
                "n_source": "Disease article count",
                "n_target": "Anatomy article count",
            },
            "disease_disease_cooccurrence": {
                "doid_code_0": "Disease Ontology ID (first disease)",
                "doid_name_0": "First disease name",
                "doid_code_1": "Disease Ontology ID (second disease)",
                "doid_name_1": "Second disease name",
                "cooccurrence": "Co-occurring PubMed articles",
                "expected": "Expected co-occurrences under independence",
                "enrichment": "Observed/expected ratio",
                "odds_ratio": "Fisher's odds ratio",
                "p_fisher": "Fisher's exact test p-value (one-sided greater)",
                "n_source": "First disease article count",
                "n_target": "Second disease article count",
            },
        }

    # ------------------------------------------------------------------
    # Entity list builders
    # ------------------------------------------------------------------

    def _parse_mesh_xml(self) -> list:
        """Parse MeSH XML. Returns list of {mesh_id, mesh_name, tree_numbers} dicts."""
        xml_path = self._mesh_dir / f"desc{MESH_YEAR}.xml"
        if not xml_path.exists():
            logger.error(f"MeSH XML not found: {xml_path}")
            return []
        logger.info(f"Parsing MeSH XML from {xml_path}")
        descriptors = []
        context = etree.iterparse(str(xml_path), events=("end",), tag="DescriptorRecord")
        for _, elem in context:
            ui = elem.findtext(".//DescriptorUI")
            name = elem.findtext(".//DescriptorName/String")
            if ui and name:
                tree_numbers = [tn.text for tn in elem.findall(".//TreeNumber") if tn.text]
                descriptors.append({"mesh_id": ui, "mesh_name": name, "tree_numbers": tree_numbers})
            elem.clear()
        logger.info(f"Loaded {len(descriptors)} MeSH descriptors")
        return descriptors

    def _load_disease_list(self, mesh_names: Dict[str, str]) -> Optional[pd.DataFrame]:
        """Build disease→MeSH mapping from disease_xrefs.tsv and disease_nodes.tsv."""
        xrefs_path = self._processed_dir / "disease_ontology" / "disease_xrefs.tsv"
        nodes_path = self._processed_dir / "disease_ontology" / "disease_nodes.tsv"
        for path in (xrefs_path, nodes_path):
            if not path.exists():
                logger.error(f"Required file not found: {path}")
                return None

        xrefs_df = pd.read_csv(xrefs_path, sep="\t")
        xrefs_df = xrefs_df[xrefs_df["xref"].str.startswith("MESH:")].copy()
        xrefs_df["mesh_id"] = xrefs_df["xref"].str.split(":", n=1).str[1]
        xrefs_df = xrefs_df.rename(columns={"doid": "doid_code"})[["doid_code", "mesh_id"]]

        nodes_df = pd.read_csv(nodes_path, sep="\t")[["doid", "name"]].rename(
            columns={"doid": "doid_code", "name": "doid_name"}
        )
        disease_df = xrefs_df.merge(nodes_df, on="doid_code", how="inner")
        disease_df["mesh_name"] = disease_df["mesh_id"].map(mesh_names)
        disease_df = disease_df.dropna(subset=["mesh_name"])
        disease_df = disease_df[~disease_df["mesh_id"].isin(EXCLUDED_MESH_IDS)]
        logger.info(f"Loaded {len(disease_df)} disease→MeSH mappings")
        return disease_df

    def _load_symptom_list(self, mesh_terms: list) -> pd.DataFrame:
        """Extract symptom terms from MeSH C23.888 subtree."""
        symptoms = [
            {"mesh_id": t["mesh_id"], "mesh_name": t["mesh_name"]}
            for t in mesh_terms
            if any(tn.startswith(SYMPTOM_TREE_PREFIX) for tn in t["tree_numbers"])
        ]
        df = pd.DataFrame(symptoms)
        logger.info(f"Loaded {len(df)} symptom terms from MeSH {SYMPTOM_TREE_PREFIX[:-1]}")
        return df

    def _load_anatomy_list(self, mesh_names: Dict[str, str]) -> Optional[pd.DataFrame]:
        """Load UBERON→MeSH anatomy mapping from uberon_mesh_xrefs.tsv (UberonParser output)."""
        xrefs_path = self._processed_dir / "uberon" / "uberon_mesh_xrefs.tsv"
        if not xrefs_path.exists():
            logger.error(f"uberon_mesh_xrefs.tsv not found: {xrefs_path}; run UberonParser first")
            return None
        df = pd.read_csv(xrefs_path, sep="\t")
        # One MeSH query per UBERON term; take first mesh_id when multiple exist
        df = df.drop_duplicates(subset=["uberon_id"], keep="first")
        df["mesh_name"] = df["mesh_id"].map(mesh_names)
        df = df.dropna(subset=["mesh_name"])
        logger.info(f"Loaded {len(df)} anatomy terms from {xrefs_path}")
        return df

    # ------------------------------------------------------------------
    # PubMed querying and PMID caching
    # ------------------------------------------------------------------

    def _fetch_pmids(self, query: str) -> Set[str]:
        """Fetch all PMIDs matching query from NCBI E-utilities (esearch)."""
        params: Dict = {
            "db": "pubmed",
            "term": query,
            "retmax": 10000,
            "retstart": 0,
            "retmode": "json",
        }
        pmids: Set[str] = set()
        count = 1
        while params["retstart"] < count:
            try:
                resp = requests.get(EUTILS_URL, params=params, timeout=30)
                resp.raise_for_status()
                result = resp.json().get("esearchresult", {})
                count = int(result.get("count", 0))
                pmids.update(result.get("idlist", []))
                params["retstart"] += params["retmax"]
                time.sleep(EUTILS_SLEEP)
            except Exception as exc:
                logger.error(f"PubMed query failed for '{query}': {exc}")
                break
        return pmids

    def _compute_pmids_file(
        self,
        df: pd.DataFrame,
        id_col: str,
        name_col: str,
        query_template: str,
        out_path: Path,
    ) -> None:
        """
        Query PubMed for each row and save PMIDs to a gzipped TSV.

        Skips if out_path already exists and force=False.
        """
        if out_path.exists() and not self.force:
            logger.info(f"Using cached PMIDs: {out_path}")
            return

        rows = []
        for _, row in df.iterrows():
            query = query_template.format(name=row[name_col].lower())
            pmids = self._fetch_pmids(query)
            entry = row.to_dict()
            entry["term_query"] = query
            entry["n_articles"] = len(pmids)
            entry["pubmed_ids"] = "|".join(sorted(pmids))
            rows.append(entry)
            logger.info(f"  {len(pmids):5d} articles: {row[name_col]}")

        pd.DataFrame(rows).to_csv(out_path, sep="\t", index=False, compression="gzip")
        logger.info(f"Saved PMIDs to {out_path}")

    def _read_pmids_tsv(
        self, path: Path, key: str, min_articles: int = 1
    ) -> Tuple[pd.DataFrame, Dict[str, Set[str]]]:
        """Read gzipped pmids TSV. Returns (metadata_df, term→pmids dict)."""
        df = pd.read_csv(path, sep="\t", compression="gzip")
        df = df[df["n_articles"] >= min_articles].copy()
        term_to_pmids: Dict[str, Set[str]] = {}
        for _, row in df.iterrows():
            if pd.notna(row["pubmed_ids"]) and row["pubmed_ids"]:
                term_to_pmids[row[key]] = set(str(row["pubmed_ids"]).split("|"))
        df = df.drop(columns=["pubmed_ids"], errors="ignore")
        return df, term_to_pmids

    # ------------------------------------------------------------------
    # Cooccurrence computation
    # ------------------------------------------------------------------

    @staticmethod
    def _cooccurrence_metrics(
        source_pmids: Set[str], target_pmids: Set[str], total_pmids: int
    ) -> dict:
        """Compute Fisher's exact test and enrichment for two PMID sets."""
        a = len(source_pmids & target_pmids)
        b = len(source_pmids) - a
        c = len(target_pmids) - a
        d = total_pmids - (a + b + c)
        expected = len(source_pmids) * len(target_pmids) / total_pmids if total_pmids else 0.0
        enrichment = a / expected if expected > 0 else 0.0
        odds_ratio, p_fisher = scipy.stats.fisher_exact([[a, b], [c, d]], alternative="greater")
        return {
            "cooccurrence": a,
            "expected": expected,
            "enrichment": enrichment,
            "odds_ratio": odds_ratio,
            "p_fisher": p_fisher,
            "n_source": len(source_pmids),
            "n_target": len(target_pmids),
        }

    def _score_pmid_cooccurrence(
        self,
        term0_to_pmids: Dict[str, Set[str]],
        term1_to_pmids: Dict[str, Set[str]],
        term0_col: str,
        term1_col: str,
    ) -> pd.DataFrame:
        """Compute pairwise cooccurrence for all term pairs sharing at least one PMID."""
        if not term0_to_pmids or not term1_to_pmids:
            return pd.DataFrame()

        shared = set.union(*term0_to_pmids.values()) & set.union(*term1_to_pmids.values())
        total = len(shared)
        logger.info(f"Shared PMIDs for {term0_col}×{term1_col}: {total}")

        t0 = {k: v & shared for k, v in term0_to_pmids.items() if v & shared}
        t1 = {k: v & shared for k, v in term1_to_pmids.items() if v & shared}

        rows = [
            {
                term0_col: k0,
                term1_col: k1,
                **self._cooccurrence_metrics(t0[k0], t1[k1], total),
            }
            for k0, k1 in itertools.product(t0, t1)
        ]
        logger.info(f"Computed {len(rows)} cooccurrence pairs for {term0_col}×{term1_col}")
        return pd.DataFrame(rows)
