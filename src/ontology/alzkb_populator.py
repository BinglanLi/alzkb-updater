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
from typing import Dict, List, Optional, Any, Union
import owlready2

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
    
    def __init__(self, ontology_path: str, data_dir: str, mysql_config: Optional[Dict[str, str]] = None):
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
        self.parsers = {}
        
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
        if source_name in self.parsers:
            return self.parsers[source_name]
        
        if parser_type == "flat":
            parser = FlatFileDatabaseParser(source_name, self.ontology, str(self.data_dir))
        elif parser_type == "mysql":
            if not self.mysql_config:
                raise ValueError(f"MySQL config required for parser type 'mysql'")
            parser = MySQLDatabaseParser(source_name, self.ontology, self.mysql_config)
        else:
            raise ValueError(f"Unknown parser type: {parser_type}")
        
        self.parsers[source_name] = parser
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
                if not source_filename:
                    raise ValueError("source_filename required for flat file parser")
                parser.parse_node_type(
                    node_type=node_type,
                    source_filename=source_filename,
                    fmt=fmt,
                    parse_config=parse_config or {},
                    merge=merge,
                    skip=skip
                )
            else:  # mysql
                if not source_table:
                    raise ValueError("source_table required for MySQL parser")
                parser.parse_node_type(
                    node_type=node_type,
                    source_table=source_table,
                    parse_config=parse_config or {},
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
                             relationship_type: str,
                             source_filename: Optional[str] = None,
                             source_table: Optional[str] = None,
                             fmt: str = "tsv",
                             parse_config: Dict[str, Any] = None,
                             inverse_relationship_type: Optional[str] = None,
                             merge: bool = False,
                             skip: bool = False,
                             parser_type: str = "flat") -> bool:
        """
        Populate relationships in the ontology from a data source.
        
        Args:
            source_name: Name of the data source
            relationship_type: Type of relationship (ontology property)
            source_filename: Filename for flat file sources
            source_table: Table name for database sources
            fmt: File format ("tsv", "csv", "sif", etc.)
            parse_config: Configuration dict for parsing
            inverse_relationship_type: Inverse relationship type (optional)
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
            
            # Get the relationship type from ontology
            rel_type = getattr(self.ontology, relationship_type, None)
            if not rel_type:
                raise ValueError(f"Relationship type not found in ontology: {relationship_type}")
            
            inv_rel_type = None
            if inverse_relationship_type:
                inv_rel_type = getattr(self.ontology, inverse_relationship_type, None)
            
            if parser_type == "flat":
                if not source_filename:
                    raise ValueError("source_filename required for flat file parser")
                parser.parse_relationship_type(
                    relationship_type=rel_type,
                    source_filename=source_filename,
                    fmt=fmt,
                    parse_config=parse_config or {},
                    inverse_relationship_type=inv_rel_type,
                    merge=merge,
                    skip=skip
                )
            else:  # mysql
                if not source_table:
                    raise ValueError("source_table required for MySQL parser")
                parser.parse_relationship_type(
                    relationship_type=rel_type,
                    source_table=source_table,
                    parse_config=parse_config or {},
                    inverse_relationship_type=inv_rel_type,
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


def get_default_configs() -> Dict[str, Dict[str, Any]]:
    """
    Get default ista configurations for AlzKB data sources.

    Returns:
        Dictionary mapping source names to their ista configurations
    """
    return {
        'disgenet': {
            'class_name': 'GeneDisease Association',
            'base_uri': 'http://alzkb.org/resource/disgenet/',
            'property_base': 'http://alzkb.org/property/',
            'identity_columns': [0, 1],  # gene and disease
            'label_columns': [0],
            'property_mappings': {
                '0': 'hasGene',
                '1': 'hasDisease',
                '2': 'hasScore',
                '3': 'hasEvidence'
            }
        },
        'drugbank': {
            'class_name': 'Drug',
            'base_uri': 'http://alzkb.org/resource/drugbank/',
            'property_base': 'http://alzkb.org/property/',
            'identity_columns': [0],  # drugbank_id
            'label_columns': [1],  # name
            'property_mappings': {
                '0': 'drugbankId',
                '1': 'drugName',
                '2': 'drugType',
                '3': 'description'
            }
        },
        'aopdb': {
            'class_name': 'Pathway',
            'base_uri': 'http://alzkb.org/resource/aopdb/',
            'property_base': 'http://alzkb.org/property/',
            'identity_columns': [0],  # pathway_id
            'label_columns': [1],  # pathway_name
            'property_mappings': {
                '0': 'pathwayId',
                '1': 'pathwayName',
                '2': 'pathwayDescription'
            }
        },
        'ncbigene': {
            'class_name': 'Gene',
            'base_uri': 'http://alzkb.org/resource/gene/',
            'property_base': 'http://alzkb.org/property/',
            'identity_columns': [0],  # gene_id
            'label_columns': [1],  # symbol
            'property_mappings': {
                '0': 'geneId',
                '1': 'geneSymbol',
                '2': 'geneName',
                '3': 'organism'
            }
        },
        'hetionet': {
            'class_name': 'BioEntity',
            'base_uri': 'http://alzkb.org/resource/hetionet/',
            'property_base': 'http://alzkb.org/property/',
            'identity_columns': [0],  # entity_id
            'label_columns': [1],  # entity_name
        }
    }
