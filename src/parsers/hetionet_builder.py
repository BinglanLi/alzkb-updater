"""
Hetionet Builder for AlzKB

This module builds Hetionet from scratch by fetching data from multiple sources
and populating the ontology using ista.

Hetionet is a heterogeneous network of biomedical knowledge that integrates:
- Disease Ontology
- Gene Ontology
- Uberon (anatomy)
- GWAS Catalog
- MeSH
- DrugCentral
- BindingDB
- Bgee (gene expression)
- MEDLINE co-occurrence

Reference: https://github.com/EpistasisLab/AlzKB-updates
"""

import os
import logging
import requests
import gzip
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse
import pandas as pd
from tqdm import tqdm

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


# Data sources for building Hetionet
DATA_SOURCES = {
    # Ontologies
    'disease_ontology': {
        'url': 'https://github.com/DiseaseOntology/HumanDiseaseOntology/raw/main/src/ontology/doid.obo',
        'format': 'obo',
        'description': 'Disease Ontology - human disease concepts',
        'required': True
    },
    'gene_ontology': {
        'url': 'http://current.geneontology.org/ontology/go-basic.obo',
        'format': 'obo',
        'description': 'Gene Ontology - gene functions',
        'required': True
    },
    'uberon': {
        'url': 'http://purl.obolibrary.org/obo/uberon.obo',
        'format': 'obo',
        'description': 'Uberon - anatomy ontology',
        'required': True
    },
    
    # Phenotype and Disease
    'gwas_catalog': {
        'url': 'https://www.ebi.ac.uk/gwas/api/search/downloads/full',
        'format': 'tsv',
        'description': 'GWAS Catalog - genome-wide association studies',
        'required': False
    },
    'mesh': {
        'url': 'https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2025.xml',
        'format': 'xml',
        'description': 'MeSH - medical subject headings',
        'required': False
    },
    
    # Drug and Chemical
    'drugcentral': {
        'url': 'https://unmtid-dbs.net/download/drugcentral.dump.01012025.sql.gz',
        'format': 'sql.gz',
        'description': 'DrugCentral - drug information',
        'required': False
    },
    'bindingdb': {
        'url': 'https://www.bindingdb.org/bind/downloads/BindingDB_All_2024m11.tsv.zip',
        'format': 'tsv.zip',
        'description': 'BindingDB - protein-ligand binding data',
        'required': False
    },
    
    # Gene Expression
    'bgee': {
        'url': 'https://www.bgee.org/ftp/current/download/calls/expr_calls/Homo_sapiens_expr_simple.tsv.gz',
        'format': 'tsv.gz',
        'description': 'Bgee - gene expression data',
        'required': False
    },
    
    # Literature co-occurrence
    'medline': {
        'url': None,  # Requires special handling
        'format': 'custom',
        'description': 'MEDLINE co-occurrence data',
        'required': False,
        'note': 'Requires PubMed API or pre-processed co-occurrence data'
    }
}


