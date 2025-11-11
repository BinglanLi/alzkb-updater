"""
Data cleaning and standardization utilities.
"""
import pandas as pd
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCleaner:
    """Clean and standardize biomedical data."""
    
    @staticmethod
    def clean_text(text: Optional[str]) -> str:
        """
        Clean text fields by removing extra whitespace and handling None values.
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        if pd.isna(text) or text is None:
            return ""
        
        # Convert to string and strip whitespace
        text = str(text).strip()
        
        # Remove multiple spaces
        text = " ".join(text.split())
        
        return text
    
    @staticmethod
    def standardize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize a DataFrame by cleaning text fields and handling missing values.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        logger.info(f"Cleaning DataFrame with {len(df)} rows and {len(df.columns)} columns")
        
        df_clean = df.copy()
        
        # Clean text columns
        for col in df_clean.columns:
            if df_clean[col].dtype == 'object':
                df_clean[col] = df_clean[col].apply(DataCleaner.clean_text)
        
        # Remove completely empty rows
        df_clean = df_clean.dropna(how='all')
        
        # Remove duplicate rows
        initial_len = len(df_clean)
        df_clean = df_clean.drop_duplicates()
        duplicates_removed = initial_len - len(df_clean)
        
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate rows")
        
        logger.info(f"Cleaned DataFrame now has {len(df_clean)} rows")
        
        return df_clean
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame, required_columns: list) -> bool:
        """
        Validate that a DataFrame has the required columns.
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            
        Returns:
            True if valid, False otherwise
        """
        missing_columns = set(required_columns) - set(df.columns)
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return False
        
        return True
