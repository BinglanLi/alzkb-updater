"""
AlzKB v2 - Main Pipeline

This script orchestrates the complete AlzKB knowledge base construction pipeline:
1. Data retrieval from all sources
2. Data parsing and transformation
3. Ontology population using ista
4. Database preparation for Memgraph
5. Statistics and release notes generation
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from ontology.alzkb_populator import AlzKBOntologyPopulator, get_default_configs
from parsers import (
    AOPDBParser,
    DisGeNETParser,
    DrugBankParser,
    NCBIGeneParser,
    DoRothEAParser,
)
from parsers.hetionet_components import (
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
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alzkb_build.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class AlzKBPipeline:
    """Main pipeline for building AlzKB."""
    
    def __init__(self, base_dir: str):
        """
        Initialize the AlzKB pipeline.
        
        Args:
            base_dir: Base directory for the project
        """
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data"
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.ontology_dir = self.data_dir / "ontology"
        self.output_dir = self.data_dir / "output"
        
        # Create directories
        for dir_path in [self.raw_dir, self.processed_dir, self.ontology_dir, self.output_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.ontology_path = self.ontology_dir / "alzkb_v2.rdf"
        
        # Statistics
        self.stats = {
            'sources_processed': 0,
            'sources_failed': 0,
            'total_nodes': 0,
            'total_edges': 0,
            'start_time': datetime.now(),
            'end_time': None
        }
    
    def run_full_pipeline(self):
        """Run the complete AlzKB construction pipeline."""
        logger.info("=" * 80)
        logger.info("AlzKB v2 - Complete Pipeline")
        logger.info("=" * 80)
        logger.info(f"Start time: {self.stats['start_time']}")
        logger.info(f"Base directory: {self.base_dir}")
        logger.info("=" * 80)
        
        try:
            # Step 1: Retrieve and parse data from all sources
            logger.info("=" * 80)
            logger.info("STEP 1: Data Retrieval and Parsing")
            logger.info("=" * 80)
            parsed_data = self.retrieve_and_parse_data()
            
            # Step 2: Export to TSV/SIF format for ista
            logger.info("=" * 80)
            logger.info("STEP 2: Export to TSV/SIF Format")
            logger.info("=" * 80)
            tsv_files = self.export_to_tsv(parsed_data)
            
            # Step 3: Populate ontology using ista
            logger.info("=" * 80)
            logger.info("STEP 3: Ontology Population with ista")
            logger.info("=" * 80)
            rdf_files = self.populate_ontology_with_ista(tsv_files)
            
            # Step 4: Build database files
            logger.info("=" * 80)
            logger.info("STEP 4: Database Preparation")
            logger.info("=" * 80)
            self.build_database(rdf_files)
            
            # Step 5: Generate release notes
            logger.info("=" * 80)
            logger.info("STEP 5: Release Notes Generation")
            logger.info("=" * 80)
            self.generate_release_notes()
            
            self.stats['end_time'] = datetime.now()
            duration = self.stats['end_time'] - self.stats['start_time']
            
            logger.info("=" * 80)
            logger.info("Pipeline Completed Successfully!")
            logger.info("=" * 80)
            logger.info(f"Duration: {duration}")
            logger.info(f"Sources processed: {self.stats['sources_processed']}")
            logger.info(f"Sources failed: {self.stats['sources_failed']}")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"{'=' * 80}")
            logger.error(f"Pipeline Failed: {e}")
            logger.error(f"{'=' * 80}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def retrieve_and_parse_data(self) -> Dict[str, Dict]:
        """
        Retrieve and parse data from all sources.
        
        Returns:
            Dictionary mapping source names to parsed data
        """
        parsed_data = {}
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Define parsers - Core data sources
        parsers = {
            'aopdb': AOPDBParser(
                data_dir=str(self.raw_dir),
                mysql_config={
                    'host': 'localhost',
                    'user': os.getenv('MYSQL_USERNAME'),
                    'password': os.getenv('MYSQL_PASSWORD'),
                    'database': os.getenv('MYSQL_DB_NAME', 'aopdb')
                }
            ),
            'disgenet': DisGeNETParser(
                data_dir=str(self.raw_dir),
                api_key=os.getenv('DISGENET_API_KEY')
            ),
            'drugbank': DrugBankParser(
                data_dir=str(self.raw_dir),
                username=os.getenv('DRUGBANK_USERNAME'),
                password=os.getenv('DRUGBANK_PASSWORD')
            ),
            'ncbigene': NCBIGeneParser(
                data_dir=str(self.raw_dir),
            ),
            'dorothea': DoRothEAParser(
                data_dir=str(self.raw_dir),
            ),
            # Hetionet component parsers (replacing HetionetBuilder)
            'disease_ontology': DiseaseOntologyParser(
                data_dir=str(self.raw_dir / "hetionet")
            ),
            'gene_ontology': GeneOntologyParser(
                data_dir=str(self.raw_dir / "hetionet")
            ),
            'uberon': UberonParser(
                data_dir=str(self.raw_dir / "hetionet")
            ),
            'mesh': MeSHParser(
                data_dir=str(self.raw_dir / "hetionet")
            ),
            'gwas': GWASParser(
                data_dir=str(self.raw_dir / "hetionet")
            ),
            'drugcentral': DrugCentralParser(
                data_dir=str(self.raw_dir / "hetionet")
            ),
            'bindingdb': BindingDBParser(
                data_dir=str(self.raw_dir / "hetionet")
            ),
            'bgee': BgeeParser(
                data_dir=str(self.raw_dir / "hetionet")
            ),
            'ctd': CTDParser(
                data_dir=str(self.raw_dir / "hetionet")
            ),
            'hetionet_precomputed': HetionetPrecomputedParser(
                data_dir=str(self.raw_dir / "hetionet")
            ),
            'pubtator': PubTatorParser(
                data_dir=str(self.raw_dir / "hetionet")
            ),
        }
        
        # Process each parser
        for source_name, parser in parsers.items():
            logger.info(f"{'=' * 60}")
            logger.info(f"Processing {source_name.upper()}")
            logger.info(f"{'=' * 60}")
            
            try:
                # Download data
                logger.info(f"Downloading {source_name} data...")
                download_success = parser.download_data()
                
                if not download_success:
                    logger.warning(f"Download failed for {source_name}, attempting to use existing data")
                
                # Parse data
                logger.info(f"Parsing {source_name} data...")
                data = parser.parse_data()
                
                if data:
                    parsed_data[source_name] = data
                    self.stats['sources_processed'] += 1
                    logger.info(f"✓ Successfully processed {source_name}")
                    
                    # Log data summary
                    for key, df in data.items():
                        if hasattr(df, '__len__'):
                            logger.info(f"  - {key}: {len(df)} records")
                else:
                    logger.warning(f"No data parsed for {source_name}")
                    self.stats['sources_failed'] += 1
                    
            except Exception as e:
                logger.error(f"✗ Failed to process {source_name}: {e}")
                self.stats['sources_failed'] += 1
                import traceback
                logger.error(traceback.format_exc())
        
        return parsed_data
    
    def export_to_tsv(self, parsed_data: Dict[str, Dict]) -> Dict[str, List[str]]:
        """
        Export parsed data to TSV files for ista.
        
        Args:
            parsed_data: Dictionary of parsed data from all sources
        
        Returns:
            Dictionary mapping source names to lists of TSV file paths
        """
        tsv_files = {}
        
        for source_name, data in parsed_data.items():
            logger.info(f"Exporting {source_name} to TSV...")
            
            output_dir = self.processed_dir / source_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Export each DataFrame to TSV
                source_files = []
                for data_name, df in data.items():
                    if hasattr(df, 'to_csv'):
                        tsv_file = output_dir / f"{data_name}.tsv"
                        df.to_csv(tsv_file, sep='\t', index=False)
                        source_files.append(str(tsv_file))
                        logger.info(f"  ✓ Exported {data_name} ({len(df)} records)")
                
                tsv_files[source_name] = source_files
                
            except Exception as e:
                logger.error(f"  ✗ Failed to export {source_name}: {e}")
        
        return tsv_files
    
    def populate_ontology_with_ista(self, tsv_files: Dict[str, List[str]]) -> List[str]:
        """
        Populate ontology using ista via AlzKBOntologyPopulator.

        Args:
            tsv_files: Dictionary mapping source names to TSV file paths

        Returns:
            List of generated RDF file paths
        """
        if not self.ontology_path.exists():
            logger.error(f"Base ontology not found: {self.ontology_path}")
            return []

        # Initialize AlzKB ontology populator
        populator = AlzKBOntologyPopulator(
            ontology_path=str(self.ontology_path),
            data_dir=str(self.processed_dir)
        )

        # Get default configurations
        configs = get_default_configs()

        # Process each source
        for source_name, files in tsv_files.items():
            if source_name not in configs:
                logger.warning(f"No ista config for {source_name}, skipping")
                continue

            logger.info(f"Populating ontology from {source_name}...")

            config = configs[source_name]
            node_type = config.get('class_name', source_name)

            for tsv_file in files:
                try:
                    logger.info(f"  Processing {Path(tsv_file).name}...")

                    # Populate nodes from TSV file
                    success = populator.populate_nodes(
                        source_name=source_name,
                        node_type=node_type,
                        source_filename=Path(tsv_file).name,
                        fmt="tsv",
                        parse_config=config
                    )

                    if success:
                        logger.info(f"  ✓ Populated nodes from: {tsv_file}")
                    else:
                        logger.warning(f"  ⚠ No nodes populated from: {tsv_file}")

                except Exception as e:
                    logger.error(f"  ✗ Failed to populate from {tsv_file}: {e}")

        # Save the populated ontology
        output_rdf = self.output_dir / "alzkb_v2_populated.rdf"
        output_rdf.parent.mkdir(parents=True, exist_ok=True)

        try:
            populator.save_ontology(str(output_rdf))
            logger.info(f"✓ Saved populated ontology: {output_rdf}")

            # Print statistics
            populator.print_stats()

            return [str(output_rdf)]
        except Exception as e:
            logger.error(f"Failed to save ontology: {e}")
            return []
    
    
    def build_database(self, rdf_files: List[str]):
        """
        Build database files from RDF.
        
        Args:
            rdf_files: List of RDF file paths
        """
        if not rdf_files:
            logger.warning("No RDF files to process for database building")
            return
        
        logger.info("Building database files for Memgraph...")
        
        # Use the CSV exporter to create database files
        try:
            from rdflib import Graph
            
            # Load RDF data
            g = Graph()
            for rdf_file in rdf_files:
                logger.info(f"Loading RDF: {rdf_file}")
                g.parse(rdf_file, format='xml')
            
            logger.info(f"Total triples loaded: {len(g)}")
            
            # Extract nodes and edges
            nodes = set()
            edges = []
            
            for s, p, o in g:
                nodes.add(str(s))
                if not str(o).startswith('http'):
                    # Literal value
                    continue
                nodes.add(str(o))
                edges.append({
                    'source': str(s),
                    'relationship': str(p),
                    'target': str(o)
                })
            
            self.stats['total_nodes'] = len(nodes)
            self.stats['total_edges'] = len(edges)
            
            logger.info(f"Extracted {len(nodes)} nodes and {len(edges)} edges")
            
            # Export to CSV
            import pandas as pd
            
            # Nodes CSV
            nodes_df = pd.DataFrame({'node_id': list(nodes)})
            nodes_file = self.output_dir / "alzkb_nodes.csv"
            nodes_df.to_csv(nodes_file, index=False)
            logger.info(f"✓ Created nodes file: {nodes_file}")
            
            # Edges CSV
            edges_df = pd.DataFrame(edges)
            edges_file = self.output_dir / "alzkb_edges.csv"
            edges_df.to_csv(edges_file, index=False)
            logger.info(f"✓ Created edges file: {edges_file}")
            
        except Exception as e:
            logger.error(f"Failed to build database files: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def generate_release_notes(self):
        """Generate release notes for this version."""
        logger.info("Generating release notes...")
        
        release_notes = f"""# AlzKB v2 Release Notes

