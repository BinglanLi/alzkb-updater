"""
ista Integration Module for AlzKB

This module provides integration with ista (Instance Store for Tabular Annotations)
to populate the AlzKB ontology from parsed data sources.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd

logger = logging.getLogger(__name__)


class IstaIntegrator:
    """
    Handles integration with ista for ontology population.
    
    ista is used to convert tabular data (TSV files) into RDF format
    that populates the AlzKB ontology.
    """
    
    def __init__(self, ontology_path: str, output_dir: str, venv_path: Optional[str] = None):
        """
        Initialize the ista integrator.
        
        Args:
            ontology_path: Path to the base ontology RDF file
            output_dir: Directory for output RDF files
            venv_path: Path to virtual environment (if ista is installed in venv)
        """
        self.ontology_path = Path(ontology_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find csv2rdf executable
        if venv_path:
            self.csv2rdf_cmd = str(Path(venv_path) / "bin" / "csv2rdf")
        else:
            # Try to find in PATH
            import shutil
            csv2rdf = shutil.which("csv2rdf")
            if csv2rdf:
                self.csv2rdf_cmd = csv2rdf
            else:
                raise RuntimeError("csv2rdf not found. Please install ista.")
        
        logger.info(f"Using csv2rdf at: {self.csv2rdf_cmd}")
        
        # Verify ontology exists
        if not self.ontology_path.exists():
            raise FileNotFoundError(f"Ontology file not found: {self.ontology_path}")
    
    def create_config_for_source(self, 
                                 source_name: str,
                                 tsv_file: str,
                                 config: Dict[str, Any]) -> str:
        """
        Create an ista configuration file for a data source.
        
        Args:
            source_name: Name of the data source
            tsv_file: Path to the TSV file
            config: Configuration dictionary with:
                - class_name: OWL class name for instances
                - identity_columns: List of columns that form the identity
                - label_columns: List of columns for labels
                - property_mappings: Dict mapping column names to property URIs
                - base_uri: Base URI for instances
        
        Returns:
            Path to the created configuration file
        """
        config_path = self.output_dir / f"{source_name}_ista_config.txt"
        
        with open(config_path, 'w') as f:
            # Write basic configuration
            f.write(f"# ista configuration for {source_name}\n")
            f.write(f"# Generated automatically\n\n")
            
            # Instance base URI
            base_uri = config.get('base_uri', f'http://alzkb.org/resource/{source_name}/')
            f.write(f"-b {base_uri}\n")
            
            # Property base URI
            prop_base = config.get('property_base', 'http://alzkb.org/property/')
            f.write(f"-p {prop_base}\n")
            
            # Class name
            if 'class_name' in config:
                f.write(f"-c {config['class_name']}\n")
            
            # Identity columns
            if 'identity_columns' in config:
                id_cols = ','.join(str(c) for c in config['identity_columns'])
                f.write(f"-i {id_cols}\n")
            
            # Label columns
            if 'label_columns' in config:
                label_cols = ','.join(str(c) for c in config['label_columns'])
                f.write(f"-l {label_cols}\n")
            
            # Property mappings
            if 'property_mappings' in config:
                for col, prop_uri in config['property_mappings'].items():
                    f.write(f"--col{col} {prop_uri}\n")
        
        logger.info(f"Created ista config: {config_path}")
        return str(config_path)
    
    def populate_from_tsv(self,
                         source_name: str,
                         tsv_file: str,
                         config: Dict[str, Any],
                         delimiter: str = '\t') -> str:
        """
        Populate ontology from a TSV file using ista.
        
        Args:
            source_name: Name of the data source
            tsv_file: Path to the TSV file
            config: Configuration for ista (see create_config_for_source)
            delimiter: Field delimiter (default: tab)
        
        Returns:
            Path to the output RDF file
        """
        tsv_path = Path(tsv_file)
        if not tsv_path.exists():
            raise FileNotFoundError(f"TSV file not found: {tsv_file}")
        
        output_rdf = self.output_dir / f"{source_name}_populated.rdf"
        
        logger.info(f"Populating ontology from {source_name}...")
        
        # Build csv2rdf command
        cmd = [
            self.csv2rdf_cmd,
            '-b', config.get('base_uri', f'http://alzkb.org/resource/{source_name}/'),
            '-p', config.get('property_base', 'http://alzkb.org/property/'),
            '-d', delimiter,
            '-o', str(output_rdf)
        ]
        
        # Add class name if specified
        if 'class_name' in config:
            cmd.extend(['-c', config['class_name']])
        
        # Add identity columns
        if 'identity_columns' in config:
            id_cols = ','.join(str(c) for c in config['identity_columns'])
            cmd.extend(['-i', id_cols])
        
        # Add label columns
        if 'label_columns' in config:
            label_cols = ','.join(str(c) for c in config['label_columns'])
            cmd.extend(['-l', label_cols])
        
        # Add skip lines if specified
        if 'skip_lines' in config:
            cmd.extend(['-s', str(config['skip_lines'])])
        
        # Add input file
        cmd.append(str(tsv_path))
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Run csv2rdf
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"✓ Successfully created RDF: {output_rdf}")
            if result.stdout:
                logger.debug(f"csv2rdf output: {result.stdout}")
            
            return str(output_rdf)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"csv2rdf failed: {e.stderr}")
            raise RuntimeError(f"Failed to populate ontology for {source_name}: {e}")
    
    def populate_from_sif(self,
                         source_name: str,
                         sif_file: str,
                         edge_config: Dict[str, Any]) -> str:
        """
        Populate ontology from a SIF (Simple Interaction Format) file.
        
        SIF format: node1 <tab> relationship <tab> node2
        
        Args:
            source_name: Name of the data source
            sif_file: Path to the SIF file
            edge_config: Configuration for edges with:
                - relationship_property: URI for the relationship property
                - source_base_uri: Base URI for source nodes
                - target_base_uri: Base URI for target nodes
        
        Returns:
            Path to the output RDF file
        """
        sif_path = Path(sif_file)
        if not sif_path.exists():
            raise FileNotFoundError(f"SIF file not found: {sif_file}")
        
        output_rdf = self.output_dir / f"{source_name}_edges.rdf"
        
        logger.info(f"Populating edges from {source_name} SIF file...")
        
        # Convert SIF to RDF manually (ista doesn't directly support SIF)
        # We'll create RDF triples directly
        from rdflib import Graph, Namespace, URIRef, Literal
        from rdflib.namespace import RDF, RDFS
        
        g = Graph()
        
        # Define namespaces
        alzkb_ns = Namespace(edge_config.get('source_base_uri', 'http://alzkb.org/resource/'))
        prop_ns = Namespace(edge_config.get('property_base', 'http://alzkb.org/property/'))
        
        # Read SIF file and create triples
        with open(sif_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('\t')
                if len(parts) >= 3:
                    source, relationship, target = parts[0], parts[1], parts[2]
                    
                    source_uri = URIRef(alzkb_ns[source])
                    target_uri = URIRef(alzkb_ns[target])
                    rel_prop = URIRef(prop_ns[relationship])
                    
                    g.add((source_uri, rel_prop, target_uri))
        
        # Serialize to RDF
        g.serialize(destination=str(output_rdf), format='xml')
        
        logger.info(f"✓ Successfully created RDF from SIF: {output_rdf}")
        return str(output_rdf)
    
    def merge_rdf_files(self, rdf_files: List[str], output_file: str) -> str:
        """
        Merge multiple RDF files into a single file.
        
        Args:
            rdf_files: List of RDF file paths to merge
            output_file: Path for the merged output file
        
        Returns:
            Path to the merged RDF file
        """
        from rdflib import Graph
        
        logger.info(f"Merging {len(rdf_files)} RDF files...")
        
        # Create a new graph
        merged_graph = Graph()
        
        # Load base ontology
        logger.info(f"Loading base ontology: {self.ontology_path}")
        merged_graph.parse(str(self.ontology_path), format='xml')
        
        # Merge all RDF files
        for rdf_file in rdf_files:
            if os.path.exists(rdf_file):
                logger.info(f"Merging: {rdf_file}")
                try:
                    merged_graph.parse(rdf_file, format='xml')
                except Exception as e:
                    logger.error(f"Failed to parse {rdf_file}: {e}")
        
        # Serialize merged graph
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        merged_graph.serialize(destination=str(output_path), format='xml')
        
        logger.info(f"✓ Created merged RDF: {output_path}")
        logger.info(f"Total triples: {len(merged_graph)}")
        
        return str(output_path)


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
