#!/usr/bin/env python3
"""
Database deployment script for Railway
This script initializes the database schema and populates it with sample data
"""

import os
import sys
import logging
from models import DatabaseManager
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def deploy_database():
    """Deploy database schema to Railway"""
    try:
        # Get database URL from environment
        database_url = Config.DATABASE_URL
        logger.info(f"Connecting to database: {database_url[:50]}...")
        
        # Initialize database manager
        db_manager = DatabaseManager(database_url)
        
        # Create tables
        logger.info("Creating database tables...")
        db_manager.create_tables()
        logger.info("Database tables created successfully")
        
        # Initialize with sample data
        logger.info("Initializing sample data...")
        db_manager.init_sample_data()
        logger.info("Sample data initialized successfully")
        
        # Verify deployment
        session = db_manager.get_session()
        try:
            from models import Order, OrderItem, Payment, Inventory
            
            order_count = session.query(Order).count()
            item_count = session.query(OrderItem).count()
            payment_count = session.query(Payment).count()
            inventory_count = session.query(Inventory).count()
            
            logger.info(f"Deployment verification:")
            logger.info(f"  Orders: {order_count}")
            logger.info(f"  Order Items: {item_count}")
            logger.info(f"  Payments: {payment_count}")
            logger.info(f"  Inventory Items: {inventory_count}")
            
        finally:
            session.close()
        
        logger.info("Database deployment completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database deployment failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = deploy_database()
    sys.exit(0 if success else 1)