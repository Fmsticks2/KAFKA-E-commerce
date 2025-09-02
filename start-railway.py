#!/usr/bin/env python3
"""
Railway Startup Script

This script starts the Kafka E-commerce application on Railway
using the embedded Kafka implementation to avoid confluent-kafka issues.
"""

import os
import sys
import time
import threading
import subprocess
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import our modules
from embedded_kafka import EmbeddedKafka
from main import app
import structlog

# Setup logging
logger = structlog.get_logger(__name__)

def start_embedded_kafka():
    """Start the embedded Kafka service"""
    try:
        kafka = EmbeddedKafka()
        kafka.start()
        logger.info("Embedded Kafka started successfully")
        return kafka
    except Exception as e:
        logger.error("Failed to start embedded Kafka", error=str(e))
        return None

def main():
    """Main startup function"""
    logger.info("Starting Railway deployment...")
    
    # Set environment variables for Railway
    os.environ.setdefault('USE_EMBEDDED_KAFKA', 'true')
    os.environ.setdefault('ENVIRONMENT', 'production')
    os.environ.setdefault('DEBUG', 'false')
    
    # Get port from Railway
    port = int(os.environ.get('PORT', 8000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    logger.info(f"Starting server on {host}:{port}")
    
    # Start embedded Kafka in a separate thread
    kafka_thread = threading.Thread(target=start_embedded_kafka, daemon=True)
    kafka_thread.start()
    
    # Give Kafka time to start
    time.sleep(2)
    
    # Start the Flask application
    try:
        app.run(host=host, port=port, debug=False)
    except Exception as e:
        logger.error("Failed to start Flask app", error=str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()