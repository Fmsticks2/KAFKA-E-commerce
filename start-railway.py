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

# Set environment variables BEFORE importing any modules
os.environ['USE_EMBEDDED_KAFKA'] = 'true'
os.environ['ENVIRONMENT'] = 'production'
os.environ['DEBUG'] = 'false'
os.environ['KAFKA_BOOTSTRAP_SERVERS'] = 'embedded://localhost:9092'
os.environ['EMBEDDED_KAFKA_URL'] = 'http://localhost:9092'

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import our modules AFTER setting environment variables
from embedded_kafka import EmbeddedKafka
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

def start_simple_flask_app():
    """Start a simple Flask app without the complex main.py launcher"""
    from flask import Flask, jsonify
    from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'timestamp': time.time(),
            'kafka': 'embedded',
            'environment': 'railway'
        })
    
    @app.route('/')
    def home():
        return jsonify({
            'message': 'Kafka E-commerce API',
            'status': 'running',
            'version': '1.0.0',
            'kafka': 'embedded'
        })
    
    return app

def main():
    """Main startup function"""
    logger.info("Starting Railway deployment...")
    
    # Get port from Railway
    port = int(os.environ.get('PORT', 8000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    logger.info(f"Starting server on {host}:{port}")
    
    # Start embedded Kafka in a separate thread
    kafka_thread = threading.Thread(target=start_embedded_kafka, daemon=True)
    kafka_thread.start()
    
    # Give Kafka time to start
    time.sleep(3)
    
    # Start the simplified Flask application
    try:
        app = start_simple_flask_app()
        app.run(host=host, port=port, debug=False)
    except Exception as e:
        logger.error("Failed to start Flask app", error=str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()