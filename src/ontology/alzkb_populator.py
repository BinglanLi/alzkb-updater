"""
AlzKB Ontology Populator using ista

This module provides a unified interface for populating the AlzKB ontology
using ista (Instance Store for Tabular Annotations).

ista is used to convert tabular data (TSV/CSV files) and database records
into RDF format that populates the AlzKB ontology.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import owlready2

from ontology_configs import ONTOLOGY_CONFIGS

# Add ista to Python path if not already installed
ISTA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '.ista')
if os.path.exists(ISTA_PATH) and ISTA_PATH not in sys.path:
    sys.path.insert(0, ISTA_PATH)

try:
    from ista import FlatFileDatabaseParser, MySQLDatabaseParser
except ImportError as e:
    logging.error(f"Failed to import ista: {e}")
    logging.error(f"Please ensure ista is installed at {ISTA_PATH}")
    raise

logger = logging.getLogger(__name__)


class AlzKBOntologyPopulator:
    """
    Unified ontology populator for AlzKB using ista.
    
    This class provides methods to populate the AlzKB ontology from various
    data sources using ista's FlatFileDatabaseParser and MySQLDatabaseParser.
    """
    
    def __init__(self, ontology_path: str, data_dir: str, 
                 mysql_config: Optional[Dict[str, str]] = None):
        """
        Initialize the AlzKB ontology populator.
        
        Args:
            ontology_path: Path to the AlzKB ontology RDF file
            data_dir: Directory containing data files
            mysql_config: MySQL configuration for database sources (optional)
        """
        self.ontology_path = Path(ontology_path)
        self.data_dir = Path(data_dir)
        self.mysql_config = mysql_config
        self.ontology = None
        
        # Validate paths
        if not self.ontology_path.exists():
            raise FileNotFoundError(f"Ontology file not found: {self.ontology_path}")
        if not self.data_dir.exists():
            logger.warning(f"Data directory not found: {self.data_dir}. Creating it.")
            self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load ontology
        self._load_ontology()
    
    def _load_ontology(self):
        """Load the AlzKB ontology using owlready2."""
        try:
            ontology_uri = f"file://{self.ontology_path.absolute()}"
            logger.info(f"Loading ontology from: {ontology_uri}")
            self.ontology = owlready2.get_ontology(ontology_uri).load()
            logger.info(f"Successfully loaded ontology: {self.ontology.base_iri}")
        except Exception as e:
            logger.error(f"Failed to load ontology: {e}")
            raise
    
    def get_parser(self, source_name: str, parser_type: str = "flat") -> Union[FlatFileDatabaseParser, MySQLDatabaseParser]:
        """
        Get or create a parser for a data source.
        
        Args:
            source_name: Name of the data source
            parser_type: Type of parser ("flat" for files, "mysql" for database)
        
        Returns:
            Parser instance (FlatFileDatabaseParser or MySQLDatabaseParser)
        """
        if parser_type == "flat":
            parser = FlatFileDatabaseParser(source_name, self.ontology, str(self.data_dir))
        elif parser_type == "mysql":
            if not self.mysql_config:
                raise ValueError(f"MySQL config required for parser type 'mysql'")
            parser = MySQLDatabaseParser(source_name, self.ontology, self.mysql_config)
        else:
            raise ValueError(f"Unknown parser type: {parser_type}")
        
        logger.info(f"Created {parser_type} parser for source: {source_name}")
        return parser
    
    def populate_nodes(self, 
                      source_name: str,
                      node_type: str,
                      source_filename: Optional[str] = None,
                      source_table: Optional[str] = None,
                      fmt: str = "tsv",
                      parse_config: Dict[str, Any] = None,
                      merge: bool = False,
                      skip: bool = False,
                      parser_type: str = "flat") -> bool:
        """
        Populate nodes in the ontology from a data source.
        
        Args:
            source_name: Name of the data source
            node_type: Type of nodes to create (e.g., "Gene", "Drug", "Disease")
            source_filename: Filename for flat file sources
            source_table: Table name for database sources
            fmt: File format ("tsv", "csv", "tsv-pandas", etc.)
            parse_config: Configuration dict for parsing
            merge: Whether to merge with existing nodes
            skip: Whether to skip this source
            parser_type: Type of parser ("flat" or "mysql")
        
        Returns:
            True if successful, False otherwise
        """
        if skip:
            logger.info(f"Skipping node population for {source_name}.{node_type}")
            return True
        
        try:
            parser = self.get_parser(source_name, parser_type)
            
            if parser_type == "flat":
                parser.parse_node_type(
                    node_type=node_type,
                    source_filename=source_filename,
                    fmt=fmt,
                    parse_config=parse_config,
                    merge=merge,
                    skip=skip
                )
            else:  # mysql
                if not source_table:
                    raise ValueError("source_table required for MySQL parser")
                parser.parse_node_type(
                    node_type=node_type,
                    source_table=source_table,
                    parse_config=parse_config,
                    merge=merge,
                    skip=skip
                )
            
            logger.info(f"Successfully populated nodes: {source_name}.{node_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to populate nodes for {source_name}.{node_type}: {e}")
            return False
    
    def populate_relationships(self,
                             source_name: str,
                             relationship_type: type,
                             source_filename: Optional[str] = None,
                             source_table: Optional[str] = None,
                             fmt: str = "tsv",
                             parse_config: Dict[str, Any] = None,
                             inverse_relationship_type: Optional[type] = None,
                             merge: bool = False,
                             skip: bool = False,
                             parser_type: str = "flat") -> bool:
        """
        Populate relationships in the ontology from a data source.
        
        Args:
            source_name: Name of the data source
            relationship_type: Type of relationship (ontology property)
            inverse_relationship_type: Inverse relationship type (ontology property, optional)
            source_filename: Filename for flat file sources
            source_table: Table name for database sources
            fmt: File format ("tsv", "csv", "sif", etc.)
            parse_config: Configuration dict for parsing
            
            merge: Whether to merge with existing relationships
            skip: Whether to skip this source
            parser_type: Type of parser ("flat" or "mysql")
        
        Returns:
            True if successful, False otherwise
        """
        if skip:
            logger.info(f"Skipping relationship population for {source_name}.{relationship_type}")
            return True
        
        try:
            parser = self.get_parser(source_name, parser_type)
            
            if parser_type == "flat":
                parser.parse_relationship_type(
                    relationship_type=relationship_type,
                    source_filename=source_filename,
                    fmt=fmt,
                    parse_config=parse_config,
                    inverse_relationship_type=inverse_relationship_type,
                    merge=merge,
                    skip=skip
                )
            else:  # mysql
                if not source_table:
                    raise ValueError("source_table required for MySQL parser")
                parser.parse_relationship_type(
                    relationship_type=relationship_type,
                    source_table=source_table,
                    parse_config=parse_config,
                    inverse_relationship_type=inverse_relationship_type,
                    merge=merge,
                    skip=skip
                )
            
            logger.info(f"Successfully populated relationships: {source_name}.{relationship_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to populate relationships for {source_name}.{relationship_type}: {e}")
            return False
    
    def save_ontology(self, output_path: Optional[str] = None) -> str:
        """
        Save the populated ontology to an RDF file.
        
        Args:
            output_path: Path to save the ontology. If None, overwrites the original.
        
        Returns:
            Path to the saved ontology file
        """
        if output_path is None:
            output_path = str(self.ontology_path)
        
        try:
            logger.info(f"Saving ontology to: {output_path}")
            self.ontology.save(file=output_path, format="rdfxml")
            logger.info(f"Successfully saved ontology to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to save ontology: {e}")
            raise
    
    def get_ontology_stats(self) -> Dict[str, int]:
        """
        Get statistics about the populated ontology.
        
        Returns:
            Dictionary with counts of classes, individuals, and properties
        """
        stats = {
            "classes": len(list(self.ontology.classes())),
            "individuals": len(list(self.ontology.individuals())),
            "object_properties": len(list(self.ontology.object_properties())),
            "data_properties": len(list(self.ontology.data_properties()))
        }
        return stats
    
    def print_stats(self):
        """Print ontology statistics."""
        stats = self.get_ontology_stats()
        logger.info("Ontology Statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")

    def _resolve_property(self, name: str) -> Optional[type]:
        """
        Resolve a string property name to an ontology object.

        Args:
            name: Property name as string (e.g., 'xrefMeSH', 'Gene', 'geneInPathway')

        Returns:
            The ontology object, or None if not found
        """
        if name is None:
            return None
        prop = getattr(self.ontology, name, None)
        if prop is None:
            logger.warning(f"Property '{name}' not found in ontology")
        return prop

    def _resolve_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve string property names in a config to ontology objects.

        Args:
            config: Configuration dict with string property names

        Returns:
            New config dict with resolved ontology references
        """
        import copy
        resolved = copy.deepcopy(config)
        parse_config = resolved.get('parse_config', {})

        # Resolve data_property_map values
        if 'data_property_map' in parse_config:
            resolved_map = {}
            for col, prop_name in parse_config['data_property_map'].items():
                resolved_map[col] = self._resolve_property(prop_name)
            parse_config['data_property_map'] = resolved_map

        # Resolve merge_column property
        if 'merge_column' in parse_config:
            merge = parse_config['merge_column']
            if 'data_property' in merge:
                merge['data_property'] = self._resolve_property(merge['data_property'])

        # Resolve relationship parse_config properties
        for key in ['subject_node_type', 'object_node_type',
                    'subject_match_property', 'object_match_property']:
            if key in parse_config:
                parse_config[key] = self._resolve_property(parse_config[key])

        # Resolve top-level relationship type properties
        if 'relationship_type' in resolved:
            resolved['relationship_type'] = self._resolve_property(resolved['relationship_type'])
        if 'inverse_relationship_type' in resolved:
            resolved['inverse_relationship_type'] = self._resolve_property(resolved['inverse_relationship_type'])

        return resolved

    def get_config(self, config_key: str) -> Optional[Dict[str, Any]]:
        """
        Get a single resolved config by key.

        Args:
            config_key: Key in format "{source_name}.{data_name}"

        Returns:
            Resolved config dict, or None if not found
        """
        if config_key not in ONTOLOGY_CONFIGS:
            return None

        return self._resolve_config(ONTOLOGY_CONFIGS[config_key])

    def populate_from_config(self, config_key: str,
                             fmt: str = "tsv",
                             parser_type: str = "flat") -> Tuple[Optional[bool], Optional[str]]:
        """
        Populate ontology using a config key from ontology_configs.
        Source filename is read from the config itself.

        Args:
            config_key: Key in format "{source_name}.{data_name}"
            fmt: File format ("tsv", "csv", etc.)
            parser_type: Parser type ("flat" or "mysql")

        Returns:
            Tuple of (success, data_type):
            - (None, None) if no config found
            - (True/False, 'node'/'relationship') based on result
        """
        config = self.get_config(config_key)

        if config is None:
            logger.warning(f"No config found for {config_key}")
            return (None, None)

        data_type = config.get('data_type')
        source_name = config_key.split('.')[0]
        source_filename = config.get('source_filename')

        if not source_filename:
            logger.error(f"No source_filename in config for {config_key}")
            return (False, None)

        if data_type == 'node':
            success = self.populate_nodes(
                source_name=source_name,
                node_type=config.get('node_type'),
                source_filename=source_filename,
                fmt=fmt,
                parse_config=config.get('parse_config'),
                merge=config.get('merge', False),
                skip=config.get('skip', False),
                parser_type=parser_type
            )
            return (success, 'node')
        elif data_type == 'relationship':
            success = self.populate_relationships(
                source_name=source_name,
                relationship_type=config.get('relationship_type'),
                source_filename=source_filename,
                fmt=fmt,
                parse_config=config.get('parse_config'),
                inverse_relationship_type=config.get('inverse_relationship_type'),
                merge=config.get('merge', False),
                skip=config.get('skip', False),
                parser_type=parser_type
            )
            return (success, 'relationship')
        else:
            logger.error(f"Unknown data_type '{data_type}' for {config_key}")
            return (False, None)

    def get_default_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get default ista configurations for AlzKB data sources.

        Configuration keys use `{source_name}.{data_name}` format to match
        parser output dictionaries. Each config entry has a `data_type` field
        to route to the appropriate ista method:
        - 'node': Use parse_node_type()
        - 'relationship': Use parse_relationship_type()

        Returns:
            Dictionary mapping config keys to their ista configurations
        """
        return {
            # =====================================================================
            # AOP-DB - Adverse Outcome Pathway Database
            # =====================================================================
            'aopdb.pathway': {
                'data_type': 'node',
                'node_type': 'Drug',
                'parse_config': {
                    'headers': True,
                    'iri_column_name': 'DTX_id',
                    "data_property_map": {
                        "ChemicalID": self.ontology.xrefMeSH,
                        "source_database": self.ontology.source_database,
                    },
                    "merge_column": {
                        "source_column_name": "DTX_id",
                        "data_property": self.ontology.xrefDTXSID
                    },
                },
                'merge': True,
                'skip': False,
            },
            'aopdb.pathway': {
                'data_type': 'node',
                'node_type': 'Pathway',
                'parse_config': {
                    'headers': True,
                    'iri_column_name': 'path_name',
                    "data_property_map": {
                        "path_id": self.ontology.pathwayId,
                        "path_name": self.ontology.pathwayName,
                        "ext_source": self.ontology.sourceDatabase,
                        "source_database": self.ontology.sourceDatabase,
                    },
                },
                'merge': False,
                'skip': False,
            },
            'aopdb.relationships': {
                'data_type': 'relationship',
                'relationship_type': 'geneInPathway',  # String name, not object
                'inverse_relationship_type': 'PathwayContainsGene',  # String name, not object
                'parse_config': {
                    'headers': True,
                    'subject_node_type': self.ontology.Gene,
                    'subject_column_name': 'entrez',
                    'subject_match_property': self.ontology.xrefNcbiGene,
                    'object_node_type': self.ontology.Pathway,
                    'object_column_name': 'path_name',
                    'object_match_property': self.ontology.pathwayName,
                },
                'merge': False,
                'skip': False,
            },

            # =====================================================================
            # DisGeNET - Gene-Disease Associations
            # =====================================================================
            'disgenet.disease_classifications': {
                'data_type': 'node',
                'node_type': 'Disease',
                'parse_config': {
                    'headers': True,
                    'iri_column_name': 'diseaseId',
                    'data_property_map': {
                        'diseaseId': self.ontology.xrefUmlsCUI,
                        'diseaseName': self.ontology.commonName,
                        'sourceDatabase': self.ontology.sourceDatabase,
                    },
                },
                'merge': False,
                'skip': False,
            },
            'disgenet.disease_mappings': {
                'data_type': 'node',
                'node_type': 'Disease',
                'parse_config': {
                    'headers': True,
                    'iri_column_name': 'diseaseId',
                    "filter_column": "DO",
                    "filter_value": "0",
                    "merge_column": {
                        "source_column_name": "diseaseId", # column name in the source data to merge on
                        "data_property": self.ontology.xrefUmlsCUI, # property name in the ontology to merge on
                        "sourceDatabase": self.ontology.sourceDatabase,
                    },
                    "data_property_map": {
                        "DO": self.ontology.xrefDiseaseOntology
                    }
                },
                'merge': True,
                'skip': False,
            },
            'disgenet.gene_disease_associations': {
                'data_type': 'relationship',
                'relationship_type': 'geneAssociatesWithDisease',  # String name, not object
                'parse_config': {
                    'subject_node_type': self.ontology.Gene,
                    'subject_column_name': 'geneSymbol',
                    'subject_match_property': self.ontology.geneSymbol,
                    'object_node_type': self.ontology.Disease,
                    'object_column_name': 'diseaseId',
                    'object_match_property': self.ontology.xrefUmlsCUI,
                    'filter_column': 'diseaseType',
                    'filter_value': 'disease',
                    'headers': True,
                },
                'merge': False,
                'skip': False,
            },

            # =====================================================================
            # DrugBank - Drug Information
            # =====================================================================
            'drugbank.drugs': {
                'data_type': 'node',
                'node_type': 'Drug',
                'parse_config': {
                    'iri_column_name': 'drugbank_id',
                    'headers': True,
                    'data_property_map': {
                        'DrugBank ID': self.ontology.xrefDrugbank,
                        'cas_number': self.ontology.xrefCasRN,
                        'drug_name': self.ontology.commonName,
                        'source_database': self.ontology.sourceDatabase,
                    },
                    'merge_column': {
                        'source_column_name': 'cas_number',
                        'data_property': self.ontology.xrefCasRN,
                    },
                },
                'merge': False,
                'skip': False,
            },

            # =====================================================================
            # NCBI Gene - Gene Information
            # =====================================================================
            'ncbigene.genes': {
                'data_type': 'node',
                'node_type': 'Gene',
                'parse_config': {
                    'compound_fields': {
                        "dbXrefs": {"delimiter": "|", "field_split_prefix": ":"}
                    },
                    'iri_column_name': 'Symbol',
                    'headers': True,
                    "data_property_map": {
                        'GeneID': self.ontology.xrefNcbiGene,
                        'Symbol': self.ontology.geneSymbol,
                        'type_of_gene': self.ontology.typeOfGene,
                        'Full_name_from_nomenclature_authority': self.ontology.commonName,
                        'xref_MIM': self.ontology.xrefOMIM,
                        'xref_HGNC': self.ontology.xrefHGNC,
                        'xref_Ensembl': self.ontology.xrefEnsembl,
                        'chromosome': self.ontology.chromosome,
                        "source_database": self.ontology.sourceDatabase,
                    },
                },
                'merge': False,
                'skip': False,
            },

            # =====================================================================
            # DoRothEA - Transcription Factor Regulatory Network
            # =====================================================================
            'dorothea.transcription_factor_nodes': {
                'data_type': 'node',
                'node_type': 'TranscriptionFactor',
                'parse_config': {
                    'headers': True,
                    'iri_column_name': 'tf_symbol',
                    "data_property_map": {
                        "tf_symbol": self.ontology.TF,
                        "source_database": self.ontology.sourceDatabase,
                    }
                },
                'merge': True,
                'skip': False,
            },
            'dorothea.tf_gene_interactions': {
                'data_type': 'relationship',
                'relationship_type': 'transcriptionFactorInteractsWithGene',  # String name, not object
                'parse_config': {
                    'subject_node_type': self.ontology.TranscriptionFactor,
                    'subject_column_name': 'tf_symbol',
                    'subject_match_property': self.ontology.TF,
                    'object_node_type': self.ontology.Gene,
                    'object_column_name': 'target_gene',
                    'object_match_property': self.ontology.geneSymbol,
                    'headers': True,
                },
                'merge': False,
                'skip': False,
            },
            
            # # =====================================================================
            # # Disease Ontology - Disease Nodes
            # # =====================================================================
            # 'disease_ontology.disease_nodes': {
            #     'data_type': 'node',
            #     'class_name': 'Disease',
            #     'base_uri': 'http://alzkb.org/resource/doid/',
            #     'iri_column_name': 'doid',
            #     'label_columns': ['name'],
            #     'data_property_columns': ['definition', 'xrefs'],
            # },
            # 'disease_ontology.disease_anatomy': {
            #     'data_type': 'relationship',
            #     'relationship_type': 'diseaseLocalizesToAnatomy',
            #     'subject_node_type': 'Disease',
            #     'subject_column': 'disease_id',
            #     'subject_match_property': 'diseaseOntologyId',
            #     'object_node_type': 'BodyPart',
            #     'object_column': 'anatomy_id',
            #     'object_match_property': 'uberonId',
            # },

            # # =====================================================================
            # # Gene Ontology - GO Terms and Gene Associations
            # # =====================================================================
            # 'gene_ontology.biological_process_nodes': {
            #     'data_type': 'node',
            #     'class_name': 'BiologicalProcess',
            #     'base_uri': 'http://alzkb.org/resource/go/bp/',
            #     'iri_column_name': 'go_id',
            #     'label_columns': ['name'],
            #     'data_property_columns': ['definition'],
            # },
            # 'gene_ontology.molecular_function_nodes': {
            #     'data_type': 'node',
            #     'class_name': 'MolecularFunction',
            #     'base_uri': 'http://alzkb.org/resource/go/mf/',
            #     'iri_column_name': 'go_id',
            #     'label_columns': ['name'],
            #     'data_property_columns': ['definition'],
            # },
            # 'gene_ontology.cellular_component_nodes': {
            #     'data_type': 'node',
            #     'class_name': 'CellularComponent',
            #     'base_uri': 'http://alzkb.org/resource/go/cc/',
            #     'iri_column_name': 'go_id',
            #     'label_columns': ['name'],
            #     'data_property_columns': ['definition'],
            # },
            # 'gene_ontology.gene_bp_associations': {
            #     'data_type': 'relationship',
            #     'relationship_type': 'geneParticipatesInBiologicalProcess',
            #     'subject_node_type': 'Gene',
            #     'subject_column': 'gene_id',
            #     'subject_match_property': 'xrefNcbiGene',
            #     'object_node_type': 'BiologicalProcess',
            #     'object_column': 'go_id',
            #     'object_match_property': 'geneOntologyId',
            #     'data_property_columns': ['evidence_code', 'qualifier'],
            # },
            # 'gene_ontology.gene_mf_associations': {
            #     'data_type': 'relationship',
            #     'relationship_type': 'geneHasMolecularFunction',
            #     'subject_node_type': 'Gene',
            #     'subject_column': 'gene_id',
            #     'subject_match_property': 'xrefNcbiGene',
            #     'object_node_type': 'MolecularFunction',
            #     'object_column': 'go_id',
            #     'object_match_property': 'geneOntologyId',
            #     'data_property_columns': ['evidence_code', 'qualifier'],
            # },
            # 'gene_ontology.gene_cc_associations': {
            #     'data_type': 'relationship',
            #     'relationship_type': 'geneAssociatedWithCellularComponent',
            #     'subject_node_type': 'Gene',
            #     'subject_column': 'gene_id',
            #     'subject_match_property': 'xrefNcbiGene',
            #     'object_node_type': 'CellularComponent',
            #     'object_column': 'go_id',
            #     'object_match_property': 'geneOntologyId',
            #     'data_property_columns': ['evidence_code', 'qualifier'],
            # },

            # # =====================================================================
            # # Uberon - Anatomy/BodyPart Nodes
            # # =====================================================================
            # 'uberon.anatomy_nodes': {
            #     'data_type': 'node',
            #     'class_name': 'BodyPart',
            #     'base_uri': 'http://alzkb.org/resource/uberon/',
            #     'iri_column_name': 'uberon_id',
            #     'label_columns': ['name'],
            #     'data_property_columns': ['definition'],
            # },

            # # =====================================================================
            # # MeSH - Symptom Nodes
            # # =====================================================================
            # 'mesh.symptom_nodes': {
            #     'data_type': 'node',
            #     'class_name': 'Symptom',
            #     'base_uri': 'http://alzkb.org/resource/mesh/symptom/',
            #     'iri_column_name': 'mesh_id',
            #     'label_columns': ['name'],
            #     'data_property_columns': ['tree_numbers'],
            # },
            # 'mesh.disease_symptom': {
            #     'data_type': 'relationship',
            #     'relationship_type': 'symptomManifestationOfDisease',
            #     'subject_node_type': 'Symptom',
            #     'subject_column': 'symptom_id',
            #     'subject_match_property': 'meshId',
            #     'object_node_type': 'Disease',
            #     'object_column': 'disease_id',
            #     'object_match_property': 'diseaseOntologyId',
            # },

            # # =====================================================================
            # # GWAS Catalog - Gene-Disease Associations
            # # =====================================================================
            # 'gwas.gene_disease_associations': {
            #     'data_type': 'relationship',
            #     'relationship_type': 'geneAssociatesWithDisease',
            #     'subject_node_type': 'Gene',
            #     'subject_column': 'gene_symbol',
            #     'subject_match_property': 'geneSymbol',
            #     'object_node_type': 'Disease',
            #     'object_column': 'disease_id',
            #     'object_match_property': 'diseaseOntologyId',
            #     'data_property_columns': ['p_value', 'odds_ratio', 'pubmed_id', 'study_accession'],
            # },

            # # =====================================================================
            # # DrugCentral - Drug-Disease Relationships
            # # =====================================================================
            # 'drugcentral.drug_treats_disease': {
            #     'data_type': 'relationship',
            #     'relationship_type': 'drugTreatsDisease',
            #     'subject_node_type': 'Drug',
            #     'subject_column': 'drug_id',
            #     'subject_match_property': 'drugbankId',
            #     'object_node_type': 'Disease',
            #     'object_column': 'disease_id',
            #     'object_match_property': 'diseaseOntologyId',
            #     'data_property_columns': ['indication_type'],
            # },
            # 'drugcentral.drug_palliates_disease': {
            #     'data_type': 'relationship',
            #     'relationship_type': 'drugPalliatesDisease',
            #     'subject_node_type': 'Drug',
            #     'subject_column': 'drug_id',
            #     'subject_match_property': 'drugbankId',
            #     'object_node_type': 'Disease',
            #     'object_column': 'disease_id',
            #     'object_match_property': 'diseaseOntologyId',
            #     'data_property_columns': ['indication_type'],
            # },

            # # =====================================================================
            # # BindingDB - Drug-Gene Binding
            # # =====================================================================
            # 'bindingdb.drug_binds_gene': {
            #     'data_type': 'relationship',
            #     'relationship_type': 'chemicalBindsGene',
            #     'subject_node_type': 'Drug',
            #     'subject_column': 'drug_id',
            #     'subject_match_property': 'drugbankId',
            #     'object_node_type': 'Gene',
            #     'object_column': 'gene_symbol',
            #     'object_match_property': 'geneSymbol',
            #     'data_property_columns': ['affinity_nm', 'affinity_type', 'uniprot_id'],
            # },

            # # =====================================================================
            # # Bgee - Gene Expression in Anatomy
            # # =====================================================================
            # 'bgee.bodypart_overexpresses_gene': {
            #     'data_type': 'relationship',
            #     'relationship_type': 'bodyPartOverexpressesGene',
            #     'subject_node_type': 'BodyPart',
            #     'subject_column': 'anatomy_id',
            #     'subject_match_property': 'uberonId',
            #     'object_node_type': 'Gene',
            #     'object_column': 'gene_id',
            #     'object_match_property': 'xrefNcbiGene',
            #     'data_property_columns': ['expression_level', 'call_quality'],
            # },
            # 'bgee.bodypart_underexpresses_gene': {
            #     'data_type': 'relationship',
            #     'relationship_type': 'bodyPartUnderexpressesGene',
            #     'subject_node_type': 'BodyPart',
            #     'subject_column': 'anatomy_id',
            #     'subject_match_property': 'uberonId',
            #     'object_node_type': 'Gene',
            #     'object_column': 'gene_id',
            #     'object_match_property': 'xrefNcbiGene',
            #     'data_property_columns': ['expression_level', 'call_quality'],
            # },

            # # =====================================================================
            # # CTD - Chemical-Gene Expression Interactions
            # # =====================================================================
            # 'ctd.chemical_increases_expression': {
            #     'data_type': 'relationship',
            #     'relationship_type': 'chemicalIncreasesExpression',
            #     'subject_node_type': 'Drug',
            #     'subject_column': 'chemical_id',
            #     'subject_match_property': 'drugbankId',
            #     'object_node_type': 'Gene',
            #     'object_column': 'gene_id',
            #     'object_match_property': 'xrefNcbiGene',
            #     'data_property_columns': ['pubmed_ids', 'organism'],
            # },
            # 'ctd.chemical_decreases_expression': {
            #     'data_type': 'relationship',
            #     'relationship_type': 'chemicalDecreasesExpression',
            #     'subject_node_type': 'Drug',
            #     'subject_column': 'chemical_id',
            #     'subject_match_property': 'drugbankId',
            #     'object_node_type': 'Gene',
            #     'object_column': 'gene_id',
            #     'object_match_property': 'xrefNcbiGene',
            #     'data_property_columns': ['pubmed_ids', 'organism'],
            # },

            # # =====================================================================
            # # Hetionet Precomputed - Gene-Gene Relationships
            # # =====================================================================
            # 'hetionet_precomputed.gene_interacts': {
            #     'data_type': 'relationship',
            #     'relationship_type': 'geneInteractsWithGene',
            #     'subject_node_type': 'Gene',
            #     'subject_column': 'source_gene',
            #     'subject_match_property': 'xrefNcbiGene',
            #     'object_node_type': 'Gene',
            #     'object_column': 'target_gene',
            #     'object_match_property': 'xrefNcbiGene',
            # },
            # 'hetionet_precomputed.gene_covaries': {
            #     'data_type': 'relationship',
            #     'relationship_type': 'geneCovariesWithGene',
            #     'subject_node_type': 'Gene',
            #     'subject_column': 'source_gene',
            #     'subject_match_property': 'xrefNcbiGene',
            #     'object_node_type': 'Gene',
            #     'object_column': 'target_gene',
            #     'object_match_property': 'xrefNcbiGene',
            # },
            # 'hetionet_precomputed.gene_regulates': {
            #     'data_type': 'relationship',
            #     'relationship_type': 'geneRegulatesGene',
            #     'subject_node_type': 'Gene',
            #     'subject_column': 'source_gene',
            #     'subject_match_property': 'xrefNcbiGene',
            #     'object_node_type': 'Gene',
            #     'object_column': 'target_gene',
            #     'object_match_property': 'xrefNcbiGene',
            # },

            # # =====================================================================
            # # PubTator/MEDLINE - Literature Co-occurrence
            # # =====================================================================
            # 'pubtator.disease_disease_cooccurrence': {
            #     'data_type': 'relationship',
            #     'relationship_type': 'diseaseAssociatesWithDisease',
            #     'subject_node_type': 'Disease',
            #     'subject_column': 'disease1_id',
            #     'subject_match_property': 'diseaseOntologyId',
            #     'object_node_type': 'Disease',
            #     'object_column': 'disease2_id',
            #     'object_match_property': 'diseaseOntologyId',
            #     'data_property_columns': ['pmid_count', 'cooccurrence_score'],
            # },
            # 'pubtator.gene_disease_literature': {
            #     'data_type': 'relationship',
            #     'relationship_type': 'geneAssociatesWithDisease',
            #     'subject_node_type': 'Gene',
            #     'subject_column': 'gene_id',
            #     'subject_match_property': 'xrefNcbiGene',
            #     'object_node_type': 'Disease',
            #     'object_column': 'disease_id',
            #     'object_match_property': 'diseaseOntologyId',
            #     'data_property_columns': ['pmid_count'],
            # },
        }
