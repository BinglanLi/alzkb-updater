"""
Data parsers for the knowledge graph.

This module contains parsers for various data sources used to populate the knowledge graph.
Each parser is responsible for downloading, parsing, and formatting data from
a specific source.
"""

from .base_parser import BaseParser
from .ncbigene_parser import NCBIGeneParser
from .drugbank_parser import DrugBankParser
from .disgenet_parser import DisGeNETParser
from .aopdb_parser import AOPDBParser
from .dorothea_parser import DoRothEAParser
from .collecttri_parser import CollectTRIParser
from .disease_ontology_parser import DiseaseOntologyParser
from .gene_ontology_parser import GeneOntologyParser
from .uberon_parser import UberonParser
from .mesh_parser import MeSHParser
from .gwas_parser import GWASParser
from .drugcentral_parser import DrugCentralParser
from .bindingdb_parser import BindingDBParser
from .bgee_parser import BgeeParser
from .ctd_parser import CTDParser
from .pubtator_parser import PubTatorParser
from .medline_cooccurrence_parser import MEDLINECooccurrenceParser

__all__ = [
    'BaseParser',
    'NCBIGeneParser',
    'DrugBankParser',
    'DisGeNETParser',
    'AOPDBParser',
    'DoRothEAParser',
    'CollectTRIParser',
    'DiseaseOntologyParser',
    'GeneOntologyParser',
    'UberonParser',
    'MeSHParser',
    'GWASParser',
    'DrugCentralParser',
    'BindingDBParser',
    'BgeeParser',
    'CTDParser',
    'PubTatorParser',
    'MEDLINECooccurrenceParser',
]
