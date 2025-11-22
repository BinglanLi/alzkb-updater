"""
HetionetParser: Parser for Hetionet data.

Hetionet is a comprehensive biomedical knowledge graph that integrates
multiple data sources. It contains nodes (entities) and edges (relationships)
covering genes, diseases, compounds, and more.

Source: https://github.com/hetio/hetionet
"""

import logging
from typing import Dict, Optional
import pandas as pd
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class HetionetParser(BaseParser):
    """
    Parser for Hetionet knowledge graph data.
    
    Downloads and parses Hetionet nodes and edges files.
    """
    
    NODES_URL = "https://github.com/hetio/hetionet/raw/master/hetnet/tsv/hetionet-v1.0-nodes.tsv"
    EDGES_URL = "https://github.com/hetio/hetionet/raw/master/hetnet/tsv/hetionet-v1.0-edges.sif.gz"
    
    def download_data(self) -> bool:
        """
        Download Hetionet nodes and edges files.
        
        Returns:
            True if successful, False otherwise.
        """
        logger.info("Downloading Hetionet data...")
        
        # Download nodes file
        nodes_file = self.download_file(self.NODES_URL, "hetionet-v1.0-nodes.tsv")
        if not nodes_file:
            logger.error("Failed to download Hetionet nodes file")
            return False
        
        # Download edges file (gzipped)
        edges_gz = self.download_file(self.EDGES_URL, "hetionet-v1.0-edges.sif.gz")
        if not edges_gz:
            logger.error("Failed to download Hetionet edges file")
            return False
        
        # Extract edges file
        edges_file = self.extract_gzip(edges_gz)
        if not edges_file:
            logger.error("Failed to extract Hetionet edges file")
            return False
        
        logger.info("✓ Successfully downloaded Hetionet data")
        return True
    
    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse Hetionet data files.
        
        Returns:
            Dictionary with 'nodes' and 'edges' DataFrames.
        """
        logger.info("Parsing Hetionet data...")
        
        result = {}
        
        # Parse nodes
        nodes_file = self.get_file_path("hetionet-v1.0-nodes.tsv")
        nodes_df = self.read_tsv(nodes_file)
        
        if nodes_df is not None:
            # Validate required columns
            required_cols = ['id', 'name', 'kind']
            if self.validate_data(nodes_df, required_cols):
                result['nodes'] = nodes_df
                logger.info(f"✓ Parsed {len(nodes_df)} nodes")
                
                # Show node type distribution
                node_types = nodes_df['kind'].value_counts()
                logger.info(f"Node types: {dict(node_types)}")
        
        # Parse edges
        edges_file = self.get_file_path("hetionet-v1.0-edges.sif")
        edges_df = self.read_tsv(edges_file, header=None, 
                                 names=['source', 'metaedge', 'target'])
        
        if edges_df is not None:
            result['edges'] = edges_df
            logger.info(f"✓ Parsed {len(edges_df)} edges")
            
            # Show edge type distribution
            edge_types = edges_df['metaedge'].value_counts()
            logger.info(f"Edge types (top 10): {dict(edge_types.head(10))}")
        
        return result
    
    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for Hetionet data.
        
        Returns:
            Dictionary describing the schema for nodes and edges.
        """
        return {
            'nodes': {
                'id': 'Unique identifier for the node',
                'name': 'Human-readable name',
                'kind': 'Node type (e.g., Gene, Disease, Compound)'
            },
            'edges': {
                'source': 'Source node ID',
                'metaedge': 'Edge type/relationship',
                'target': 'Target node ID'
            }
        }
    
    def filter_alzheimer_related(self, nodes_df: pd.DataFrame, 
                                edges_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Filter Hetionet data for Alzheimer's-related entities.
        
        Args:
            nodes_df: DataFrame of all nodes
            edges_df: DataFrame of all edges
        
        Returns:
            Dictionary with filtered 'nodes' and 'edges' DataFrames
        """
        logger.info("Filtering for Alzheimer's-related data...")
        
        # Find Alzheimer's disease node
        disease_nodes = nodes_df[nodes_df['kind'] == 'Disease']
        alzheimer_nodes = disease_nodes[
            disease_nodes['name'].str.contains('Alzheimer', case=False, na=False)
        ]
        
        if len(alzheimer_nodes) == 0:
            logger.warning("No Alzheimer's disease nodes found")
            return {'nodes': pd.DataFrame(), 'edges': pd.DataFrame()}
        
        logger.info(f"Found {len(alzheimer_nodes)} Alzheimer's disease nodes:")
        for _, node in alzheimer_nodes.iterrows():
            logger.info(f"  - {node['name']} ({node['id']})")
        
        # Get all edges connected to Alzheimer's disease
        alzheimer_ids = set(alzheimer_nodes['id'])
        related_edges = edges_df[
            edges_df['source'].isin(alzheimer_ids) | 
            edges_df['target'].isin(alzheimer_ids)
        ]
        
        # Get all nodes connected to these edges
        related_node_ids = set(related_edges['source']) | set(related_edges['target'])
        related_nodes = nodes_df[nodes_df['id'].isin(related_node_ids)]
        
        logger.info(f"✓ Filtered to {len(related_nodes)} related nodes")
        logger.info(f"✓ Filtered to {len(related_edges)} related edges")
        
        return {
            'nodes': related_nodes,
            'edges': related_edges
        }