## Release Information
- **Version**: 2
- **Release Date**: {datetime.now().strftime('%Y-%m-%d')}
- **Build Duration**: {self.stats['end_time'] - self.stats['start_time'] if self.stats['end_time'] else 'N/A'}

## Data Sources
- **AOP-DB**: Adverse Outcome Pathway Database (MySQL)
- **DisGeNET**: Gene-disease associations (API)
- **DrugBank**: Drug information (Web authentication)
- **NCBI Gene**: Gene information
- **Hetionet Component Sources**:
  - Disease Ontology (Disease nodes)
  - Gene Ontology (BP, MF, CC nodes and gene associations)
  - Uberon (BodyPart/Anatomy nodes)
  - MeSH (Symptom nodes)
  - GWAS Catalog (geneAssociatesWithDisease)
  - DrugCentral (drugTreatsDisease, drugPalliatesDisease)
  - BindingDB (chemicalBindsGene)
  - Bgee (bodyPartOverexpressesGene, bodyPartUnderexpressesGene)
  - CTD (chemicalIncreasesExpression, chemicalDecreasesExpression)
  - Hetionet Precomputed (geneCovaries, geneRegulates, geneInteracts)
  - PubTator/MEDLINE (diseaseAssociatesWithDisease, literature mining)
  - DoRothEA (TranscriptionFactor nodes, TF-gene interactions)

