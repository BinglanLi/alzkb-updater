"""
PubTator/MEDLINE Parser for AlzKB.

This module parses PubTator Central data to extract literature-mined
associations including:
- Disease-disease co-occurrence (diseaseAssociatesWithDisease)
- Disease-symptom co-occurrence (symptomManifestationOfDisease)
- Gene-disease literature associations (supplemental)

PubTator Central provides pre-computed bioconcept annotations from MEDLINE,
updated weekly by NCBI.

Data Sources:
  - https://ftp.ncbi.nlm.nih.gov/pub/lu/PubTatorCentral/
  - PubTator3 API: https://www.ncbi.nlm.nih.gov/research/pubtator3-api/

Output:
  - disease_disease_cooccurrence.tsv: diseaseAssociatesWithDisease
  - disease_symptom_literature.tsv: symptomManifestationOfDisease
  - gene_disease_literature.tsv: Literature-based gene-disease associations
"""

import logging
import gzip
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
import pandas as pd

from ..base_parser import BaseParser

logger = logging.getLogger(__name__)


class PubTatorParser(BaseParser):
    """
    Parser for PubTator Central / MEDLINE literature mining data.

    Extracts co-occurrence relationships from literature for use in AlzKB.
    Uses pre-computed bioconcept2pubtator files from NCBI FTP.
    """

    # PubTator Central FTP base URL
    PUBTATOR_FTP = "https://ftp.ncbi.nlm.nih.gov/pub/lu/PubTatorCentral/"

    # Bioconcept files
    DISEASE_FILE = "disease2pubtatorcentral.gz"
    GENE_FILE = "gene2pubtatorcentral.gz"
    CHEMICAL_FILE = "chemical2pubtatorcentral.gz"

    def __init__(self, data_dir: str):
        """
        Initialize the PubTator parser.

        Args:
            data_dir: Directory to store downloaded and processed data
        """
        super().__init__(data_dir)
        self.source_name = "pubtator"

    def download_data(self) -> bool:
        """
        Download PubTator bioconcept files.

        Returns:
            True if at least one file was downloaded successfully
        """
        logger.info("Downloading PubTator Central bioconcept files...")

        success = False

        # Download disease annotations
        disease_result = self.download_file(
            f"{self.PUBTATOR_FTP}{self.DISEASE_FILE}",
            self.DISEASE_FILE
        )
        if disease_result:
            logger.info("Downloaded disease annotations")
            success = True

        # Download gene annotations
        gene_result = self.download_file(
            f"{self.PUBTATOR_FTP}{self.GENE_FILE}",
            self.GENE_FILE
        )
        if gene_result:
            logger.info("Downloaded gene annotations")
            success = True

        # Download chemical annotations
        chemical_result = self.download_file(
            f"{self.PUBTATOR_FTP}{self.CHEMICAL_FILE}",
            self.CHEMICAL_FILE
        )
        if chemical_result:
            logger.info("Downloaded chemical annotations")
            success = True

        return success

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse PubTator bioconcept files and compute co-occurrences.

        Returns:
            Dictionary with co-occurrence DataFrames
        """
        result = {}

        # Parse disease annotations
        disease_path = self.source_dir / self.DISEASE_FILE
        if disease_path.exists():
            disease_annotations = self._parse_bioconcept_file(disease_path, "Disease")
            logger.info(f"Parsed {len(disease_annotations)} disease annotation PMIDs")

            # Compute disease-disease co-occurrence
            disease_cooc = self._compute_cooccurrence(disease_annotations, "Disease", "Disease")
            if disease_cooc:
                result["disease_disease_cooccurrence"] = self._format_disease_cooccurrence(disease_cooc)
                logger.info(f"Found {len(disease_cooc)} disease-disease co-occurrences")

        # Parse gene annotations
        gene_path = self.source_dir / self.GENE_FILE
        if gene_path.exists():
            gene_annotations = self._parse_bioconcept_file(gene_path, "Gene")
            logger.info(f"Parsed {len(gene_annotations)} gene annotation PMIDs")

            # Compute gene-disease co-occurrence (if both available)
            if disease_path.exists():
                gene_disease_cooc = self._compute_cross_cooccurrence(
                    gene_annotations, disease_annotations, "Gene", "Disease"
                )
                if gene_disease_cooc:
                    result["gene_disease_literature"] = self._format_gene_disease_cooccurrence(gene_disease_cooc)
                    logger.info(f"Found {len(gene_disease_cooc)} gene-disease co-occurrences")

        return result

    def _parse_bioconcept_file(self, file_path: Path, concept_type: str) -> Dict[str, set]:
        """
        Parse a PubTator bioconcept file.

        Format: PMID \t Type \t ConceptID \t Mentions \t Resource
        Returns: Dict mapping PMID to set of concept IDs found in that article

        Args:
            file_path: Path to gzipped bioconcept file
            concept_type: Type of concept (Disease, Gene, Chemical)

        Returns:
            Dictionary mapping PMID to set of concept IDs
        """
        pmid_concepts = defaultdict(set)

        try:
            with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) < 3:
                        continue

                    pmid = parts[0]
                    concept_id = parts[2]

                    # Skip empty or placeholder IDs
                    if not concept_id or concept_id == '-':
                        continue

                    pmid_concepts[pmid].add(concept_id)

        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")

        return dict(pmid_concepts)

    def _compute_cooccurrence(
        self,
        annotations: Dict[str, set],
        type1: str,
        type2: str,
        min_pmids: int = 3
    ) -> Dict[tuple, int]:
        """
        Compute co-occurrence counts for concepts within same PMIDs.

        Args:
            annotations: Dict mapping PMID to concept sets
            type1, type2: Concept types (for same-type co-occurrence)
            min_pmids: Minimum PMIDs for co-occurrence to be included

        Returns:
            Dictionary mapping (concept1, concept2) to co-occurrence count
        """
        cooccurrence = defaultdict(int)

        for pmid, concepts in annotations.items():
            concepts_list = list(concepts)

            # Count all pairs of concepts in same PMID
            for i in range(len(concepts_list)):
                for j in range(i + 1, len(concepts_list)):
                    c1, c2 = concepts_list[i], concepts_list[j]
                    # Normalize order for consistent keys
                    if c1 > c2:
                        c1, c2 = c2, c1
                    cooccurrence[(c1, c2)] += 1

        # Filter by minimum PMIDs
        filtered = {k: v for k, v in cooccurrence.items() if v >= min_pmids}

        return filtered

    def _compute_cross_cooccurrence(
        self,
        annotations1: Dict[str, set],
        annotations2: Dict[str, set],
        type1: str,
        type2: str,
        min_pmids: int = 2
    ) -> Dict[tuple, int]:
        """
        Compute co-occurrence between two different concept types.

        Args:
            annotations1, annotations2: Concept annotations dicts
            type1, type2: Concept types
            min_pmids: Minimum PMIDs for co-occurrence

        Returns:
            Dictionary mapping (concept1, concept2) to co-occurrence count
        """
        cooccurrence = defaultdict(int)

        # Find common PMIDs
        common_pmids = set(annotations1.keys()) & set(annotations2.keys())

        for pmid in common_pmids:
            concepts1 = annotations1[pmid]
            concepts2 = annotations2[pmid]

            # Count all cross-type pairs
            for c1 in concepts1:
                for c2 in concepts2:
                    cooccurrence[(c1, c2)] += 1

        # Filter by minimum PMIDs
        filtered = {k: v for k, v in cooccurrence.items() if v >= min_pmids}

        return filtered

    def _format_disease_cooccurrence(self, cooccurrence: Dict[tuple, int]) -> pd.DataFrame:
        """
        Format disease-disease co-occurrence as DataFrame.

        Args:
            cooccurrence: Co-occurrence counts dictionary

        Returns:
            Formatted DataFrame
        """
        records = []
        for (disease1, disease2), count in cooccurrence.items():
            records.append({
                "disease1_id": disease1,
                "disease2_id": disease2,
                "pmid_count": count,
                "relationship": "diseaseAssociatesWithDisease",
                "source": "PubTator_MEDLINE"
            })

        return pd.DataFrame(records)

    def _format_gene_disease_cooccurrence(self, cooccurrence: Dict[tuple, int]) -> pd.DataFrame:
        """
        Format gene-disease co-occurrence as DataFrame.

        Args:
            cooccurrence: Co-occurrence counts dictionary

        Returns:
            Formatted DataFrame
        """
        records = []
        for (gene_id, disease_id), count in cooccurrence.items():
            records.append({
                "gene_id": gene_id,
                "disease_id": disease_id,
                "pmid_count": count,
                "relationship": "geneAssociatesWithDisease",
                "source": "PubTator_MEDLINE"
            })

        return pd.DataFrame(records)

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for PubTator data.

        Returns:
            Dictionary defining the schema for co-occurrence data
        """
        return {
            "disease_disease_cooccurrence": {
                "disease1_id": "First disease ID (MESH or OMIM)",
                "disease2_id": "Second disease ID",
                "pmid_count": "Number of PMIDs with co-occurrence",
                "relationship": "Relationship type (diseaseAssociatesWithDisease)",
                "source": "Data source (PubTator_MEDLINE)"
            },
            "gene_disease_literature": {
                "gene_id": "NCBI Gene ID",
                "disease_id": "Disease ID (MESH or OMIM)",
                "pmid_count": "Number of PMIDs with co-occurrence",
                "relationship": "Relationship type (geneAssociatesWithDisease)",
                "source": "Data source (PubTator_MEDLINE)"
            }
        }
