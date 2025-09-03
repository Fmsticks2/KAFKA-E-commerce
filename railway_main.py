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
import uuid
from datetime import datetime, timedelta
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
from models import db_manager, Order, OrderItem, Payment, Inventory, InventoryReservation, Notification, OrderFlow
from sqlalchemy.exc import IntegrityError
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
            order_data = request.get_json()
            session = db_manager.get_session()
            
            try:
                # Generate unique order ID
                order_id = f"order_{uuid.uuid4().hex[:12]}"
                
                # Calculate total amount from items
                total_amount = 0
                if 'items' in order_data:
                    for item_data in order_data['items']:
                        item_total = float(item_data['price']) * int(item_data['quantity'])
                        total_amount += item_total
                
                # Create order in database
                new_order = Order(
                    id=order_id,
                    customer_id=order_data.get('customer_id', f"customer_{uuid.uuid4().hex[:8]}"),
                    status='created',
                    total_amount=total_amount
                )
                session.add(new_order)
                
                # Add order items if provided
                if 'items' in order_data:
                    for item_data in order_data['items']:
                        order_item = OrderItem(
                            order_id=order_id,
                            product_id=item_data['product_id'],
                            quantity=int(item_data['quantity']),
                            price=float(item_data['price'])
                        )
                        session.add(order_item)
                
                session.commit()
                
                # Prepare response data
                response_data = {
                    'id': order_id,
                    'customer_id': new_order.customer_id,
                    'status': new_order.status,
                    'total_amount': new_order.total_amount,
                    'created_at': new_order.created_at.isoformat(),
                    'items': order_data.get('items', [])
                }
                
                # Send to embedded Kafka
                if embedded_kafka:
                    embedded_kafka.produce('orders.created', response_data)
                
                logger.info("Order created", order_id=order_id)
                return jsonify({
                    'message': 'Order created successfully',
                    'order': response_data
                }), 201
                
            except Exception as e:
                session.rollback()
                logger.error("Error creating order", error=str(e))
                return jsonify({'error': 'Failed to create order'}), 500
            finally:
                session.close()
        else:
            # GET - return orders from database
            session = db_manager.get_session()
            try:
                orders = session.query(Order).order_by(Order.created_at.desc()).limit(10).all()
                orders_data = []
                for order in orders:
                    order_items = session.query(OrderItem).filter(OrderItem.order_id == order.id).all()
                    items_data = [{
                        'product_id': item.product_id,
                        'quantity': item.quantity,
                        'price': item.price
                    } for item in order_items]
                    
                    orders_data.append({
                        'id': order.id,
                        'customer_id': order.customer_id,
                        'status': order.status,
                        'total_amount': order.total_amount,
                        'created_at': order.created_at.isoformat(),
                        'items': items_data
                    })
                
                return jsonify({'orders': orders_data})
            except Exception as e:
                logger.error("Error retrieving orders", error=str(e))
                return jsonify({'error': 'Failed to retrieve orders'}), 500
            finally:
                session.close()
    
    # Individual order retrieval
    @app.route('/api/orders/<order_id>', methods=['GET'])
    def get_order(order_id):
        session = db_manager.get_session()
        try:
            order = session.query(Order).filter(Order.id == order_id).first()
            if not order:
                return jsonify({'error': 'Order not found'}), 404
            
            # Get order items
            order_items = session.query(OrderItem).filter(OrderItem.order_id == order_id).all()
            items_data = [{
                'product_id': item.product_id,
                'quantity': item.quantity,
                'price': item.price
            } for item in order_items]
            
            return jsonify({
                'id': order.id,
                'customer_id': order.customer_id,
                'status': order.status,
                'total_amount': order.total_amount,
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat(),
                'items': items_data
            })
        except Exception as e:
            logger.error("Error retrieving order", order_id=order_id, error=str(e))
            return jsonify({'error': 'Failed to retrieve order'}), 500
        finally:
            session.close()
    
    # Individual payment retrieval
    @app.route('/api/payments/<payment_id>', methods=['GET'])
    def get_payment(payment_id):
        session = db_manager.get_session()
        try:
            payment = session.query(Payment).filter(Payment.id == payment_id).first()
            if not payment:
                return jsonify({'error': 'Payment not found'}), 404
            
            return jsonify({
                'id': payment.id,
                'order_id': payment.order_id,
                'amount': payment.amount,
                'status': payment.status,
                'payment_method': payment.payment_method,
                'transaction_id': payment.transaction_id,
                'created_at': payment.created_at.isoformat(),
                'updated_at': payment.updated_at.isoformat()
            })
        except Exception as e:
            logger.error("Error retrieving payment", payment_id=payment_id, error=str(e))
            return jsonify({'error': 'Failed to retrieve payment'}), 500
        finally:
            session.close()
    
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
    
    # Payment refund endpoint
    @app.route('/api/payments/<payment_id>/refund', methods=['POST'])
    def refund_payment(payment_id):
        data = request.get_json() or {}
        return jsonify({
            'refund_id': f'refund_{int(time.time())}',
            'payment_id': payment_id,
            'amount': 299.99,
            'reason': data.get('reason', 'Customer request'),
            'status': 'processed',
            'processed_at': datetime.utcnow().isoformat()
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
    
    # Inventory endpoints with database integration
    @app.route('/api/inventory', methods=['GET'])
    def get_all_inventory():
        from models import db_manager, Inventory, InventoryReservation
        session = db_manager.get_session()
        try:
            inventories = session.query(Inventory).all()
            inventory_list = []
            for inv in inventories:
                # Calculate reserved quantity
                reserved = session.query(InventoryReservation).filter_by(
                    product_id=inv.product_id, status='active'
                ).with_entities(InventoryReservation.quantity).all()
                reserved_qty = sum([r[0] for r in reserved]) if reserved else 0
                
                inventory_list.append({
                    'product_id': inv.product_id,
                    'name': inv.name,
                    'quantity': inv.quantity,
                    'price': inv.price,
                    'reserved': reserved_qty,
                    'available': inv.quantity - reserved_qty
                })
            return jsonify({'inventory': inventory_list})
        except Exception as e:
            logger.error(f"Error fetching inventory: {e}")
            return jsonify({'error': 'Failed to fetch inventory'}), 500
        finally:
            session.close()
    
    @app.route('/api/inventory/<product_id>', methods=['GET', 'PUT'])
    def inventory_product(product_id):
        from models import db_manager, Inventory, InventoryReservation
        session = db_manager.get_session()
        try:
            if request.method == 'GET':
                inventory = session.query(Inventory).filter_by(product_id=product_id).first()
                if not inventory:
                    return jsonify({'error': 'Product not found'}), 404
                
                # Calculate reserved quantity
                reserved = session.query(InventoryReservation).filter_by(
                    product_id=product_id, status='active'
                ).with_entities(InventoryReservation.quantity).all()
                reserved_qty = sum([r[0] for r in reserved]) if reserved else 0
                
                return jsonify({
                    'product_id': inventory.product_id,
                    'name': inventory.name,
                    'quantity': inventory.quantity,
                    'price': inventory.price,
                    'reserved': reserved_qty,
                    'available': inventory.quantity - reserved_qty
                })
            else:  # PUT
                data = request.get_json()
                inventory = session.query(Inventory).filter_by(product_id=product_id).first()
                if not inventory:
                    return jsonify({'error': 'Product not found'}), 404
                
                # Update inventory fields
                if 'quantity' in data:
                    inventory.quantity = data['quantity']
                if 'price' in data:
                    inventory.price = data['price']
                if 'name' in data:
                    inventory.name = data['name']
                
                inventory.updated_at = datetime.utcnow()
                session.commit()
                
                return jsonify({
                    'message': 'Inventory updated successfully',
                    'product_id': product_id,
                    'quantity': inventory.quantity,
                    'price': inventory.price,
                    'name': inventory.name
                })
        except Exception as e:
            session.rollback()
            logger.error(f"Error with inventory product {product_id}: {e}")
            return jsonify({'error': 'Failed to process inventory request'}), 500
        finally:
            session.close()
    
    @app.route('/api/products/<product_id>', methods=['PUT'])
    def update_product(product_id):
        from models import db_manager, Inventory
        session = db_manager.get_session()
        try:
            data = request.get_json()
            inventory = session.query(Inventory).filter_by(product_id=product_id).first()
            if not inventory:
                return jsonify({'error': 'Product not found'}), 404
            
            updated_fields = []
            if 'name' in data:
                inventory.name = data['name']
                updated_fields.append('name')
            if 'price' in data:
                inventory.price = data['price']
                updated_fields.append('price')
            if 'quantity' in data:
                inventory.quantity = data['quantity']
                updated_fields.append('quantity')
            
            inventory.updated_at = datetime.utcnow()
            session.commit()
            
            return jsonify({
                'message': 'Product updated successfully',
                'product_id': product_id,
                'updated_fields': updated_fields
            })
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating product {product_id}: {e}")
            return jsonify({'error': 'Failed to update product'}), 500
        finally:
            session.close()
    
    # Reservations with database integration
    @app.route('/api/reservations', methods=['POST'])
    def create_reservation():
        from models import db_manager, Inventory, InventoryReservation
        from datetime import timedelta
        session = db_manager.get_session()
        try:
            data = request.get_json()
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)
            order_id = data.get('order_id')
            
            if not product_id or not order_id:
                return jsonify({'error': 'Product ID and Order ID are required'}), 400
            
            # Check if product exists and has enough inventory
            inventory = session.query(Inventory).filter_by(product_id=product_id).first()
            if not inventory:
                return jsonify({'error': 'Product not found'}), 404
            
            # Calculate available quantity
            reserved = session.query(InventoryReservation).filter_by(
                product_id=product_id, status='active'
            ).with_entities(InventoryReservation.quantity).all()
            reserved_qty = sum([r[0] for r in reserved]) if reserved else 0
            available = inventory.quantity - reserved_qty
            
            if available < quantity:
                return jsonify({'error': 'Insufficient inventory'}), 400
            
            # Create reservation with UUID
            reservation_id = f'res_{uuid.uuid4().hex[:12]}'
            reservation = InventoryReservation(
                id=reservation_id,
                product_id=product_id,
                order_id=order_id,
                quantity=quantity,
                status='active',
                expires_at=datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
            )
            session.add(reservation)
            session.commit()
            
            return jsonify({
                'reservation_id': reservation_id,
                'product_id': product_id,
                'quantity': quantity,
                'order_id': order_id,
                'status': 'active',
                'expires_at': reservation.expires_at.isoformat()
            })
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating reservation: {e}")
            return jsonify({'error': 'Failed to create reservation'}), 500
        finally:
            session.close()
    
    @app.route('/api/reservations/<reservation_id>/release', methods=['POST'])
    def release_reservation(reservation_id):
        from models import db_manager, InventoryReservation
        session = db_manager.get_session()
        try:
            reservation = session.query(InventoryReservation).filter_by(id=reservation_id).first()
            if not reservation:
                return jsonify({'error': 'Reservation not found'}), 404
            
            reservation.status = 'released'
            session.commit()
            
            return jsonify({
                'message': 'Reservation released successfully',
                'reservation_id': reservation_id,
                'status': 'released'
            })
        except Exception as e:
            session.rollback()
            logger.error(f"Error releasing reservation {reservation_id}: {e}")
            return jsonify({'error': 'Failed to release reservation'}), 500
        finally:
            session.close()
    
    # Notifications
    @app.route('/api/notifications', methods=['POST'])
    def send_notification():
        data = request.get_json()
        session = db_manager.get_session()
        
        try:
            # Generate unique notification ID
            notification_id = f'notif_{uuid.uuid4().hex[:12]}'
            
            # Create notification in database
            notification = Notification(
                id=notification_id,
                recipient=data.get('recipient', 'unknown@example.com'),
                type=data.get('type', 'email'),
                template=data.get('template', 'default'),
                subject=data.get('subject', 'Notification'),
                message=data.get('message', 'Default notification message'),
                status='sent'
            )
            session.add(notification)
            session.commit()
            
            return jsonify({
                'notification_id': notification_id,
                'status': 'sent',
                'recipient': data.get('recipient'),
                'created_at': notification.created_at.isoformat()
            })
            
        except Exception as e:
            session.rollback()
            logger.error("Error sending notification", error=str(e))
            return jsonify({'error': 'Failed to send notification'}), 500
        finally:
            session.close()
    
    @app.route('/api/notifications/<notification_id>', methods=['GET'])
    def get_notification(notification_id):
        session = db_manager.get_session()
        try:
            notification = session.query(Notification).filter(Notification.id == notification_id).first()
            if not notification:
                return jsonify({'error': 'Notification not found'}), 404
            
            return jsonify({
                'id': notification.id,
                'recipient': notification.recipient,
                'type': notification.type,
                'template': notification.template,
                'subject': notification.subject,
                'message': notification.message,
                'status': notification.status,
                'created_at': notification.created_at.isoformat(),
                'sent_at': notification.sent_at.isoformat() if notification.sent_at else None
            })
        except Exception as e:
            logger.error("Error retrieving notification", notification_id=notification_id, error=str(e))
            return jsonify({'error': 'Failed to retrieve notification'}), 500
        finally:
            session.close()
    
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
            session = db_manager.get_session()
            
            try:
                order_id = data.get('order_id')
                if not order_id:
                    return jsonify({'error': 'Order ID is required'}), 400
                
                # Verify order exists
                order = session.query(Order).filter(Order.id == order_id).first()
                if not order:
                    return jsonify({'error': 'Order not found'}), 404
                
                # Create order flow entry
                flow = OrderFlow(
                    order_id=order_id,
                    step='validation',
                    status='started',
                    message='Order flow initiated'
                )
                session.add(flow)
                session.commit()
                
                return jsonify({
                    'flow_id': flow.id,
                    'order_id': order_id,
                    'status': 'started',
                    'current_step': 'validation',
                    'steps': ['validation', 'inventory_check', 'payment', 'fulfillment'],
                    'created_at': flow.created_at.isoformat()
                })
                
            except Exception as e:
                session.rollback()
                logger.error("Error starting order flow", error=str(e))
                return jsonify({'error': 'Failed to start order flow'}), 500
            finally:
                session.close()
    
    @app.route('/api/flows/<order_id>', methods=['GET'])
    def get_order_flow(order_id):
        session = db_manager.get_session()
        try:
            # Get all flow steps for the order
            flows = session.query(OrderFlow).filter(OrderFlow.order_id == order_id).order_by(OrderFlow.created_at).all()
            
            if not flows:
                return jsonify({'error': 'Order flow not found'}), 404
            
            # Get the latest flow status
            latest_flow = flows[-1]
            
            # Format flow steps
            steps = [{
                'step': flow.step,
                'status': flow.status,
                'message': flow.message,
                'timestamp': flow.created_at.isoformat()
            } for flow in flows]
            
            return jsonify({
                'flow_id': f'flow_{order_id}',
                'order_id': order_id,
                'status': latest_flow.status,
                'current_step': latest_flow.step,
                'steps': steps,
                'last_updated': latest_flow.created_at.isoformat()
            })
            
        except Exception as e:
            logger.error("Error retrieving order flow", order_id=order_id, error=str(e))
            return jsonify({'error': 'Failed to retrieve order flow'}), 500
        finally:
            session.close()

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
        payment_data = request.get_json()
        session = db_manager.get_session()
        
        try:
            if not payment_data:
                return jsonify({'error': 'No payment data provided'}), 400
            
            # Generate unique payment ID
            payment_id = f"payment_{uuid.uuid4().hex[:12]}"
            
            # Verify order exists
            order_id = payment_data.get('order_id')
            if order_id:
                order = session.query(Order).filter(Order.id == order_id).first()
                if not order:
                    return jsonify({'error': 'Order not found'}), 404
            
            # Create payment in database
            new_payment = Payment(
                id=payment_id,
                order_id=order_id,
                amount=float(payment_data.get('amount', 0)),
                status='completed',
                payment_method=payment_data.get('payment_method', 'credit_card'),
                transaction_id=f"txn_{uuid.uuid4().hex[:8]}"
            )
            session.add(new_payment)
            session.commit()
            
            # Prepare response data
            response_data = {
                'id': payment_id,
                'order_id': order_id,
                'amount': new_payment.amount,
                'status': new_payment.status,
                'payment_method': new_payment.payment_method,
                'transaction_id': new_payment.transaction_id,
                'created_at': new_payment.created_at.isoformat()
            }
            
            # Send to embedded Kafka
            if embedded_kafka:
                embedded_kafka.produce('payments.completed', response_data)
                logger.info("Payment processed", payment_id=payment_id)
            
            return jsonify({
                'message': 'Payment processed successfully',
                'payment': response_data
            }), 200
            
        except Exception as e:
            session.rollback()
            logger.error("Failed to process payment", error=str(e))
            return jsonify({'error': 'Failed to process payment'}), 500
        finally:
            session.close()
    
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