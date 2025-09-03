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
                'payments': '/api/payments',
                'service_health': {
                    'orders': '/api/orders/health',
                    'payments': '/api/payments/health',
                    'inventory': '/api/inventory/health',
                    'notifications': '/api/notifications/health',
                    'monitoring': '/api/monitoring/health',
                    'orchestrator': '/api/orchestrator/health'
                },
                'kafka': {
                    'topics': '/api/kafka/topics',
                    'messages': '/api/kafka/messages/<topic>'
                }
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
    
    # Individual order retrieval
    @app.route('/api/orders/<order_id>', methods=['GET'])
    def get_order(order_id):
        # Sample order data - in a real app this would come from database
        sample_order = {
            'id': order_id,
            'customer_id': 'customer_123',
            'status': 'completed',
            'total_amount': 299.99,
            'items': [
                {'product_id': 'LAPTOP001', 'quantity': 1, 'price': 299.99}
            ],
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'order': sample_order,
            'message': 'Order retrieved successfully'
        })
    
    # Individual payment retrieval
    @app.route('/api/payments/<payment_id>', methods=['GET'])
    def get_payment(payment_id):
        sample_payment = {
            'id': payment_id,
            'order_id': 'order_123',
            'amount': 299.99,
            'status': 'completed',
            'method': 'credit_card',
            'created_at': datetime.utcnow().isoformat()
        }
        return jsonify({'payment': sample_payment})
    
    # Order payments
    @app.route('/api/orders/<order_id>/payments', methods=['GET'])
    def get_order_payments(order_id):
        return jsonify({
            'payments': [{
                'id': f'payment_{order_id}',
                'order_id': order_id,
                'amount': 299.99,
                'status': 'completed',
                'method': 'credit_card'
            }]
        })
    
    # Customer orders
    @app.route('/api/customers/<customer_id>/orders', methods=['GET'])
    def get_customer_orders(customer_id):
        return jsonify({
            'orders': [{
                'id': 'order_123',
                'customer_id': customer_id,
                'status': 'completed',
                'total': 299.99,
                'created_at': datetime.utcnow().isoformat()
            }]
        })
    
    # Order validation
    @app.route('/api/orders/<order_id>/validate', methods=['POST'])
    def validate_order(order_id):
        return jsonify({
            'valid': True,
            'order_id': order_id,
            'message': 'Order is valid'
        })
    
    # Inventory endpoints
    @app.route('/api/inventory', methods=['GET'])
    def get_all_inventory():
        return jsonify({
            'inventory': [
                {'product_id': 'LAPTOP001', 'quantity': 50, 'reserved': 5},
                {'product_id': 'MOUSE001', 'quantity': 200, 'reserved': 10},
                {'product_id': 'KEYBOARD001', 'quantity': 75, 'reserved': 3}
            ]
        })
    
    @app.route('/api/inventory/<product_id>', methods=['GET', 'PUT'])
    def inventory_product(product_id):
        if request.method == 'GET':
            return jsonify({
                'product_id': product_id,
                'quantity': 50,
                'reserved': 5,
                'available': 45
            })
        else:  # PUT
            data = request.get_json()
            return jsonify({
                'message': 'Inventory updated',
                'product_id': product_id,
                'new_quantity': data.get('quantity', 50)
            })
    
    @app.route('/api/products/<product_id>', methods=['PUT'])
    def update_product(product_id):
        data = request.get_json()
        return jsonify({
            'message': 'Product updated',
            'product_id': product_id,
            'updated_fields': list(data.keys()) if data else []
        })
    
    # Reservations
    @app.route('/api/reservations', methods=['POST'])
    def create_reservation():
        data = request.get_json()
        return jsonify({
            'reservation_id': f'res_{int(time.time())}',
            'product_id': data.get('product_id'),
            'quantity': data.get('quantity'),
            'status': 'active'
        })
    
    @app.route('/api/reservations/<reservation_id>/release', methods=['POST'])
    def release_reservation(reservation_id):
        return jsonify({
            'message': 'Reservation released',
            'reservation_id': reservation_id
        })
    
    # Notifications
    @app.route('/api/notifications', methods=['POST'])
    def send_notification():
        data = request.get_json()
        return jsonify({
            'notification_id': f'notif_{int(time.time())}',
            'status': 'sent',
            'recipient': data.get('recipient')
        })
    
    @app.route('/api/notifications/<notification_id>', methods=['GET'])
    def get_notification(notification_id):
        return jsonify({
            'id': notification_id,
            'type': 'order_confirmation',
            'recipient': 'customer@example.com',
            'status': 'delivered',
            'created_at': datetime.utcnow().isoformat()
        })
    
    @app.route('/api/recipients/<recipient>/notifications', methods=['GET'])
    def get_recipient_notifications(recipient):
        return jsonify({
            'notifications': [{
                'id': 'notif_123',
                'type': 'order_confirmation',
                'recipient': recipient,
                'status': 'delivered'
            }]
        })
    
    @app.route('/api/templates', methods=['GET', 'POST'])
    def notification_templates():
        if request.method == 'GET':
            return jsonify({
                'templates': [{
                    'id': 'template_1',
                    'name': 'Order Confirmation',
                    'type': 'email'
                }]
            })
        else:  # POST
            data = request.get_json()
            return jsonify({
                'template_id': f'template_{int(time.time())}',
                'name': data.get('name'),
                'status': 'created'
            })
    
    # Orchestrator flows
    @app.route('/api/flows', methods=['GET', 'POST'])
    def order_flows():
        if request.method == 'GET':
            return jsonify({
                'flows': [{
                    'id': 'flow_123',
                    'order_id': 'order_123',
                    'status': 'completed',
                    'steps': ['validate', 'payment', 'inventory', 'notification']
                }]
            })
        else:  # POST
            data = request.get_json()
            return jsonify({
                'flow_id': f'flow_{int(time.time())}',
                'order_id': data.get('order_id'),
                'status': 'started'
            })
    
    @app.route('/api/flows/<order_id>', methods=['GET'])
    def get_order_flow(order_id):
        return jsonify({
            'flow_id': f'flow_{order_id}',
            'order_id': order_id,
            'status': 'completed',
            'steps': [
                {'name': 'validate', 'status': 'completed'},
                {'name': 'payment', 'status': 'completed'},
                {'name': 'inventory', 'status': 'completed'},
                {'name': 'notification', 'status': 'completed'}
            ]
        })

    # Products API
    @app.route('/api/products', methods=['GET'])
    def products():
        return jsonify({
            'products': [
                {'id': 'LAPTOP001', 'name': 'Gaming Laptop', 'price': 1299.99, 'stock': 50},
                {'id': 'MOUSE001', 'name': 'Wireless Mouse', 'price': 29.99, 'stock': 200},
                {'id': 'KEYBOARD001', 'name': 'Mechanical Keyboard', 'price': 89.99, 'stock': 75}
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
    
    # Individual service health endpoints
    @app.route('/api/orders/health')
    def orders_health():
        return jsonify({
            'service': 'orders',
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'kafka_connected': embedded_kafka is not None
        })
    
    @app.route('/api/payments/health')
    def payments_health():
        return jsonify({
            'service': 'payments',
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'kafka_connected': embedded_kafka is not None
        })
    
    @app.route('/api/inventory/health')
    def inventory_health():
        return jsonify({
            'service': 'inventory',
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'kafka_connected': embedded_kafka is not None
        })
    
    @app.route('/api/notifications/health')
    def notifications_health():
        return jsonify({
            'service': 'notifications',
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'kafka_connected': embedded_kafka is not None
        })
    
    @app.route('/api/monitoring/health')
    def monitoring_health():
        return jsonify({
            'service': 'monitoring',
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'kafka_connected': embedded_kafka is not None
        })
    
    @app.route('/api/orchestrator/health')
    def orchestrator_health():
        return jsonify({
            'service': 'orchestrator',
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'kafka_connected': embedded_kafka is not None
        })
    
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
    
    # Service-specific metrics endpoints
    @app.route('/api/metrics', methods=['GET'])
    def service_metrics():
        return jsonify({
            'orders_processed': 1250,
            'payments_completed': 1180,
            'inventory_updates': 450,
            'notifications_sent': 890,
            'uptime': '99.9%'
        })
    
    # Missing endpoints that frontend expects
    @app.route('/api/services/health')
    def services_health():
        return jsonify({
            'services': {
                'orders': {'status': 'healthy', 'uptime': '100%'},
                'payments': {'status': 'healthy', 'uptime': '100%'},
                'inventory': {'status': 'healthy', 'uptime': '100%'},
                'notifications': {'status': 'healthy', 'uptime': '100%'},
                'monitoring': {'status': 'healthy', 'uptime': '100%'},
                'orchestrator': {'status': 'healthy', 'uptime': '100%'}
            },
            'overall_status': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @app.route('/api/metrics/kafka')
    def metrics_kafka():
        topic_count = len(embedded_kafka.topics) if embedded_kafka else 0
        total_messages = sum(len(messages) for messages in embedded_kafka.topics.values()) if embedded_kafka else 0
        return jsonify({
            'topics': topic_count,
            'total_messages': total_messages,
            'status': 'running' if embedded_kafka else 'stopped',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @app.route('/api/metrics/orders')
    def metrics_orders():
        return jsonify({
            'total_orders': 156,
            'pending_orders': 12,
            'completed_orders': 144,
            'failed_orders': 0,
            'average_processing_time': '2.3s',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @app.route('/api/metrics/system')
    def metrics_system():
        return jsonify({
            'cpu_usage': '45%',
            'memory_usage': '62%',
            'disk_usage': '34%',
            'uptime': '99.9%',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @app.route('/api/metrics/prometheus')
    def metrics_prometheus():
        return jsonify({
            'metrics': {
                'http_requests_total': 1234,
                'http_request_duration_seconds': 0.123,
                'kafka_messages_produced_total': 567,
                'kafka_messages_consumed_total': 543
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @app.route('/api/alerts')
    def alerts():
        return jsonify({
            'alerts': [
                {
                    'id': 1,
                    'severity': 'info',
                    'message': 'System running normally',
                    'timestamp': datetime.utcnow().isoformat(),
                    'resolved': True
                }
            ],
            'total_alerts': 1,
            'active_alerts': 0
        })
    
    @app.route('/api/alerts/<alert_id>/resolve', methods=['POST'])
    def resolve_alert(alert_id):
        return jsonify({
            'message': 'Alert resolved',
            'alert_id': alert_id,
            'resolved_at': datetime.utcnow().isoformat()
        })
    
    @app.route('/api/dashboard')
    def dashboard():
        return jsonify({
            'summary': {
                'total_orders': 156,
                'total_revenue': 15678.90,
                'active_users': 89,
                'system_health': 'excellent'
            },
            'recent_activity': [
                {'type': 'order', 'message': 'New order #1234 created', 'timestamp': datetime.utcnow().isoformat()},
                {'type': 'payment', 'message': 'Payment processed for order #1233', 'timestamp': datetime.utcnow().isoformat()}
            ],
            'timestamp': datetime.utcnow().isoformat()
        })
    
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