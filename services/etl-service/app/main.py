#!/usr/bin/env python3
"""
ETL Service - Data Loading and Processing
Handles Kaggle data downloads and database population
"""

import os
import sys
import logging
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from kaggle_loader import KaggleDataLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main ETL process"""
    try:
        logger.info("🚀 Starting ETL Service - Kaggle Data Loader")
        
        # Initialize the data loader
        loader = KaggleDataLoader()
        
        # Run the data loading process
        loader.run()
        
        logger.info("✅ ETL Service completed successfully")
        
    except Exception as e:
        logger.error(f"❌ ETL Service failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 