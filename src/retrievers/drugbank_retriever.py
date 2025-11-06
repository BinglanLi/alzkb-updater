"""
DrugBank data retriever for Alzheimer's disease related drugs
Note: This is a simplified version using mock data since DrugBank requires API key
"""
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DrugBankRetriever:
    """Retrieves Alzheimer's-related drug data"""
    
    def __init__(self, config: dict):
        self.alzheimer_indication = config["alzheimer_indication"]
        
    def fetch_data(self) -> pd.DataFrame:
        """
        Fetch Alzheimer's related drugs
        For demonstration, creates sample data based on known AD drugs
        
        Returns:
            DataFrame with drug information
        """
        logger.info("Fetching Alzheimer's disease drug data...")
        
        # Sample Alzheimer's drugs (real FDA-approved drugs)
        sample_drugs = [
            {
                "drug_id": "DB00843",
                "drug_name": "Donepezil",
                "drug_type": "small molecule",
                "indication": "Alzheimer's disease",
                "mechanism": "Acetylcholinesterase inhibitor",
                "targets": "ACHE",
                "approval_status": "approved"
            },
            {
                "drug_id": "DB00989",
                "drug_name": "Rivastigmine",
                "drug_type": "small molecule",
                "indication": "Alzheimer's disease",
                "mechanism": "Cholinesterase inhibitor",
                "targets": "ACHE;BCHE",
                "approval_status": "approved"
            },
            {
                "drug_id": "DB00674",
                "drug_name": "Galantamine",
                "drug_type": "small molecule",
                "indication": "Alzheimer's disease",
                "mechanism": "Acetylcholinesterase inhibitor",
                "targets": "ACHE",
                "approval_status": "approved"
            },
            {
                "drug_id": "DB00764",
                "drug_name": "Memantine",
                "drug_type": "small molecule",
                "indication": "Alzheimer's disease",
                "mechanism": "NMDA receptor antagonist",
                "targets": "GRIN1;GRIN2A;GRIN2B;GRIN2C",
                "approval_status": "approved"
            },
            {
                "drug_id": "DB16845",
                "drug_name": "Aducanumab",
                "drug_type": "biotech",
                "indication": "Alzheimer's disease",
                "mechanism": "Amyloid beta binding",
                "targets": "APP",
                "approval_status": "approved"
            },
            {
                "drug_id": "DB17148",
                "drug_name": "Lecanemab",
                "drug_type": "biotech",
                "indication": "Alzheimer's disease",
                "mechanism": "Amyloid beta binding",
                "targets": "APP",
                "approval_status": "approved"
            }
        ]
        
        df = pd.DataFrame(sample_drugs)
        logger.info(f"Retrieved {len(df)} Alzheimer's drugs")
        return df
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize DrugBank data
        
        Args:
            df: Raw drug dataframe
            
        Returns:
            Cleaned dataframe
        """
        if df.empty:
            return df
            
        logger.info("Cleaning DrugBank data...")
        
        # Split targets into list
        if 'targets' in df.columns:
            df['target_genes'] = df['targets'].apply(
                lambda x: x.split(';') if pd.notna(x) else []
            )
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['drug_id'])
        
        # Add source column
        df['source'] = 'DrugBank'
        
        logger.info(f"Cleaned data: {len(df)} unique drugs")
        return df
    
    def save_data(self, df: pd.DataFrame, output_path: str):
        """Save data to CSV"""
        df.to_csv(output_path, index=False)
        logger.info(f"Saved DrugBank data to {output_path}")