## Statistics
- **Sources Processed**: {self.stats['sources_processed']}
- **Sources Failed**: {self.stats['sources_failed']}
- **Total Nodes**: {self.stats['total_nodes']:,}
- **Total Edges**: {self.stats['total_edges']:,}

## Improvements
- Integrated ista for ontology population
- Rebuilt Hetionet from scratch with updated sources
- Improved data retrieval with better error handling
- Added comprehensive logging
- Memgraph-compatible CSV export

## Known Issues
- Some data sources may require manual download
- FTP sources require special handling
- PubMed baseline is very large and not fully integrated

## Usage
The knowledge graph is available in the following formats:
- RDF/XML: `data/output/alzkb_v2_populated.rdf`
- CSV (nodes): `data/output/alzkb_nodes.csv`
- CSV (edges): `data/output/alzkb_edges.csv`

## Citation
If you use AlzKB in your research, please cite:
[Citation information to be added]

## Contact
For questions or issues, please open an issue on GitHub.
"""
        
        # Write release notes
        release_file = self.output_dir / "RELEASE_NOTES_v2.md"
        with open(release_file, 'w') as f:
            f.write(release_notes)
        
        logger.info(f"✓ Created release notes: {release_file}")
        
        # Also print to console
        print("\n" + release_notes)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='AlzKB v2 Pipeline')
    parser.add_argument('--base-dir', default='.', help='Base directory for the project')
    
    args = parser.parse_args()
    
    # Create and run pipeline
    pipeline = AlzKBPipeline(args.base_dir)
    pipeline.run_full_pipeline()


if __name__ == '__main__':
    main()
