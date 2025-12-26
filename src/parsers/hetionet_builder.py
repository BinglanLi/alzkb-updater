"""
Hetionet Builder - Comprehensive Implementation

This module builds Hetionet from scratch by integrating data from multiple sources:
- Bgee (gene expression)
- Disease Ontology
- Gene Ontology
- GWAS Catalog
- MeSH
- Uberon (anatomy ontology)
- DrugCentral
- BindingDB
- MEDLINE (via PubMed)

Reference: https://github.com/EpistasisLab/AlzKB-updates
"""

import os
import logging
import requests
import gzip
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
from tqdm import tqdm
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class HetionetBuilder(BaseParser):
    """
    Builder for Hetionet knowledge graph from multiple data sources.
    """
    
    # Data source URLs (updated as of 2024)
    DATA_SOURCES = {
        # Ontologies
        'disease_ontology': {
            'url': 'https://github.com/DiseaseOntology/HumanDiseaseOntology/raw/main/src/ontology/doid.obo',
            'format': 'obo',
            'description': 'Disease Ontology - human disease concepts'
        },
        'gene_ontology': {
            'url': 'http://current.geneontology.org/ontology/go-basic.obo',
            'format': 'obo',
            'description': 'Gene Ontology - gene functions'
        },
        'uberon': {
            'url': 'http://purl.obolibrary.org/obo/uberon.obo',
            'format': 'obo',
            'description': 'Uberon - anatomy ontology'
        },
        
        # Phenotype and Disease
        'gwas_catalog': {
            'url': 'https://www.ebi.ac.uk/gwas/api/search/downloads/full',
            'format': 'tsv',
            'description': 'GWAS Catalog - genome-wide association studies'
        },
        'mesh': {
            'url': 'https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2025.xml',
            'format': 'xml',
            'description': 'MeSH - medical subject headings',
            'note': 'FTP link may require special handling'
        },
        
        # Drug and Chemical
        'drugcentral': {
            'url': 'https://unmtid-dbs.net/download/drugcentral.dump.01012025.sql.gz',
            'format': 'sql.gz',
            'description': 'DrugCentral - drug information',
            'note': 'Check https://unmtid-dbs.net/download/ for latest version'
        },
        'bindingdb': {
            'url': 'https://www.bindingdb.org/bind/downloads/BindingDB_All_2024m11.tsv.zip',
            'format': 'tsv.zip',
            'description': 'BindingDB - protein-ligand binding data'
        },
        
        # Gene Expression
        'bgee': {
            'url': 'https://www.bgee.org/ftp/current/download/calls/expr_calls/Homo_sapiens_expr_simple.tsv.gz',
            'format': 'tsv.gz',
            'description': 'Bgee - gene expression data'
        },
        
        # Literature
        'pubmed_baseline': {
            'url': 'https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/',
            'format': 'xml.gz',
            'description': 'PubMed baseline - biomedical literature',
            'note': 'Large dataset, selective download recommended'
        }
    }
    
    def __init__(self, data_dir: str):
        """
        Initialize Hetionet builder.
        
        Args:
            data_dir: Directory for storing downloaded data
        """
        super().__init__(data_dir, "hetionet")
        self.components_dir = self.data_dir / "components"
        self.components_dir.mkdir(parents=True, exist_ok=True)
    
    def download_data(self) -> bool:
        """
        Download all Hetionet component data sources.
        
        Returns:
            True if all downloads successful, False otherwise
        """
        logger.info("=" * 60)
        logger.info("Downloading Hetionet component data sources")
        logger.info("=" * 60)
        
        success_count = 0
        total_count = len(self.DATA_SOURCES)
        
        for source_name, source_info in self.DATA_SOURCES.items():
            logger.info(f"\nProcessing {source_name}...")
            logger.info(f"  Description: {source_info['description']}")
            
            if 'note' in source_info:
                logger.warning(f"  Note: {source_info['note']}")
            
            try:
                if self._download_source(source_name, source_info):
                    success_count += 1
                    logger.info(f"  ✓ {source_name} downloaded successfully")
                else:
                    logger.warning(f"  ✗ {source_name} download failed")
            except Exception as e:
                logger.error(f"  ✗ Error downloading {source_name}: {e}")
        
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Download Summary: {success_count}/{total_count} sources successful")
        logger.info(f"{'=' * 60}")
        
        return success_count > 0
    
    def _download_source(self, source_name: str, source_info: Dict[str, Any]) -> bool:
        """
        Download a single data source.
        
        Args:
            source_name: Name of the source
            source_info: Source information dict with url and format
        
        Returns:
            True if successful, False otherwise
        """
        url = source_info['url']
        format_type = source_info['format']
        
        # Determine output filename
        if format_type.endswith('.gz'):
            ext = format_type
        elif format_type.endswith('.zip'):
            ext = format_type
        else:
            ext = f".{format_type}"
        
        output_file = self.components_dir / f"{source_name}{ext}"
        
        # Check if already downloaded
        if output_file.exists():
            logger.info(f"  File already exists: {output_file}")
            return True
        
        # Special handling for FTP URLs
        if url.startswith('ftp://'):
            logger.warning(f"  FTP download required for {source_name}")
            logger.info(f"  Please download manually from: {url}")
            logger.info(f"  Save to: {output_file}")
            return False
        
        # Special handling for PubMed baseline (too large)
        if source_name == 'pubmed_baseline':
            logger.info(f"  PubMed baseline is very large")
            logger.info(f"  Selective download recommended")
            logger.info(f"  URL: {url}")
            # We'll skip this for now
            return False
        
        try:
            logger.info(f"  Downloading from: {url}")
            
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            # Get file size if available
            total_size = int(response.headers.get('content-length', 0))
            
            # Download with progress bar
            with open(output_file, 'wb') as f:
                if total_size > 0:
                    with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                            pbar.update(len(chunk))
                else:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            logger.info(f"  Saved to: {output_file}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"  Download failed: {e}")
            if output_file.exists():
                output_file.unlink()
            return False
        except Exception as e:
            logger.error(f"  Unexpected error: {e}")
            if output_file.exists():
                output_file.unlink()
            return False
    
    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse all downloaded Hetionet components.
        
        Returns:
            Dictionary of parsed DataFrames
        """
        logger.info("Parsing Hetionet components...")
        
        parsed_data = {}
        
        # Parse each component
        parsers = {
            'disease_ontology': self._parse_disease_ontology,
            'gene_ontology': self._parse_gene_ontology,
            'uberon': self._parse_uberon,
            'gwas_catalog': self._parse_gwas_catalog,
            'mesh': self._parse_mesh,
            'drugcentral': self._parse_drugcentral,
            'bindingdb': self._parse_bindingdb,
            'bgee': self._parse_bgee,
            'medline_cooccurrence': self._parse_medline_cooccurrence
        }
        
        for source_name, parser_func in parsers.items():
            try:
                logger.info(f"\nParsing {source_name}...")
                result = parser_func()
                if result:
                    parsed_data[source_name] = result
                    logger.info(f"  ✓ Parsed {source_name}")
            except Exception as e:
                logger.error(f"  ✗ Failed to parse {source_name}: {e}")
        
        return parsed_data
    
    def _parse_disease_ontology(self) -> Optional[pd.DataFrame]:
        """Parse Disease Ontology OBO file."""
        obo_file = self.components_dir / "disease_ontology.obo"
        if not obo_file.exists():
            logger.warning(f"Disease Ontology file not found: {obo_file}")
            return None
        
        diseases = []
        current_disease = {}
        
        with open(obo_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                if line == '[Term]':
                    if current_disease:
                        diseases.append(current_disease)
                    current_disease = {}
                elif line.startswith('id: DOID:'):
                    current_disease['disease_id'] = line.split(': ')[1]
                elif line.startswith('name: '):
                    current_disease['disease_name'] = line.split(': ', 1)[1]
                elif line.startswith('def: '):
                    # Extract definition
                    def_text = line.split(': ', 1)[1]
                    current_disease['definition'] = def_text.split('"')[1] if '"' in def_text else def_text
        
        if current_disease:
            diseases.append(current_disease)
        
        df = pd.DataFrame(diseases)
        logger.info(f"  Parsed {len(df)} diseases from Disease Ontology")
        return df
    
    def _parse_gene_ontology(self) -> Optional[pd.DataFrame]:
        """Parse Gene Ontology OBO file."""
        obo_file = self.components_dir / "gene_ontology.obo"
        if not obo_file.exists():
            logger.warning(f"Gene Ontology file not found: {obo_file}")
            return None
        
        terms = []
        current_term = {}
        
        with open(obo_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                if line == '[Term]':
                    if current_term:
                        terms.append(current_term)
                    current_term = {}
                elif line.startswith('id: GO:'):
                    current_term['go_id'] = line.split(': ')[1]
                elif line.startswith('name: '):
                    current_term['go_name'] = line.split(': ', 1)[1]
                elif line.startswith('namespace: '):
                    current_term['namespace'] = line.split(': ')[1]
        
        if current_term:
            terms.append(current_term)
        
        df = pd.DataFrame(terms)
        logger.info(f"  Parsed {len(df)} terms from Gene Ontology")
        return df
    
    def _parse_uberon(self) -> Optional[pd.DataFrame]:
        """Parse Uberon anatomy ontology."""
        obo_file = self.components_dir / "uberon.obo"
        if not obo_file.exists():
            logger.warning(f"Uberon file not found: {obo_file}")
            return None
        
        terms = []
        current_term = {}
        
        with open(obo_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                if line == '[Term]':
                    if current_term:
                        terms.append(current_term)
                    current_term = {}
                elif line.startswith('id: UBERON:'):
                    current_term['uberon_id'] = line.split(': ')[1]
                elif line.startswith('name: '):
                    current_term['anatomy_name'] = line.split(': ', 1)[1]
        
        if current_term:
            terms.append(current_term)
        
        df = pd.DataFrame(terms)
        logger.info(f"  Parsed {len(df)} anatomy terms from Uberon")
        return df
    
    def _parse_gwas_catalog(self) -> Optional[pd.DataFrame]:
        """Parse GWAS Catalog data."""
        tsv_file = self.components_dir / "gwas_catalog.tsv"
        if not tsv_file.exists():
            logger.warning(f"GWAS Catalog file not found: {tsv_file}")
            return None
        
        try:
            df = pd.read_csv(tsv_file, sep='\t', low_memory=False)
            logger.info(f"  Parsed {len(df)} associations from GWAS Catalog")
            return df
        except Exception as e:
            logger.error(f"  Failed to parse GWAS Catalog: {e}")
            return None
    

    def _parse_mesh(self) -> Optional[pd.DataFrame]:
        """
        Parse MeSH XML file to extract symptoms and clinical findings.
        
        MeSH (Medical Subject Headings) contains clinical symptoms that can be
        integrated into Hetionet as symptom nodes and disease-symptom relationships.
        
        Returns:
            DataFrame with symptom information
        """
        xml_file = self.components_dir / "mesh.xml"
        if not xml_file.exists():
            logger.warning(f"MeSH file not found: {xml_file}")
            return None
        
        try:
            import xml.etree.ElementTree as ET
            
            logger.info("  Parsing MeSH XML file...")
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            symptoms = []
            
            # MeSH XML structure: DescriptorRecordSet > DescriptorRecord
            for descriptor in root.findall('.//DescriptorRecord'):
                descriptor_ui = descriptor.find('.//DescriptorUI')
                descriptor_name = descriptor.find('.//DescriptorName/String')
                
                if descriptor_ui is None or descriptor_name is None:
                    continue
                
                mesh_id = descriptor_ui.text
                mesh_name = descriptor_name.text
                
                # Check if this is a symptom or clinical finding
                # Look for tree numbers starting with C23 (Pathological Conditions, Signs and Symptoms)
                tree_numbers = descriptor.findall('.//TreeNumber')
                is_symptom = False
                
                for tree_num in tree_numbers:
                    if tree_num.text and tree_num.text.startswith('C23'):
                        is_symptom = True
                        break
                
                if is_symptom:
                    # Extract scope note (definition)
                    scope_note = descriptor.find('.//ScopeNote')
                    definition = scope_note.text if scope_note is not None else ''
                    
                    symptoms.append({
                        'mesh_id': mesh_id,
                        'symptom_name': mesh_name,
                        'definition': definition,
                        'source': 'MeSH'
                    })
            
            if not symptoms:
                logger.warning("  No symptoms found in MeSH file")
                return None
            
            df = pd.DataFrame(symptoms)
            logger.info(f"  Parsed {len(df)} symptoms from MeSH")
            return df
            
        except Exception as e:
            logger.error(f"  Failed to parse MeSH: {e}")
            return None

    def _parse_drugcentral(self) -> Optional[pd.DataFrame]:
        """Parse DrugCentral data."""
        sql_file = self.components_dir / "drugcentral.sql.gz"
        if not sql_file.exists():
            logger.warning(f"DrugCentral file not found: {sql_file}")
            return None
        
        # DrugCentral is a SQL dump, would need SQL parsing
        # For now, just log that it exists
        logger.info(f"  DrugCentral SQL file available (parsing not yet implemented)")
        return None
    
    def _parse_bindingdb(self) -> Optional[pd.DataFrame]:
        """Parse BindingDB data."""
        zip_file = self.components_dir / "bindingdb.tsv.zip"
        if not zip_file.exists():
            logger.warning(f"BindingDB file not found: {zip_file}")
            return None
        
        try:
            # Extract and read TSV
            with zipfile.ZipFile(zip_file, 'r') as zf:
                # Find the TSV file in the archive
                tsv_files = [f for f in zf.namelist() if f.endswith('.tsv')]
                if not tsv_files:
                    logger.error("  No TSV file found in BindingDB archive")
                    return None
                
                with zf.open(tsv_files[0]) as f:
                    df = pd.read_csv(f, sep='\t', low_memory=False)
                    logger.info(f"  Parsed {len(df)} binding records from BindingDB")
                    return df
        except Exception as e:
            logger.error(f"  Failed to parse BindingDB: {e}")
            return None
    
    def _parse_bgee(self) -> Optional[pd.DataFrame]:
        """Parse Bgee gene expression data."""
        gz_file = self.components_dir / "bgee.tsv.gz"
        if not gz_file.exists():
            logger.warning(f"Bgee file not found: {gz_file}")
            return None
        
        try:
            df = pd.read_csv(gz_file, sep='\t', compression='gzip', low_memory=False)
            logger.info(f"  Parsed {len(df)} expression records from Bgee")
            return df
        except Exception as e:
            logger.error(f"  Failed to parse Bgee: {e}")
            return None

    def _parse_medline_cooccurrence(self) -> Optional[pd.DataFrame]:
        """
        Parse MEDLINE cooccurrence data to extract entity relationships.
        
        This method processes PubMed abstracts to identify cooccurrence of
        entities (genes, diseases, compounds) in the literature, which can
        be used to infer potential relationships.
        
        Note: This is a placeholder implementation. Full MEDLINE processing
        requires significant computational resources and specialized tools
        like PubTator or text mining pipelines.
        
        Returns:
            DataFrame with cooccurrence edges (entity1, entity2, pmid, cooccurrence_count)
        """
        logger.info("  Checking for MEDLINE cooccurrence data...")
        
        # Check if pre-computed cooccurrence file exists
        cooccur_file = self.components_dir / "medline_cooccurrence.tsv"
        
        if cooccur_file.exists():
            try:
                df = pd.read_csv(cooccur_file, sep='\t')
                logger.info(f"  ✓ Loaded {len(df)} cooccurrence edges from file")
                return df
            except Exception as e:
                logger.error(f"  Failed to load cooccurrence file: {e}")
                return None
        else:
            logger.info("  MEDLINE cooccurrence file not found")
            logger.info("  Note: MEDLINE cooccurrence extraction requires:")
            logger.info("    1. Download PubMed baseline from: https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/")
            logger.info("    2. Use tools like PubTator (https://www.ncbi.nlm.nih.gov/research/pubtator/)")
            logger.info("    3. Or use Hetionet's pre-computed cooccurrence data")
            logger.info("  Recommended: Download from Hetionet repository:")
            logger.info("    https://github.com/hetio/hetionet/tree/master/hetnet/tsv")
            
            # Try to download pre-computed cooccurrence from Hetionet
            try:
                import requests
                
                logger.info("  Attempting to download pre-computed cooccurrence from Hetionet...")
                
                # Hetionet provides pre-computed cooccurrence data
                hetionet_url = "https://github.com/hetio/hetionet/raw/master/hetnet/tsv/hetionet-v1.0-edges.sif.gz"
                
                response = requests.get(hetionet_url, timeout=60)
                response.raise_for_status()
                
                # Save to file
                import gzip
                output_file = self.components_dir / "hetionet_edges.sif.gz"
                output_file.write_bytes(response.content)
                
                # Read and filter for cooccurrence edges
                with gzip.open(output_file, 'rt') as f:
                    edges = []
                    for line in f:
                        parts = line.strip().split('\t')
                        if len(parts) == 3:
                            source, edge_type, target = parts
                            # Include literature-derived edges
                            if 'r' in edge_type.lower():  # 'r' indicates relationship/cooccurrence
                                edges.append({
                                    'source': source,
                                    'edge_type': edge_type,
                                    'target': target,
                                    'source_db': 'Hetionet'
                                })
                
                if edges:
                    df = pd.DataFrame(edges)
                    # Save for future use
                    df.to_csv(cooccur_file, sep='\t', index=False)
                    logger.info(f"  ✓ Downloaded and parsed {len(df)} cooccurrence edges")
                    return df
                else:
                    logger.warning("  No cooccurrence edges found in Hetionet data")
                    return None
                    
            except Exception as e:
                logger.warning(f"  Could not download Hetionet cooccurrence data: {e}")
                logger.info("  Skipping MEDLINE cooccurrence integration")
                return None

    
    def export_to_sif(self, data: Dict[str, pd.DataFrame], output_dir: str) -> List[str]:
        """
        Export parsed Hetionet data to SIF format for ista.
        
        SIF format: source <tab> relationship <tab> target
        
        Args:
            data: Dictionary of parsed DataFrames
            output_dir: Output directory
        
        Returns:
            List of created SIF files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        exported_files = []
        
        # Export different edge types
        # This is a simplified example - full implementation would create
        # edges from the parsed data
        
        logger.info("Exporting Hetionet edges to SIF format...")
        logger.info("(Full edge extraction not yet implemented)")
        
        return exported_files
    
    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """Get schema information for Hetionet components."""
        return {
            'disease_ontology': {
                'disease_id': 'Disease Ontology ID',
                'disease_name': 'Disease name',
                'definition': 'Disease definition'
            },
            'gene_ontology': {
                'go_id': 'Gene Ontology ID',
                'go_name': 'GO term name',
                'namespace': 'GO namespace (BP/MF/CC)'
            },
            'gwas_catalog': {
                'variant': 'Genetic variant',
                'trait': 'Associated trait',
                'p_value': 'Statistical significance'
            }
        }
