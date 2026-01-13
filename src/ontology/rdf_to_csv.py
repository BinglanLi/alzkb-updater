"""
RDF to CSV Converter for Memgraph

This module converts RDF ontology files to CSV format suitable for Memgraph import.
It extracts nodes and edges from the RDF graph and exports them as CSV files.
"""

import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import pandas as pd
import rdflib
from rdflib import Graph, Namespace, RDF, RDFS, OWL
from collections import defaultdict

logger = logging.getLogger(__name__)


class RDFToCSVConverter:
    """
    Converts RDF ontology to CSV files for Memgraph import.
    
    This converter extracts nodes (individuals) and edges (relationships)
    from an RDF graph and exports them in Memgraph-compatible CSV format.
    """
    
    def __init__(self, rdf_path: str, output_dir: str, ontology_namespace: str = None):
        """
        Initialize the RDF to CSV converter.
        
        Args:
            rdf_path: Path to the RDF file
            output_dir: Directory to save CSV files
            ontology_namespace: Namespace of the ontology (optional)
        """
        self.rdf_path = Path(rdf_path)
        self.output_dir = Path(output_dir)
        self.ontology_namespace = ontology_namespace
        self.graph = Graph()
        self.nodes = []
        self.edges = []
        
        if not self.rdf_path.exists():
            raise FileNotFoundError(f"RDF file not found: {self.rdf_path}")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_rdf(self) -> bool:
        """
        Load the RDF file into an rdflib graph.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Loading RDF file: {self.rdf_path}")
            self.graph.parse(str(self.rdf_path), format="xml")
            logger.info(f"Successfully loaded RDF with {len(self.graph)} triples")
            return True
        except Exception as e:
            logger.error(f"Failed to load RDF file: {e}")
            return False
    
    def extract_nodes(self) -> List[Dict[str, Any]]:
        """
        Extract all nodes (individuals) from the RDF graph.
        
        Returns:
            List of node dictionaries
        """
        logger.info("Extracting nodes from RDF graph...")
        nodes = []
        node_ids = set()
        
        # Query for all individuals (instances of classes)
        for s, p, o in self.graph.triples((None, RDF.type, None)):
            # Skip if object is a class definition
            if o in [OWL.Class, RDFS.Class]:
                continue
            
            # Extract node ID
            node_id = str(s).split('#')[-1] if '#' in str(s) else str(s).split('/')[-1]
            
            if node_id in node_ids:
                continue
            node_ids.add(node_id)
            
            # Extract node type (class)
            node_type = str(o).split('#')[-1] if '#' in str(o) else str(o).split('/')[-1]
            
            # Extract properties
            properties = self._extract_node_properties(s)
            
            node = {
                'id': node_id,
                'type': node_type,
                'uri': str(s),
                **properties
            }
            nodes.append(node)
        
        self.nodes = nodes
        logger.info(f"Extracted {len(nodes)} nodes")
        return nodes
    
    def _extract_node_properties(self, subject) -> Dict[str, Any]:
        """
        Extract all properties for a given subject.
        
        Args:
            subject: RDF subject node
        
        Returns:
            Dictionary of properties
        """
        properties = {}
        
        for p, o in self.graph.predicate_objects(subject):
            # Skip RDF type
            if p == RDF.type:
                continue
            
            # Extract property name
            prop_name = str(p).split('#')[-1] if '#' in str(p) else str(p).split('/')[-1]
            
            # Extract property value
            if isinstance(o, rdflib.Literal):
                prop_value = str(o)
            else:
                prop_value = str(o).split('#')[-1] if '#' in str(o) else str(o).split('/')[-1]
            
            # Handle multiple values for same property
            if prop_name in properties:
                if isinstance(properties[prop_name], list):
                    properties[prop_name].append(prop_value)
                else:
                    properties[prop_name] = [properties[prop_name], prop_value]
            else:
                properties[prop_name] = prop_value
        
        return properties
    
    def extract_edges(self) -> List[Dict[str, Any]]:
        """
        Extract all edges (relationships) from the RDF graph.
        
        Returns:
            List of edge dictionaries
        """
        logger.info("Extracting edges from RDF graph...")
        edges = []
        edge_set = set()
        
        # Query for all object properties (relationships between individuals)
        for s, p, o in self.graph.triples((None, None, None)):
            # Skip if predicate is RDF/RDFS/OWL property
            if p in [RDF.type, RDFS.label, RDFS.comment, OWL.sameAs]:
                continue
            
            # Skip if object is a literal (data property, not object property)
            if isinstance(o, rdflib.Literal):
                continue
            
            # Extract source and target IDs
            source_id = str(s).split('#')[-1] if '#' in str(s) else str(s).split('/')[-1]
            target_id = str(o).split('#')[-1] if '#' in str(o) else str(o).split('/')[-1]
            
            # Extract relationship type
            rel_type = str(p).split('#')[-1] if '#' in str(p) else str(p).split('/')[-1]
            
            # Create edge tuple for deduplication
            edge_tuple = (source_id, rel_type, target_id)
            if edge_tuple in edge_set:
                continue
            edge_set.add(edge_tuple)
            
            edge = {
                'source': source_id,
                'target': target_id,
                'type': rel_type,
                'source_uri': str(s),
                'target_uri': str(o),
                'predicate_uri': str(p)
            }
            edges.append(edge)
        
        self.edges = edges
        logger.info(f"Extracted {len(edges)} edges")
        return edges
    
    def export_to_csv(self, nodes_filename: str = "nodes.csv", 
                     edges_filename: str = "edges.csv") -> Tuple[str, str]:
        """
        Export nodes and edges to CSV files.
        
        Args:
            nodes_filename: Filename for nodes CSV
            edges_filename: Filename for edges CSV
        
        Returns:
            Tuple of (nodes_path, edges_path)
        """
        # Export nodes
        nodes_path = self.output_dir / nodes_filename
        if self.nodes:
            # Convert list properties to strings
            for node in self.nodes:
                for key, value in node.items():
                    if isinstance(value, list):
                        node[key] = '|'.join(str(v) for v in value)
            
            nodes_df = pd.DataFrame(self.nodes)
            nodes_df.to_csv(nodes_path, index=False)
            logger.info(f"Exported {len(self.nodes)} nodes to: {nodes_path}")
        else:
            logger.warning("No nodes to export")
        
        # Export edges
        edges_path = self.output_dir / edges_filename
        if self.edges:
            edges_df = pd.DataFrame(self.edges)
            edges_df.to_csv(edges_path, index=False)
            logger.info(f"Exported {len(self.edges)} edges to: {edges_path}")
        else:
            logger.warning("No edges to export")
        
        return str(nodes_path), str(edges_path)
    
    def convert(self, nodes_filename: str = "nodes.csv",
               edges_filename: str = "edges.csv") -> Tuple[str, str]:
        """
        Full conversion pipeline: load RDF, extract nodes/edges, export to CSV.
        
        Args:
            nodes_filename: Filename for nodes CSV
            edges_filename: Filename for edges CSV
        
        Returns:
            Tuple of (nodes_path, edges_path)
        """
        if not self.load_rdf():
            raise RuntimeError("Failed to load RDF file")
        
        self.extract_nodes()
        self.extract_edges()
        
        return self.export_to_csv(nodes_filename, edges_filename)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the converted data.
        
        Returns:
            Dictionary with statistics
        """
        node_types = defaultdict(int)
        edge_types = defaultdict(int)
        
        for node in self.nodes:
            node_types[node['type']] += 1
        
        for edge in self.edges:
            edge_types[edge['type']] += 1
        
        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'node_types': dict(node_types),
            'edge_types': dict(edge_types)
        }
    
    def print_statistics(self):
        """Print conversion statistics."""
        stats = self.get_statistics()
        logger.info("Conversion Statistics:")
        logger.info(f"  Total Nodes: {stats['total_nodes']}")
        logger.info(f"  Total Edges: {stats['total_edges']}")
        logger.info(f"  Node Types: {len(stats['node_types'])}")
        logger.info(f"  Edge Types: {len(stats['edge_types'])}")
        
        if stats['node_types']:
            logger.info("  Node Type Distribution:")
            for node_type, count in sorted(stats['node_types'].items(), key=lambda x: x[1], reverse=True)[:10]:
                logger.info(f"    {node_type}: {count}")
        
        if stats['edge_types']:
            logger.info("  Edge Type Distribution:")
            for edge_type, count in sorted(stats['edge_types'].items(), key=lambda x: x[1], reverse=True)[:10]:
                logger.info(f"    {edge_type}: {count}")
