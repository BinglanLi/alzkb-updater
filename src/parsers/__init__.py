"""
Data parsers for AlzKB v2.

This module contains parsers for various data sources used to populate AlzKB.
Each parser is responsible for downloading, parsing, and formatting data from
a specific source.
"""

from .base_parser import BaseParser
from .ncbigene_parser import NCBIGeneParser
from .drugbank_parser import DrugBankParser
from .disgenet_parser import DisGeNETParser
from .aopdb_parser import AOPDBParser

# Hetionet component parsers (replacing HetionetBuilder)
from .hetionet_components import (
    DiseaseOntologyParser,
    GeneOntologyParser,
    UberonParser,
    MeSHParser,
    GWASParser,
    DrugCentralParser,
    BindingDBParser,
    BgeeParser,
    CTDParser,
    HetionetPrecomputedParser,
    PubTatorParser,
    DoRothEAParser,
)

__all__ = [
    'BaseParser',
    'NCBIGeneParser',
    'DrugBankParser',
    'DisGeNETParser',
    'AOPDBParser',
    # Hetionet component parsers
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
    'DoRothEAParser',
]
