#!/usr/bin/env python3
import sys
import os
import logging
from dotenv import load_dotenv

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', '.env'))

from database.db import Database
from utils.helpers import setup_logger

# Setup logging
logger = setup_logger('db_setup', 'logs/db_setup.log')

def main():
    """Initialize database and create tables."""
    logger.info("Starting database setup...")
    
    # Create database connection
    db = Database()
    
    # Check connection
    if not db.connection or not db.connection.is_connected():
        logger.error("Failed to connect to database. Check your credentials.")
        return False
    
    logger.info("Successfully connected to database.")
    
    # Create tables
    if db.create_tables():
        logger.info("All tables created successfully.")
    else:
        logger.error("Failed to create tables.")
        return False
    
    # Close connection
    db.close()
    logger.info("Database setup completed successfully.")
    return True

if __name__ == "__main__":
    if main():
        print("Database setup completed successfully.")
    else:
        print("Database setup failed. Check logs for details.")
