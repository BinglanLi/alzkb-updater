#!/usr/bin/env python3
"""
Main script to run AlzKB data integration
"""
import argparse
import logging
from alzkb.integrator import AlzKBIntegrator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='AlzKB Updater - Integrate Alzheimer\'s disease data from multiple sources'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory for data files'
    )
    parser.add_argument(
        '--keywords',
        type=str,
        nargs='+',
        default=None,
        help='Keywords for Alzheimer\'s disease search'
    )
    
    args = parser.parse_args()
    
    logger.info("Starting AlzKB Updater...")
    
    # Initialize integrator
    integrator = AlzKBIntegrator(
        output_dir=args.output_dir,
        keywords=args.keywords
    )
    
    # Run integration
    integrated_df = integrator.integrate_data()
    
    # Generate summary
    summary = integrator.generate_summary(integrated_df)
    
    logger.info("AlzKB update completed successfully!")
    logger.info(f"Total records integrated: {summary.get('total_records', 0)}")
    
    return 0


if __name__ == "__main__":
    exit(main())
