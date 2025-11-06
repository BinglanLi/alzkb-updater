"""
Data export module for AlzKB
Exports integrated data to CSV format
"""
import pandas as pd
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataExporter:
    """Exports AlzKB data to various formats"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def export_to_csv(self, df: pd.DataFrame, filename: str) -> str:
        """
        Export dataframe to CSV
        
        Args:
            df: DataFrame to export
            filename: Output filename
            
        Returns:
            Full path to exported file
        """
        output_path = os.path.join(self.output_dir, filename)
        df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(df)} records to {output_path}")
        return output_path
    
    def export_entities(self, integrated_df: pd.DataFrame):
        """
        Export separate entity files (proteins, drugs)
        
        Args:
            integrated_df: Integrated dataframe
        """
        logger.info("Exporting entity files...")
        
        # Export proteins
        protein_columns = ['uniprot_id', 'entry_name', 'gene_name', 'gene_names', 
                          'protein_name', 'organism', 'sequence_length', 
                          'function', 'disease_association']
        
        # Filter for rows with protein data
        has_protein = integrated_df['uniprot_id'].notna()
        protein_data = integrated_df[has_protein]
        
        # Select available columns
        available_protein_cols = [col for col in protein_columns if col in protein_data.columns]
        protein_df = protein_data[available_protein_cols].drop_duplicates()
        
        if not protein_df.empty:
            self.export_to_csv(protein_df, 'alzkb_proteins.csv')
        
        # Export drugs
        drug_columns = ['drug_id', 'drug_name', 'drug_type', 'indication', 
                       'mechanism', 'approval_status']
        
        # Filter for rows with drug data
        has_drug = integrated_df['drug_id'].notna()
        drug_data = integrated_df[has_drug]
        
        # Select available columns
        available_drug_cols = [col for col in drug_columns if col in drug_data.columns]
        drug_df = drug_data[available_drug_cols].drop_duplicates()
        
        if not drug_df.empty:
            self.export_to_csv(drug_df, 'alzkb_drugs.csv')
    
    def export_relationships(self, edges_df: pd.DataFrame):
        """
        Export relationship/edge data
        
        Args:
            edges_df: DataFrame with graph edges
        """
        if not edges_df.empty:
            self.export_to_csv(edges_df, 'alzkb_relationships.csv')
            logger.info("Exported relationship data")
    
    def create_summary_report(self, integrated_df: pd.DataFrame, 
                            edges_df: pd.DataFrame) -> str:
        """
        Create a summary report of the knowledge base
        
        Returns:
            Path to summary report
        """
        logger.info("Creating summary report...")
        
        summary = []
        summary.append("=" * 60)
        summary.append("AlzKB Summary Report")
        summary.append("=" * 60)
        summary.append("")
        
        # Count entities
        n_proteins = integrated_df['uniprot_id'].notna().sum() if 'uniprot_id' in integrated_df.columns else 0
        n_drugs = integrated_df['drug_id'].notna().sum() if 'drug_id' in integrated_df.columns else 0
        n_relationships = len(edges_df)
        
        summary.append(f"Total Proteins: {n_proteins}")
        summary.append(f"Total Drugs: {n_drugs}")
        summary.append(f"Total Relationships: {n_relationships}")
        summary.append("")
        
        # Top genes
        if 'gene_name' in integrated_df.columns:
            top_genes = integrated_df['gene_name'].value_counts().head(10)
            summary.append("Top 10 Genes:")
            for gene, count in top_genes.items():
                if pd.notna(gene):
                    summary.append(f"  - {gene}: {count}")
            summary.append("")
        
        # Drug mechanisms
        if 'mechanism' in integrated_df.columns:
            mechanisms = integrated_df['mechanism'].dropna().value_counts().head(5)
            summary.append("Top Drug Mechanisms:")
            for mech, count in mechanisms.items():
                summary.append(f"  - {mech}: {count}")
        
        summary_text = "\n".join(summary)
        
        # Save summary
        summary_path = os.path.join(self.output_dir, 'alzkb_summary.txt')
        with open(summary_path, 'w') as f:
            f.write(summary_text)
        
        logger.info(f"Summary report saved to {summary_path}")
        print("\n" + summary_text)
        
        return summary_path
