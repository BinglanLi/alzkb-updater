"""
AOPDBParser: Parser for AOP-DB (Adverse Outcome Pathway Database).

AOP-DB is a MySQL database containing information about adverse outcome
pathways, which describe causal relationships between molecular initiating
events and adverse outcomes.

Source: https://gaftp.epa.gov/EPADataCommons/ORD/AOP-DB/
Note: This is a large MySQL database that must be downloaded and imported.
"""

import logging
from typing import Dict, Optional, Any
import pandas as pd
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class AOPDBParser(BaseParser):
    """
    Parser for AOP-DB MySQL database.
    
    This parser connects to a MySQL database and extracts relevant
    adverse outcome pathway data.
    """
    
    def __init__(self, data_dir: Optional[str] = None, 
                 mysql_config: Optional[Dict[str, str]] = None):
        """
        Initialize the AOP-DB parser.
        
        Args:
            data_dir: Directory for cached data
            mysql_config: MySQL connection configuration with keys:
                         'host', 'user', 'password', 'database'
        """
        super().__init__(data_dir)
        self.mysql_config = mysql_config or {}
        self.connection = None
        self._mysql_available = False
        
        # Check if MySQL connector is available
        try:
            import mysql.connector
            self._mysql_available = True
            logger.info("MySQL connector is available")
        except ImportError:
            logger.warning("MySQL connector not available. Install with: pip install mysql-connector-python")
    
    def download_data(self) -> bool:
        """
        Check for AOP-DB database.
        
        Since AOP-DB is a large MySQL database, this method only checks
        if the database is accessible.
        
        Returns:
            True if database is accessible, False otherwise.
        """
        logger.info("Checking for AOP-DB database...")
        logger.info("Note: AOP-DB must be downloaded and imported into MySQL from:")
        logger.info("  https://gaftp.epa.gov/EPADataCommons/ORD/AOP-DB/")
        logger.info("  File: AOP-DB_v2.zip (7.2 GB compressed)")
        
        if not self._mysql_available:
            logger.error("MySQL connector not available")
            return False
        
        if not self.mysql_config:
            logger.error("MySQL configuration not provided")
            logger.info("Please provide mysql_config with: host, user, password, database")
            return False
        
        # Try to connect to database
        try:
            import mysql.connector
            
            conn = mysql.connector.connect(
                host=self.mysql_config.get('host', 'localhost'),
                user=self.mysql_config.get('user', 'root'),
                password=self.mysql_config.get('password', ''),
                database=self.mysql_config.get('database', 'aopdb')
            )
            
            self.connection = conn
            logger.info("✓ Successfully connected to AOP-DB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to AOP-DB: {e}")
            return False
    
    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse AOP-DB data.
        
        Extracts key tables from the AOP-DB MySQL database.
        
        Returns:
            Dictionary with DataFrames for different AOP entities.
        """
        logger.info("Parsing AOP-DB data...")
        
        if not self.connection:
            logger.error("Not connected to database. Call download_data() first.")
            return {}
        
        result = {}
        
        # Define queries for key tables
        queries = {
            'aops': "SELECT * FROM aop LIMIT 1000",
            'key_events': "SELECT * FROM key_event LIMIT 1000",
            'stressors': "SELECT * FROM stressor LIMIT 1000",
            'genes': "SELECT * FROM gene LIMIT 1000"
        }
        
        for table_name, query in queries.items():
            try:
                df = pd.read_sql(query, self.connection)
                result[table_name] = df
                logger.info(f"✓ Parsed {len(df)} rows from {table_name}")
            except Exception as e:
                logger.error(f"Failed to parse {table_name}: {e}")
        
        return result
    
    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for AOP-DB data.
        
        Returns:
            Dictionary describing the schema for AOP entities.
        """
        return {
            'aops': {
                'aop_id': 'AOP identifier',
                'aop_name': 'AOP name',
                'description': 'AOP description'
            },
            'key_events': {
                'ke_id': 'Key event identifier',
                'ke_name': 'Key event name',
                'biological_level': 'Biological organization level'
            },
            'stressors': {
                'stressor_id': 'Stressor identifier',
                'stressor_name': 'Stressor name',
                'cas_number': 'CAS Registry Number'
            },
            'genes': {
                'gene_id': 'Gene identifier',
                'gene_symbol': 'Gene symbol',
                'ncbi_gene_id': 'NCBI Gene ID'
            }
        }
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Closed database connection")
    
    def __del__(self):
        """Cleanup: close connection on deletion."""
        self.close()
