"""
Data integration module for AlzKB
Integrates protein and drug data into unified knowledge base
"""
import pandas as pd
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlzKBIntegrator:
    """Integrates data from multiple sources into AlzKB"""
    
    def __init__(self, config: dict):
        self.config = config
        
    def integrate_protein_drug_data(self, 
                                    protein_df: pd.DataFrame, 
                                    drug_df: pd.DataFrame) -> pd.DataFrame:
        """
        Integrate protein and drug data based on gene targets
        
        Args:
            protein_df: DataFrame with protein information
            drug_df: DataFrame with drug information
            
        Returns:
            Integrated DataFrame
        """
        logger.info("Integrating protein and drug data...")
        
        if protein_df.empty or drug_df.empty:
            logger.warning("One or more input dataframes are empty")
            return pd.DataFrame()
        
        # Create drug-target relationships
        drug_target_pairs = []
        
        for _, drug_row in drug_df.iterrows():
            if 'target_genes' in drug_row and isinstance(drug_row['target_genes'], list):
                for gene in drug_row['target_genes']:
                    drug_target_pairs.append({
                        'drug_id': drug_row['drug_id'],
                        'drug_name': drug_row['drug_name'],
                        'drug_type': drug_row['drug_type'],
                        'mechanism': drug_row['mechanism'],
                        'approval_status': drug_row['approval_status'],
                        'target_gene': gene,
                        'indication': drug_row['indication']
                    })
        
        drug_target_df = pd.DataFrame(drug_target_pairs)
        
        # Merge with protein data
        if 'gene_name' in protein_df.columns and not drug_target_df.empty:
            integrated_df = pd.merge(
                protein_df,
                drug_target_df,
                left_on='gene_name',
                right_on='target_gene',
                how='outer'
            )
            
            logger.info(f"Created {len(integrated_df)} integrated records")
        else:
            # If no gene matching possible, concatenate with relationship type
            protein_df['entity_type'] = 'protein'
            drug_df['entity_type'] = 'drug'
            integrated_df = pd.concat([protein_df, drug_df], ignore_index=True, sort=False)
            logger.info(f"Concatenated {len(integrated_df)} total records")
        
        return integrated_df
    
    def create_knowledge_graph_edges(self, integrated_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create knowledge graph edges from integrated data
        
        Args:
            integrated_df: Integrated dataframe
            
        Returns:
            DataFrame with graph edges (source, relation, target)
        """
        logger.info("Creating knowledge graph edges...")
        
        edges = []
        
        # Drug-Protein interactions
        for _, row in integrated_df.iterrows():
            if pd.notna(row.get('drug_id')) and pd.notna(row.get('uniprot_id')):
                edges.append({
                    'source': row['drug_id'],
                    'source_name': row['drug_name'],
                    'source_type': 'drug',
                    'relation': 'targets',
                    'target': row['uniprot_id'],
                    'target_name': row['protein_name'],
                    'target_type': 'protein',
                    'mechanism': row.get('mechanism', ''),
                    'evidence': 'DrugBank'
                })
        
        edges_df = pd.DataFrame(edges)
        logger.info(f"Created {len(edges_df)} knowledge graph edges")
        
        return edges_df
    
    def deduplicate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate records"""
        logger.info("Removing duplicates...")
        initial_count = len(df)
        
        # Identify key columns for deduplication
        key_columns = []
        if 'uniprot_id' in df.columns:
            key_columns.append('uniprot_id')
        if 'drug_id' in df.columns:
            key_columns.append('drug_id')
            
        if key_columns:
            df = df.drop_duplicates(subset=key_columns, keep='first')
        
        logger.info(f"Removed {initial_count - len(df)} duplicates")
        return df
    
    def add_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add metadata to integrated data"""
        from datetime import datetime
        
        df['integration_date'] = datetime.now().strftime('%Y-%m-%d')
        df['alzkb_version'] = '1.0'
        
        return df
