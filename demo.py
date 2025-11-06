#!/usr/bin/env python3
"""
Demo script to test AlzKB Updater functionality
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alzkb.integrator import AlzKBIntegrator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run a simple demo of AlzKB Updater"""
    logger.info("="*60)
    logger.info("AlzKB Updater Demo")
    logger.info("="*60)
    
    # Initialize with a small set of keywords for testing
    test_keywords = ["Alzheimer", "APOE"]
    
    logger.info(f"\nTesting with keywords: {test_keywords}")
    
    # Create integrator
    integrator = AlzKBIntegrator(keywords=test_keywords)
    
    # Run integration
    logger.info("\nStarting data integration...")
    integrated_df = integrator.integrate_data()
    
    # Generate and display summary
    logger.info("\nGenerating summary...")
    summary = integrator.generate_summary(integrated_df)
    
    logger.info("\n" + "="*60)
    logger.info("Demo Complete!")
    logger.info("="*60)
    logger.info(f"Total records: {summary.get('total_records', 0)}")
    logger.info(f"\nCheck the 'data/processed/' directory for output files:")
    logger.info("  - alzkb_integrated.csv")
    logger.info("  - alzkb_summary.txt")
    logger.info("  - Individual source files")
    

if __name__ == "__main__":
    main()
