#!/usr/bin/env python3
"""
Database Initialization Script for Kafka E-commerce System

This script creates all necessary database tables and populates them with sample data.
It can be run locally or on Railway to set up the database schema.
"""

import os
import sys
from models import DatabaseManager, db_manager
from config import Config

def init_database():
    """
    Initialize the database with tables and sample data
    """
    try:
        print("Starting database initialization...")
        
        # Get database URL from environment or config
        database_url = os.getenv('DATABASE_URL') or Config.DATABASE_URL
        print(f"Using database URL: {database_url[:20]}...")
        
        # Create database manager
        db_manager = DatabaseManager(database_url)
        
        # Create all tables
        print("Creating database tables...")
        db_manager.create_tables()
        print("✓ Database tables created successfully")
        
        # Initialize sample data
        print("Initializing sample data...")
        db_manager.init_sample_data()
        print("✓ Sample data initialized successfully")
        
        print("\n🎉 Database initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during database initialization: {e}")
        return False

def verify_database():
    """
    Verify that the database is properly set up
    """
    try:
        from models import Inventory, Order, Payment, Notification
        
        session = db_manager.get_session()
        
        # Check if tables exist and have data
        inventory_count = session.query(Inventory).count()
        print(f"Inventory items: {inventory_count}")
        
        if inventory_count > 0:
            print("✓ Database verification successful")
            
            # Show sample inventory
            print("\nSample inventory items:")
            items = session.query(Inventory).limit(3).all()
            for item in items:
                print(f"  - {item.name} ({item.product_id}): {item.quantity} units @ ${item.price}")
        else:
            print("⚠️  Database tables exist but no data found")
            
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

def main():
    """
    Main function to run database initialization
    """
    print("=" * 60)
    print("Kafka E-commerce Database Initialization")
    print("=" * 60)
    
    # Initialize database
    if init_database():
        print("\nVerifying database setup...")
        verify_database()
    else:
        print("\n❌ Database initialization failed")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Database initialization complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()