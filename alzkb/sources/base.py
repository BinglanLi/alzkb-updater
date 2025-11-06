"""
Base class for data sources
"""
import os
import pandas as pd
import requests
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataSource(ABC):
    """Abstract base class for all data sources"""
    
    def __init__(self, name: str, url: str, output_dir: str):
        self.name = name
        self.url = url
        self.output_dir = output_dir
        self.raw_data_path = os.path.join(output_dir, "raw", f"{name.lower()}_raw.csv")
        self.processed_data_path = os.path.join(output_dir, "processed", f"{name.lower()}_processed.csv")
        
    @abstractmethod
    def fetch_data(self) -> pd.DataFrame:
        """Fetch data from the source"""
        pass
    
    @abstractmethod
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize the data"""
        pass
    
    def save_raw_data(self, df: pd.DataFrame):
        """Save raw data to CSV"""
        os.makedirs(os.path.dirname(self.raw_data_path), exist_ok=True)
        df.to_csv(self.raw_data_path, index=False)
        logger.info(f"Saved raw data to {self.raw_data_path}")
        
    def save_processed_data(self, df: pd.DataFrame):
        """Save processed data to CSV"""
        os.makedirs(os.path.dirname(self.processed_data_path), exist_ok=True)
        df.to_csv(self.processed_data_path, index=False)
        logger.info(f"Saved processed data to {self.processed_data_path}")
        
    def update(self) -> pd.DataFrame:
        """Main update workflow"""
        logger.info(f"Starting update for {self.name}")
        
        # Fetch data
        logger.info(f"Fetching data from {self.name}...")
        raw_df = self.fetch_data()
        self.save_raw_data(raw_df)
        
        # Clean data
        logger.info(f"Cleaning data from {self.name}...")
        processed_df = self.clean_data(raw_df)
        self.save_processed_data(processed_df)
        
        logger.info(f"Update complete for {self.name}. Processed {len(processed_df)} records.")
        return processed_df
