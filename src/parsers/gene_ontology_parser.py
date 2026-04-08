"""
Gene Ontology Parser for AlzKB.

This module parses the Gene Ontology (GO) to extract:
- Biological Process (BP) nodes
- Molecular Function (MF) nodes
- Cellular Component (CC) nodes
- Gene-GO associations (aggregated by GO term)

Data Sources:
  - GO OBO: http://current.geneontology.org/ontology/go-basic.obo
  - NCBI gene2go: https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2go.gz
  - GOA Human: http://current.geneontology.org/annotations/goa_human.gaf.gz (fallback)

Output:
  - biological_process_nodes.tsv
  - molecular_function_nodes.tsv
  - cellular_component_nodes.tsv
  - go_annotations.tsv: Aggregated gene-GO annotations (matches Hetionet format)
  - gene_bp_associations.tsv (geneParticipatesInBiologicalProcess)
  - gene_mf_associations.tsv (geneHasMolecularFunction)
  - gene_cc_associations.tsv (geneAssociatedWithCellularComponent)
"""

import logging
import gzip
from pathlib import Path
from typing import Dict, Optional, List, Set
import pandas as pd

try:
    import obonet
except ImportError:
    obonet = None

try:
    import pronto
except ImportError:
    pronto = None

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class GeneOntologyParser(BaseParser):
    """
    Parser for the Gene Ontology (GO).

    Extracts GO terms (BP, MF, CC) and gene-GO associations from
    the GO OBO file and GOA annotations.
    """

    # Gene Ontology URLs
    GO_OBO_URL = "http://current.geneontology.org/ontology/go-basic.obo"
    GOA_HUMAN_URL = "http://current.geneontology.org/annotations/goa_human.gaf.gz"

    # NCBI gene2go - primary source for gene-GO associations (same as used by Hetionet)
    GENE2GO_URL = "https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2go.gz"

    # Human taxonomy ID
    HUMAN_TAX_ID = 9606

    # GO namespaces
    NAMESPACES = {
        "biological_process": "BP",
        "molecular_function": "MF",
        "cellular_component": "CC"
    }

    # Namespace mapping for gene2go Category column
    CATEGORY_TO_NAMESPACE = {
        "Process": "biological_process",
        "Function": "molecular_function",
        "Component": "cellular_component"
    }

    def __init__(self, data_dir: str, gene_symbol_map: Dict[int, str] = None):
        """
        Initialize the Gene Ontology parser.

        Args:
            data_dir: Directory to store downloaded and processed data
            gene_symbol_map: Optional dict mapping Entrez Gene ID to symbol
                            (used for creating aggregated annotations)
        """
        super().__init__(data_dir)
        self.source_name = "gene_ontology"
        self.gene_symbol_map = gene_symbol_map or {}

    def download_data(self) -> bool:
        """
        Download the Gene Ontology OBO and gene2go annotation files.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading Gene Ontology files...")

        # Download GO OBO
        obo_result = self.download_file(self.GO_OBO_URL, "go-basic.obo")
        if not obo_result:
            logger.error("Failed to download GO OBO file")
            return False
        logger.info(f"Successfully downloaded GO OBO to {obo_result}")

        # Download NCBI gene2go (primary source, same as Hetionet)
        gene2go_result = self.download_file(self.GENE2GO_URL, "gene2go.gz")
        if not gene2go_result:
            logger.warning("Failed to download gene2go - will try GOA annotations")
            # Fallback to GOA Human annotations
            goa_result = self.download_file(self.GOA_HUMAN_URL, "goa_human.gaf.gz")
            if not goa_result:
                logger.warning("Failed to download GOA annotations - continuing without gene associations")
        else:
            logger.info(f"Successfully downloaded gene2go to {gene2go_result}")

        logger.info("Successfully downloaded Gene Ontology files")
        return True

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse GO OBO and gene2go annotation files.

        Returns:
            Dictionary with DataFrames for GO terms and gene associations
        """
        result = {}

        # Parse GO ontology first to get GO term names
        obo_path = self.source_dir / "go-basic.obo"
        go_term_info = {}  # go_id -> {name, namespace}
        if obo_path.exists():
            go_terms = self._parse_go_ontology(obo_path)
            result.update(go_terms)

            # Build lookup for GO term names and namespaces
            for key in ["biological_process_nodes", "molecular_function_nodes", "cellular_component_nodes"]:
                if key in go_terms:
                    for _, row in go_terms[key].iterrows():
                        go_term_info[row['go_id']] = {
                            'name': row['name'],
                            'namespace': row['namespace']
                        }
        else:
            logger.error(f"GO OBO file not found: {obo_path}")

        # Parse gene2go (primary source, same as Hetionet)
        gene2go_path = self.source_dir / "gene2go.gz"
        if gene2go_path.exists():
            associations = self._parse_gene2go(gene2go_path, go_term_info)
            result.update(associations)
        else:
            # Fallback to GOA annotations
            logger.warning(f"gene2go not found, trying GOA annotations")
            goa_path = self.source_dir / "goa_human.gaf.gz"
            if goa_path.exists():
                associations = self._parse_goa_annotations(goa_path)
                result.update(associations)
            else:
                logger.warning(f"GOA annotations not found: {goa_path}")

        return result

    def _parse_go_ontology(self, obo_path: Path) -> Dict[str, pd.DataFrame]:
        """
        Parse the GO OBO file to extract terms.

        Args:
            obo_path: Path to the GO OBO file

        Returns:
            Dictionary with DataFrames for BP, MF, CC terms
        """
        logger.info(f"Parsing GO ontology from {obo_path}")

        if obonet:
            return self._parse_go_with_obonet(obo_path)
        elif pronto:
            return self._parse_go_with_pronto(obo_path)
        else:
            logger.error("Neither obonet nor pronto is installed")
            return {}

    def _parse_go_with_obonet(self, obo_path: Path) -> Dict[str, pd.DataFrame]:
        """Parse GO using obonet."""
        try:
            graph = obonet.read_obo(str(obo_path))

            bp_terms = []
            mf_terms = []
            cc_terms = []

            for node_id, node_data in graph.nodes(data=True):
                if not node_id.startswith("GO:"):
                    continue

                if node_data.get("is_obsolete", False):
                    continue

                namespace = node_data.get("namespace", "")
                term = {
                    "go_id": node_id,
                    "name": node_data.get("name", ""),
                    "definition": self._clean_definition(node_data.get("def", "")),
                    "namespace": namespace
                }

                if namespace == "biological_process":
                    bp_terms.append(term)
                elif namespace == "molecular_function":
                    mf_terms.append(term)
                elif namespace == "cellular_component":
                    cc_terms.append(term)

            logger.info(f"Parsed {len(bp_terms)} BP, {len(mf_terms)} MF, {len(cc_terms)} CC terms")

            return {
                "biological_process_nodes": pd.DataFrame(bp_terms),
                "molecular_function_nodes": pd.DataFrame(mf_terms),
                "cellular_component_nodes": pd.DataFrame(cc_terms)
            }

        except Exception as e:
            logger.error(f"Error parsing GO with obonet: {e}")
            return {}

    def _parse_go_with_pronto(self, obo_path: Path) -> Dict[str, pd.DataFrame]:
        """Parse GO using pronto."""
        try:
            ontology = pronto.Ontology(str(obo_path))

            bp_terms = []
            mf_terms = []
            cc_terms = []

            for term in ontology.terms():
                if not term.id.startswith("GO:"):
                    continue

                if term.obsolete:
                    continue

                namespace = term.namespace or ""
                term_data = {
                    "go_id": term.id,
                    "name": term.name or "",
                    "definition": str(term.definition) if term.definition else "",
                    "namespace": namespace
                }

                if namespace == "biological_process":
                    bp_terms.append(term_data)
                elif namespace == "molecular_function":
                    mf_terms.append(term_data)
                elif namespace == "cellular_component":
                    cc_terms.append(term_data)

            logger.info(f"Parsed {len(bp_terms)} BP, {len(mf_terms)} MF, {len(cc_terms)} CC terms")

            return {
                "biological_process_nodes": pd.DataFrame(bp_terms),
                "molecular_function_nodes": pd.DataFrame(mf_terms),
                "cellular_component_nodes": pd.DataFrame(cc_terms)
            }

        except Exception as e:
            logger.error(f"Error parsing GO with pronto: {e}")
            return {}

    def _parse_goa_annotations(self, goa_path: Path) -> Dict[str, pd.DataFrame]:
        """
        Parse GOA annotation file to extract gene-GO associations.

        Args:
            goa_path: Path to the GOA GAF file (gzipped)

        Returns:
            Dictionary with DataFrames for gene-BP, gene-MF, gene-CC associations
        """
        logger.info(f"Parsing GOA annotations from {goa_path}")

        try:
            # GAF 2.2 column names
            columns = [
                "DB", "DB_Object_ID", "DB_Object_Symbol", "Qualifier", "GO_ID",
                "DB_Reference", "Evidence_Code", "With_From", "Aspect",
                "DB_Object_Name", "DB_Object_Synonym", "DB_Object_Type",
                "Taxon", "Date", "Assigned_By", "Annotation_Extension",
                "Gene_Product_Form_ID"
            ]

            # Read GAF file (skip comment lines)
            rows = []
            with gzip.open(goa_path, 'rt') as f:
                for line in f:
                    if line.startswith('!'):
                        continue
                    parts = line.strip().split('\t')
                    if len(parts) >= 15:
                        rows.append(parts[:17] if len(parts) >= 17 else parts + [''] * (17 - len(parts)))

            df = pd.DataFrame(rows, columns=columns)

            # Filter for human genes (taxon:9606)
            df = df[df['Taxon'].str.contains('taxon:9606', na=False)]

            # Separate by aspect (P=BP, F=MF, C=CC)
            bp_assoc = df[df['Aspect'] == 'P'][['DB_Object_Symbol', 'GO_ID', 'Evidence_Code']].copy()
            bp_assoc.columns = ['gene_symbol', 'go_id', 'evidence']
            bp_assoc['relationship'] = 'geneParticipatesInBiologicalProcess'

            mf_assoc = df[df['Aspect'] == 'F'][['DB_Object_Symbol', 'GO_ID', 'Evidence_Code']].copy()
            mf_assoc.columns = ['gene_symbol', 'go_id', 'evidence']
            mf_assoc['relationship'] = 'geneHasMolecularFunction'

            cc_assoc = df[df['Aspect'] == 'C'][['DB_Object_Symbol', 'GO_ID', 'Evidence_Code']].copy()
            cc_assoc.columns = ['gene_symbol', 'go_id', 'evidence']
            cc_assoc['relationship'] = 'geneAssociatedWithCellularComponent'

            # Remove duplicates
            bp_assoc = bp_assoc.drop_duplicates(subset=['gene_symbol', 'go_id'])
            mf_assoc = mf_assoc.drop_duplicates(subset=['gene_symbol', 'go_id'])
            cc_assoc = cc_assoc.drop_duplicates(subset=['gene_symbol', 'go_id'])

            logger.info(f"Parsed {len(bp_assoc)} BP, {len(mf_assoc)} MF, {len(cc_assoc)} CC associations")

            return {
                "gene_bp_associations": bp_assoc,
                "gene_mf_associations": mf_assoc,
                "gene_cc_associations": cc_assoc
            }

        except Exception as e:
            logger.error(f"Error parsing GOA annotations: {e}")
            return {}

    def _parse_gene2go(self, gene2go_path: Path, go_term_info: Dict) -> Dict[str, pd.DataFrame]:
        """
        Parse NCBI gene2go file to extract gene-GO associations.

        Creates aggregated output matching the Hetionet format:
        GO_annotations-9606-inferred-allev.tsv with columns:
        go_id, go_name, go_domain, tax_id, annotation_type, size, gene_ids, gene_symbols

        Args:
            gene2go_path: Path to gene2go.gz
            go_term_info: Dict mapping go_id to {name, namespace}

        Returns:
            Dictionary with DataFrames for aggregated annotations and individual associations
        """
        logger.info(f"Parsing gene2go from {gene2go_path}")

        try:
            # gene2go columns: tax_id, GeneID, GO_ID, Evidence, Qualifier, GO_term, PubMed, Category
            df = pd.read_csv(
                gene2go_path,
                sep='\t',
                compression='gzip',
                comment='#',
                names=['tax_id', 'GeneID', 'GO_ID', 'Evidence', 'Qualifier', 'GO_term', 'PubMed', 'Category'],
                dtype={'tax_id': int, 'GeneID': int}
            )

            logger.info(f"Loaded {len(df)} gene2go records")

            # Filter for human genes only
            df = df[df['tax_id'] == self.HUMAN_TAX_ID]
            logger.info(f"After human filter: {len(df)} records")

            # Map Category to namespace
            df['namespace'] = df['Category'].map(self.CATEGORY_TO_NAMESPACE)

            # Get gene symbols from map if available
            if self.gene_symbol_map:
                df['gene_symbol'] = df['GeneID'].map(self.gene_symbol_map)
            else:
                df['gene_symbol'] = df['GeneID'].astype(str)

            # Aggregate by GO term to create the Hetionet format
            aggregated = []
            for go_id, group in df.groupby('GO_ID'):
                gene_ids = sorted(group['GeneID'].unique())
                gene_symbols = [self.gene_symbol_map.get(gid, str(gid)) for gid in gene_ids]

                # Get GO term name and namespace from OBO data or gene2go
                if go_id in go_term_info:
                    go_name = go_term_info[go_id]['name']
                    namespace = go_term_info[go_id]['namespace']
                else:
                    go_name = group['GO_term'].iloc[0] if 'GO_term' in group.columns else ''
                    namespace = group['namespace'].iloc[0] if 'namespace' in group.columns else ''

                aggregated.append({
                    'go_id': go_id,
                    'go_name': go_name,
                    'go_domain': namespace,
                    'tax_id': self.HUMAN_TAX_ID,
                    'annotation_type': 'inferred',
                    'size': len(gene_ids),
                    'gene_ids': '|'.join(map(str, gene_ids)),
                    'gene_symbols': '|'.join(gene_symbols)
                })

            go_annotations_df = pd.DataFrame(aggregated)
            logger.info(f"Created {len(go_annotations_df)} aggregated GO annotations")

            # Also create individual associations for backward compatibility
            bp_assoc = df[df['namespace'] == 'biological_process'][['GeneID', 'GO_ID', 'Evidence', 'gene_symbol']].copy()
            bp_assoc.columns = ['entrez_gene_id', 'go_id', 'evidence', 'gene_symbol']
            bp_assoc['relationship'] = 'geneParticipatesInBiologicalProcess'
            bp_assoc = bp_assoc.drop_duplicates(subset=['entrez_gene_id', 'go_id'])

            mf_assoc = df[df['namespace'] == 'molecular_function'][['GeneID', 'GO_ID', 'Evidence', 'gene_symbol']].copy()
            mf_assoc.columns = ['entrez_gene_id', 'go_id', 'evidence', 'gene_symbol']
            mf_assoc['relationship'] = 'geneHasMolecularFunction'
            mf_assoc = mf_assoc.drop_duplicates(subset=['entrez_gene_id', 'go_id'])

            cc_assoc = df[df['namespace'] == 'cellular_component'][['GeneID', 'GO_ID', 'Evidence', 'gene_symbol']].copy()
            cc_assoc.columns = ['entrez_gene_id', 'go_id', 'evidence', 'gene_symbol']
            cc_assoc['relationship'] = 'geneAssociatedWithCellularComponent'
            cc_assoc = cc_assoc.drop_duplicates(subset=['entrez_gene_id', 'go_id'])

            logger.info(f"Parsed {len(bp_assoc)} BP, {len(mf_assoc)} MF, {len(cc_assoc)} CC individual associations")

            return {
                "go_annotations": go_annotations_df,
                "gene_bp_associations": bp_assoc,
                "gene_mf_associations": mf_assoc,
                "gene_cc_associations": cc_assoc
            }

        except Exception as e:
            logger.error(f"Error parsing gene2go: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}

    def _clean_definition(self, definition: str) -> str:
        """Clean up definition string from OBO format."""
        if not definition:
            return ""
        definition = definition.strip('"')
        if " [" in definition:
            definition = definition.split(" [")[0]
        return definition

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for Gene Ontology data.

        Returns:
            Dictionary defining the schema for GO nodes and associations
        """
        return {
            "biological_process_nodes": {
                "go_id": "Gene Ontology ID (e.g., GO:0008150)",
                "name": "GO term name",
                "definition": "GO term definition",
                "namespace": "GO namespace (biological_process)"
            },
            "molecular_function_nodes": {
                "go_id": "Gene Ontology ID",
                "name": "GO term name",
                "definition": "GO term definition",
                "namespace": "GO namespace (molecular_function)"
            },
            "cellular_component_nodes": {
                "go_id": "Gene Ontology ID",
                "name": "GO term name",
                "definition": "GO term definition",
                "namespace": "GO namespace (cellular_component)"
            },
            "go_annotations": {
                "go_id": "Gene Ontology ID",
                "go_name": "GO term name",
                "go_domain": "GO namespace (biological_process, molecular_function, cellular_component)",
                "tax_id": "Taxonomy ID (9606 for human)",
                "annotation_type": "Annotation type (inferred)",
                "size": "Number of genes annotated to this term",
                "gene_ids": "Pipe-separated Entrez Gene IDs",
                "gene_symbols": "Pipe-separated gene symbols"
            },
            "gene_bp_associations": {
                "entrez_gene_id": "Entrez Gene ID",
                "go_id": "GO term ID",
                "evidence": "Evidence code",
                "gene_symbol": "Gene symbol",
                "relationship": "Relationship type"
            },
            "gene_mf_associations": {
                "entrez_gene_id": "Entrez Gene ID",
                "go_id": "GO term ID",
                "evidence": "Evidence code",
                "gene_symbol": "Gene symbol",
                "relationship": "Relationship type"
            },
            "gene_cc_associations": {
                "entrez_gene_id": "Entrez Gene ID",
                "go_id": "GO term ID",
                "evidence": "Evidence code",
                "gene_symbol": "Gene symbol",
                "relationship": "Relationship type"
            }
        }