class HetionetBuilder(BaseParser):
    """
    Builds Hetionet from scratch using multiple data sources.
    
    This builder fetches data from various sources, processes it into
    the appropriate format, and uses ista to populate the AlzKB ontology.
    """
    
    def __init__(self, data_dir: str):
        """
        Initialize the Hetionet builder.
        
        Args:
            data_dir: Directory to store downloaded and processed data
        """
        super().__init__(data_dir)
        self.source_name = "hetionet"
        self.hetionet_dir = Path(data_dir) / "hetionet"
        self.hetionet_dir.mkdir(parents=True, exist_ok=True)
        
        # Track downloaded sources
        self.downloaded_sources = {}
        self.processed_data = {}
    
    def download_data(self) -> bool:
        """
        Download all Hetionet data sources.
        
        Returns:
            True if at least required sources were downloaded successfully
        """
        logger.info("Downloading Hetionet data sources...")
        success_count = 0
        required_count = 0
        
        for source_name, source_info in DATA_SOURCES.items():
            is_required = source_info.get('required', False)
            if is_required:
                required_count += 1
            
            logger.info(f"Downloading {source_name}: {source_info['description']}")
            
            if self._download_source(source_name, source_info):
                success_count += 1
                self.downloaded_sources[source_name] = True
            else:
                self.downloaded_sources[source_name] = False
                if is_required:
                    logger.error(f"Failed to download required source: {source_name}")
        
        logger.info(f"Downloaded {success_count}/{len(DATA_SOURCES)} sources")
        
        # Check if all required sources were downloaded
        required_success = sum(1 for name, info in DATA_SOURCES.items() 
                              if info.get('required', False) and self.downloaded_sources.get(name, False))
        
        if required_success < required_count:
            logger.error(f"Only {required_success}/{required_count} required sources downloaded")
            return False
        
        return True
    
    def _download_source(self, source_name: str, source_info: Dict[str, Any]) -> bool:
        """
        Download a single data source.
        
        Args:
            source_name: Name of the data source
            source_info: Information about the data source
        
        Returns:
            True if successful, False otherwise
        """
        url = source_info.get('url')
        if not url:
            logger.warning(f"No URL provided for {source_name}, skipping")
            return False
        
        # Determine output filename
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename:
            filename = f"{source_name}.{source_info['format']}"
        
        output_path = self.hetionet_dir / filename
        
        # Skip if already downloaded
        if output_path.exists():
            logger.info(f"  {source_name} already downloaded: {output_path}")
            return True
        
        try:
            logger.info(f"  Downloading from: {url}")
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            # Get file size for progress bar
            total_size = int(response.headers.get('content-length', 0))
            
            # Download with progress bar
            with open(output_path, 'wb') as f:
                if total_size > 0:
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc=source_name) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))
                else:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            logger.info(f"  Downloaded to: {output_path}")
            
            # Decompress if gzipped
            if filename.endswith('.gz') and not filename.endswith('.tar.gz'):
                self._decompress_gz(output_path)
            
            return True
            
        except Exception as e:
            logger.error(f"  Failed to download {source_name}: {e}")
            if output_path.exists():
                output_path.unlink()
            return False
    
    def _decompress_gz(self, gz_path: Path) -> Optional[Path]:
        """
        Decompress a gzipped file.
        
        Args:
            gz_path: Path to the gzipped file
        
        Returns:
            Path to the decompressed file, or None if failed
        """
        output_path = gz_path.with_suffix('')
        
        if output_path.exists():
            logger.info(f"  Decompressed file already exists: {output_path}")
            return output_path
        
        try:
            logger.info(f"  Decompressing: {gz_path}")
            with gzip.open(gz_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            logger.info(f"  Decompressed to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"  Failed to decompress {gz_path}: {e}")
            return None
    
    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse all downloaded Hetionet data sources.
        
        Returns:
            Dictionary of parsed DataFrames by source name
        """
        logger.info("Parsing Hetionet data sources...")
        
        parsed_data = {}
        
        for source_name, downloaded in self.downloaded_sources.items():
            if not downloaded:
                logger.warning(f"Skipping {source_name} (not downloaded)")
                continue
            
            logger.info(f"Parsing {source_name}...")
            
            try:
                if source_name == 'disease_ontology':
                    data = self._parse_disease_ontology()
                elif source_name == 'gene_ontology':
                    data = self._parse_gene_ontology()
                elif source_name == 'uberon':
                    data = self._parse_uberon()
                elif source_name == 'gwas_catalog':
                    data = self._parse_gwas_catalog()
                elif source_name == 'mesh':
                    data = self._parse_mesh()
                elif source_name == 'drugcentral':
                    data = self._parse_drugcentral()
                elif source_name == 'bindingdb':
                    data = self._parse_bindingdb()
                elif source_name == 'bgee':
                    data = self._parse_bgee()
                elif source_name == 'medline':
                    data = self._parse_medline_cooccurrence()
                else:
                    logger.warning(f"No parser implemented for {source_name}")
                    continue
                
                if data is not None:
                    parsed_data[source_name] = data
                    self.processed_data[source_name] = data
                    logger.info(f"  Successfully parsed {source_name}")
                else:
                    logger.warning(f"  No data parsed for {source_name}")
                    
            except Exception as e:
                logger.error(f"  Failed to parse {source_name}: {e}")
        
        logger.info(f"Successfully parsed {len(parsed_data)} sources")
        return parsed_data
    
    def _parse_disease_ontology(self) -> Optional[pd.DataFrame]:
        """Parse Disease Ontology OBO file."""
        logger.info("  Parsing Disease Ontology...")
        # Placeholder - implement OBO parsing
        logger.warning("  Disease Ontology parsing not yet implemented")
        return None
    
    def _parse_gene_ontology(self) -> Optional[pd.DataFrame]:
        """Parse Gene Ontology OBO file."""
        logger.info("  Parsing Gene Ontology...")
        # Placeholder - implement OBO parsing
        logger.warning("  Gene Ontology parsing not yet implemented")
        return None
    
    def _parse_uberon(self) -> Optional[pd.DataFrame]:
        """Parse Uberon OBO file."""
        logger.info("  Parsing Uberon...")
        # Placeholder - implement OBO parsing
        logger.warning("  Uberon parsing not yet implemented")
        return None
    
    def _parse_gwas_catalog(self) -> Optional[pd.DataFrame]:
        """Parse GWAS Catalog TSV file."""
        logger.info("  Parsing GWAS Catalog...")
        # Placeholder - implement GWAS parsing
        logger.warning("  GWAS Catalog parsing not yet implemented")
        return None
    
    def _parse_mesh(self) -> Optional[pd.DataFrame]:
        """Parse MeSH XML file."""
        logger.info("  Parsing MeSH...")
        # Placeholder - implement MeSH XML parsing
        logger.warning("  MeSH parsing not yet implemented")
        return None
    
    def _parse_drugcentral(self) -> Optional[pd.DataFrame]:
        """Parse DrugCentral SQL dump."""
        logger.info("  Parsing DrugCentral...")
        # Placeholder - implement DrugCentral SQL parsing
        logger.warning("  DrugCentral parsing not yet implemented")
        return None
    
    def _parse_bindingdb(self) -> Optional[pd.DataFrame]:
        """Parse BindingDB TSV file."""
        logger.info("  Parsing BindingDB...")
        # Placeholder - implement BindingDB parsing
        logger.warning("  BindingDB parsing not yet implemented")
        return None
    
    def _parse_bgee(self) -> Optional[pd.DataFrame]:
        """Parse Bgee gene expression data."""
        logger.info("  Parsing Bgee...")
        # Placeholder - implement Bgee parsing
        logger.warning("  Bgee parsing not yet implemented")
        return None
    
    def _parse_medline_cooccurrence(self) -> Optional[pd.DataFrame]:
        """Parse or generate MEDLINE co-occurrence data."""
        logger.info("  Parsing MEDLINE co-occurrence...")
        # Placeholder - implement MEDLINE co-occurrence
        logger.warning("  MEDLINE co-occurrence not yet implemented")
        return None
    
    def populate_ontology(self, populator, skip_sources: List[str] = None) -> bool:
        """
        Populate the ontology using ista with parsed Hetionet data.
        
        Args:
            populator: AlzKBOntologyPopulator instance
            skip_sources: List of source names to skip
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Populating ontology with Hetionet data using ista...")
        
        skip_sources = skip_sources or []
        success = True
        
        # This is a placeholder - actual implementation will populate
        # nodes and relationships for each data source using the populator
        
        logger.warning("Hetionet ontology population not yet fully implemented")
        return success
    
    def export_to_tsv(self, output_dir: str) -> List[str]:
        """
        Export parsed Hetionet data to TSV files for ista.
        
        Args:
            output_dir: Directory to save TSV files
        
        Returns:
            List of exported file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        exported_files = []
        
        for source_name, data in self.processed_data.items():
            if data is None or (isinstance(data, pd.DataFrame) and data.empty):
                continue
            
            output_file = output_dir / f"hetionet_{source_name}.tsv"
            
            try:
                if isinstance(data, pd.DataFrame):
                    data.to_csv(output_file, sep='\t', index=False)
                    exported_files.append(str(output_file))
                    logger.info(f"Exported {source_name} to: {output_file}")
            except Exception as e:
                logger.error(f"Failed to export {source_name}: {e}")
        
        return exported_files
    
    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for Hetionet data.
        
        Returns:
            Dictionary defining node and edge types
        """
        return {
            'nodes': {
                'Disease': 'Disease concepts from Disease Ontology',
                'Gene': 'Gene concepts from Gene Ontology',
                'BodyPart': 'Anatomy concepts from Uberon',
                'Drug': 'Drug concepts from DrugCentral',
                'BiologicalProcess': 'Biological process from Gene Ontology',
                'MolecularFunction': 'Molecular function from Gene Ontology',
                'CellularComponent': 'Cellular component from Gene Ontology',
                'Symptom': 'Symptoms from MeSH',
                'DrugClass': 'Drug classes'
            },
            'edges': {
                'geneAssociatesWithDisease': 'Gene-disease associations from GWAS',
                'drugTreatsDisease': 'Drug-disease treatments',
                'drugBindsGene': 'Drug-gene binding from BindingDB',
                'geneInteractsWithGene': 'Gene-gene interactions',
                'geneExpressedInAnatomy': 'Gene expression in anatomy from Bgee',
                'diseaseLocalizesToAnatomy': 'Disease localization',
                'geneParticipatesInBiologicalProcess': 'Gene-process associations',
                'geneHasMolecularFunction': 'Gene-function associations',
                'geneAssociatedWithCellularComponent': 'Gene-component associations'
            }
        }
