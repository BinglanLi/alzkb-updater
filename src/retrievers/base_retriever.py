"""
Base retriever class for biomedical database queries.
"""
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import requests
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class BaseRetriever(ABC):
    """Abstract base class for data retrievers."""
    
    def __init__(self, name: str, base_url: str, rate_limit: float = 1.0):
        """
        Initialize the retriever.
        
        Args:
            name: Name of the database
            base_url: Base URL for API requests
            rate_limit: Minimum seconds between requests
        """
        self.name = name
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    def _rate_limit_wait(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Optional[Dict] = None, 
                     headers: Optional[Dict] = None) -> Optional[requests.Response]:
        """
        Make an HTTP request with error handling.
        
        Args:
            url: URL to request
            params: Query parameters
            headers: Request headers
            
        Returns:
            Response object or None if request failed
        """
        self._rate_limit_wait()
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {str(e)}")
            return None
    
    @abstractmethod
    def retrieve_data(self, **kwargs) -> pd.DataFrame:
        """
        Retrieve data from the database.
        
        Returns:
            DataFrame containing retrieved data
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> List[str]:
        """
        Get the expected schema (column names) for this data source.
        
        Returns:
            List of column names
        """
        pass
