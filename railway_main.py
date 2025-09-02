#!/usr/bin/env python3
"""
Railway Main Application

Simplified version for Railway deployment that uses only embedded Kafka
and avoids confluent-kafka dependencies entirely.
"""

import os
import sys
import time
import threading
import json
from datetime import datetime
from pathlib import Path

# Set environment variables before any imports
os.environ['USE_EMBEDDED_KAFKA'] = 'true'
os.environ['ENVIRONMENT'] = 'production'
os.environ['DEBUG'] = 'false'
os.environ['EMBEDDED_KAFKA_URL'] = 'http://localhost:9093'
os.environ['EMBEDDED_KAFKA_PORT'] = '9093'
# Ensure no conflicting Kafka settings
if 'KAFKA_BOOTSTRAP_SERVERS' in os.environ:
    del os.environ['KAFKA_BOOTSTRAP_SERVERS']

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, request, jsonify
from flask_cors import CORS
from embedded_kafka import EmbeddedKafka
import structlog

# Setup logging
logger = structlog.get_logger(__name__)

# Global embedded Kafka instance
embedded_kafka = None

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    CORS(app)
    
    # Health check endpoint
    @app.route('/health')
    def health():
        kafka_status = 'running' if embedded_kafka else 'stopped'
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'kafka': kafka_status,
            'environment': 'railway',
            'version': '1.0.0'
        })
    
    # Root endpoint
    @app.route('/')
    def home():
        return jsonify({
            'message': 'Kafka E-commerce API - Railway Deployment',
            'status': 'running',
            'version': '1.0.0',
            'kafka': 'embedded',
            'endpoints': {
                'health': '/health',
                'orders': '/api/orders',
                'products': '/api/products',
                'payments': '/api/payments'
            }
        })
    
    # Orders API
    @app.route('/api/orders', methods=['GET', 'POST'])
    def orders():
        if request.method == 'POST':
            try:
                order_data = request.get_json()
                if not order_data:
                    return jsonify({'error': 'No order data provided'}), 400
                
                # Add timestamp and ID
                order_data['id'] = f"order_{int(time.time())}"
                order_data['timestamp'] = datetime.utcnow().isoformat()
                order_data['status'] = 'created'
                
                # Send to embedded Kafka
                if embedded_kafka:
                    embedded_kafka.produce('orders.created', order_data)
                    logger.info("Order created", order_id=order_data['id'])
                
                return jsonify({
                    'message': 'Order created successfully',
                    'order': order_data
                }), 201
            except Exception as e:
                logger.error("Failed to create order", error=str(e))
                return jsonify({'error': 'Failed to create order'}), 500
        else:
            # GET - return sample orders
            return jsonify({
                'orders': [
                    {
                        'id': 'order_1',
                        'status': 'completed',
                        'total': 99.99,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                ]
            })
    
    # Products API
    @app.route('/api/products', methods=['GET'])
    def products():
        return jsonify({
            'products': [
                {'id': 1, 'name': 'Sample Product 1', 'price': 29.99, 'stock': 100},
                {'id': 2, 'name': 'Sample Product 2', 'price': 49.99, 'stock': 50},
                {'id': 3, 'name': 'Sample Product 3', 'price': 19.99, 'stock': 200}
            ]
        })
    
    # Payments API
    @app.route('/api/payments', methods=['POST'])
    def payments():
        try:
            payment_data = request.get_json()
            if not payment_data:
                return jsonify({'error': 'No payment data provided'}), 400
            
            # Simulate payment processing
            payment_data['id'] = f"payment_{int(time.time())}"
            payment_data['timestamp'] = datetime.utcnow().isoformat()
            payment_data['status'] = 'completed'
            
            # Send to embedded Kafka
            if embedded_kafka:
                embedded_kafka.produce('payments.completed', payment_data)
                logger.info("Payment processed", payment_id=payment_data['id'])
            
            return jsonify({
                'message': 'Payment processed successfully',
                'payment': payment_data
            }), 200
        except Exception as e:
            logger.error("Failed to process payment", error=str(e))
            return jsonify({'error': 'Failed to process payment'}), 500
    
    # Kafka topics endpoint
    @app.route('/api/kafka/topics')
    def kafka_topics():
        if embedded_kafka:
            topics = list(embedded_kafka.topics.keys())
            return jsonify({'topics': topics})
        return jsonify({'topics': []})
    
    # Kafka messages endpoint
    @app.route('/api/kafka/messages/<topic>')
    def kafka_messages(topic):
        if embedded_kafka and topic in embedded_kafka.topics:
            messages = list(embedded_kafka.topics[topic])
            return jsonify({
                'topic': topic,
                'message_count': len(messages),
                'messages': messages[-10:]  # Last 10 messages
            })
        return jsonify({'error': 'Topic not found'}), 404
    
    return app

def setup_embedded_kafka():
    """Setup the embedded Kafka service"""
    global embedded_kafka
    try:
        embedded_kafka = EmbeddedKafka()
        
        # Create default topics
        topics = [
            'orders.created',
            'orders.validated', 
            'payments.requested',
            'payments.completed',
            'payments.failed',
            'inventory.reserved',
            'inventory.released',
            'notifications.email',
            'orders.completed',
            'orders.failed'
        ]
        
        for topic in topics:
            embedded_kafka.create_topic(topic)
        
        logger.info("Embedded Kafka setup successfully with topics", topics=topics)
        return embedded_kafka
    except Exception as e:
        logger.error("Failed to setup embedded Kafka", error=str(e))
        return None

def start_embedded_kafka():
    """Start embedded Kafka in a separate thread"""
    global embedded_kafka
    embedded_kafka = setup_embedded_kafka()
    if embedded_kafka:
        logger.info("Embedded Kafka started successfully")
    else:
        logger.error("Failed to start embedded Kafka")

def main():
    """Main application entry point"""
    logger.info("Starting Railway Kafka E-commerce Application...")
    
    # Get configuration from environment
    port = int(os.environ.get('PORT', 8000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    logger.info(f"Server configuration: {host}:{port}")
    
    # Start embedded Kafka in background thread
    kafka_thread = threading.Thread(target=start_embedded_kafka, daemon=True)
    kafka_thread.start()
    
    # Wait for Kafka to start
    time.sleep(3)
    
    # Create and start Flask app
    app = create_app()
    
    logger.info("Starting Flask application...")
    try:
        app.run(host=host, port=port, debug=False, threaded=True)
    except Exception as e:
        logger.error("Failed to start application", error=str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()