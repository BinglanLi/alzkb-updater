"""
Hetionet component parsers for AlzKB.

This module provides individual parsers for each data source that was
originally part of Hetionet or needed to build Hetionet-like relationships.

Each parser extends BaseParser and provides:
- download_data(): Download source data files
- parse_data(): Parse and return standardized DataFrames
- get_schema(): Return schema documentation

Available Parsers:
- DiseaseOntologyParser: Disease nodes from Disease Ontology
- GeneOntologyParser: BP, MF, CC nodes and gene-GO associations
- UberonParser: Anatomy/BodyPart nodes from Uberon
- MeSHParser: Symptom nodes from MeSH
- GWASParser: Gene-disease associations from GWAS Catalog
- DrugCentralParser: Drug-disease treatment relationships
- BindingDBParser: Drug-gene binding relationships
- BgeeParser: Gene expression in anatomy
- CTDParser: Chemical-gene expression changes
- HetionetPrecomputedParser: Pre-computed gene-gene relationships
- PubTatorParser: Literature-mined co-occurrences
"""

from .disease_ontology_parser import DiseaseOntologyParser
from .gene_ontology_parser import GeneOntologyParser
from .uberon_parser import UberonParser
from .mesh_parser import MeSHParser
from .gwas_parser import GWASParser
from .drugcentral_parser import DrugCentralParser
from .bindingdb_parser import BindingDBParser
from .bgee_parser import BgeeParser
from .ctd_parser import CTDParser
from .hetionet_precomputed_parser import HetionetPrecomputedParser
from .pubtator_parser import PubTatorParser

__all__ = [
    'DiseaseOntologyParser',
    'GeneOntologyParser',
    'UberonParser',
    'MeSHParser',
    'GWASParser',
    'DrugCentralParser',
    'BindingDBParser',
    'BgeeParser',
    'CTDParser',
    'HetionetPrecomputedParser',
    'PubTatorParser',
]
