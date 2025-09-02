import json
import uuid
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import structlog
from jsonschema import validate, ValidationError
from config import Config
from kafka_utils import KafkaConnectionManager, MessageProducer, MessageConsumer

# Setup structured logging
logger = structlog.get_logger(__name__)

class OrderService:
    """Order Service handles order creation, validation, and state management"""
    
    def __init__(self):
        self.connection_manager = KafkaConnectionManager()
        self.producer = MessageProducer(self.connection_manager)
        self.orders = {}  # In-memory order storage (in production, use database)
        self.running = False
        
        # Order validation schema
        self.order_schema = {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "minLength": 1},
                "items": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "string", "minLength": 1},
                            "quantity": {"type": "integer", "minimum": 1},
                            "price": {"type": "number", "minimum": 0}
                        },
                        "required": ["product_id", "quantity", "price"]
                    }
                }
            },
            "required": ["customer_id", "items"]
        }
        
        # Start consumer for order status updates
        self._start_consumers()
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order"""
        try:
            # Validate order data
            validate(instance=order_data, schema=self.order_schema)
            
            # Generate order ID
            order_id = str(uuid.uuid4())
            
            # Calculate total amount
            total_amount = sum(item['quantity'] * item['price'] for item in order_data['items'])
            
            # Create order object
            order = {
                'order_id': order_id,
                'customer_id': order_data['customer_id'],
                'items': order_data['items'],
                'total_amount': total_amount,
                'status': 'created',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Store order
            self.orders[order_id] = order
            
            # Publish order created event
            success = self.producer.send_message(
                topic=Config.TOPICS['ORDERS_CREATED'],
                message=order,
                key=order_id
            )
            
            if success:
                logger.info("Order created successfully", order_id=order_id, customer_id=order_data['customer_id'])
                return {
                    'success': True,
                    'order_id': order_id,
                    'status': 'created',
                    'total_amount': total_amount
                }
            else:
                # Remove order if publishing failed
                del self.orders[order_id]
                logger.error("Failed to publish order created event", order_id=order_id)
                return {
                    'success': False,
                    'error': 'Failed to process order'
                }
                
        except ValidationError as e:
            logger.error("Order validation failed", error=str(e))
            return {
                'success': False,
                'error': f'Invalid order data: {e.message}'
            }
        except Exception as e:
            logger.error("Error creating order", error=str(e))
            return {
                'success': False,
                'error': 'Internal server error'
            }
    
    def validate_order(self, order_data: Dict[str, Any]) -> bool:
        """Validate order and publish validation result"""
        try:
            order_id = order_data['order_id']
            
            # Basic validation checks
            validation_passed = True
            validation_errors = []
            
            # Check if order exists
            if order_id not in self.orders:
                validation_errors.append("Order not found")
                validation_passed = False
            
            # Check customer ID format
            if not order_data.get('customer_id'):
                validation_errors.append("Invalid customer ID")
                validation_passed = False
            
            # Check items
            items = order_data.get('items', [])
            if not items:
                validation_errors.append("No items in order")
                validation_passed = False
            
            for item in items:
                if item.get('quantity', 0) <= 0:
                    validation_errors.append(f"Invalid quantity for product {item.get('product_id')}")
                    validation_passed = False
                if item.get('price', 0) < 0:
                    validation_errors.append(f"Invalid price for product {item.get('product_id')}")
                    validation_passed = False
            
            # Update order status
            if order_id in self.orders:
                if validation_passed:
                    self.orders[order_id]['status'] = 'validated'
                    self.orders[order_id]['updated_at'] = datetime.utcnow().isoformat()
                    
                    # Publish validated order event
                    self.producer.send_message(
                        topic=Config.TOPICS['ORDERS_VALIDATED'],
                        message=self.orders[order_id],
                        key=order_id
                    )
                    
                    logger.info("Order validated successfully", order_id=order_id)
                else:
                    self.orders[order_id]['status'] = 'validation_failed'
                    self.orders[order_id]['validation_errors'] = validation_errors
                    self.orders[order_id]['updated_at'] = datetime.utcnow().isoformat()
                    
                    # Publish order failed event
                    self.producer.send_message(
                        topic=Config.TOPICS['ORDERS_FAILED'],
                        message={
                            **self.orders[order_id],
                            'failure_reason': 'validation_failed',
                            'errors': validation_errors
                        },
                        key=order_id
                    )
                    
                    logger.error("Order validation failed", order_id=order_id, errors=validation_errors)
            
            return validation_passed
            
        except Exception as e:
            logger.error("Error validating order", order_id=order_data.get('order_id'), error=str(e))
            return False
    
    def handle_payment_completed(self, message: Dict[str, Any]) -> bool:
        """Handle payment completed event"""
        try:
            order_id = message['order_id']
            
            if order_id in self.orders:
                self.orders[order_id]['status'] = 'payment_completed'
                self.orders[order_id]['payment_id'] = message.get('payment_id')
                self.orders[order_id]['updated_at'] = datetime.utcnow().isoformat()
                
                logger.info("Payment completed for order", order_id=order_id)
            
            return True
            
        except Exception as e:
            logger.error("Error handling payment completed event", error=str(e))
            return False
    
    def handle_payment_failed(self, message: Dict[str, Any]) -> bool:
        """Handle payment failed event"""
        try:
            order_id = message['order_id']
            
            if order_id in self.orders:
                self.orders[order_id]['status'] = 'payment_failed'
                self.orders[order_id]['failure_reason'] = message.get('failure_reason', 'Payment processing failed')
                self.orders[order_id]['updated_at'] = datetime.utcnow().isoformat()
                
                # Publish order failed event
                self.producer.send_message(
                    topic=Config.TOPICS['ORDERS_FAILED'],
                    message={
                        **self.orders[order_id],
                        'failure_reason': 'payment_failed'
                    },
                    key=order_id
                )
                
                logger.error("Payment failed for order", order_id=order_id)
            
            return True
            
        except Exception as e:
            logger.error("Error handling payment failed event", error=str(e))
            return False
    
    def handle_order_completed(self, message: Dict[str, Any]) -> bool:
        """Handle order completed event"""
        try:
            order_id = message['order_id']
            
            if order_id in self.orders:
                self.orders[order_id]['status'] = 'completed'
                self.orders[order_id]['completed_at'] = datetime.utcnow().isoformat()
                self.orders[order_id]['updated_at'] = datetime.utcnow().isoformat()
                
                logger.info("Order completed successfully", order_id=order_id)
            
            return True
            
        except Exception as e:
            logger.error("Error handling order completed event", error=str(e))
            return False
    
    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        return self.orders.get(order_id)
    
    def get_orders_by_customer(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all orders for a customer"""
        return [order for order in self.orders.values() if order['customer_id'] == customer_id]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        total_orders = len(self.orders)
        status_counts = {}
        
        for order in self.orders.values():
            status = order['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        producer_metrics = self.producer.get_metrics()
        
        return {
            'total_orders': total_orders,
            'status_distribution': status_counts,
            'producer_metrics': producer_metrics
        }
    
    def _start_consumers(self):
        """Start Kafka consumers for order-related events"""
        def start_payment_consumer():
            consumer = MessageConsumer(
                connection_manager=self.connection_manager,
                topics=[Config.TOPICS['PAYMENTS_COMPLETED'], Config.TOPICS['PAYMENTS_FAILED']],
                group_id=Config.CONSUMER_GROUPS['ORDER_SERVICE'],
                message_handler=self._handle_payment_events
            )
            consumer.start_consuming()
        
        def start_completion_consumer():
            consumer = MessageConsumer(
                connection_manager=self.connection_manager,
                topics=[Config.TOPICS['ORDERS_COMPLETED']],
                group_id=f"{Config.CONSUMER_GROUPS['ORDER_SERVICE']}_completion",
                message_handler=self.handle_order_completed
            )
            consumer.start_consuming()
        
        # Start consumers in separate threads
        threading.Thread(target=start_payment_consumer, daemon=True).start()
        threading.Thread(target=start_completion_consumer, daemon=True).start()
        
        self.running = True
        logger.info("Order service consumers started")
    
    def _handle_payment_events(self, message: Dict[str, Any]) -> bool:
        """Route payment events to appropriate handlers"""
        status = message.get('status')
        
        if status == 'completed':
            return self.handle_payment_completed(message)
        elif status == 'failed':
            return self.handle_payment_failed(message)
        else:
            logger.warning("Unknown payment status", status=status)
            return True
    
    def stop(self):
        """Stop the service"""
        self.running = False
        self.connection_manager.close_connections()
        logger.info("Order service stopped")

# Flask web service for order management
app = Flask(__name__)

# Configure CORS for Vercel frontend integration
cors_origins = Config.get_cors_origins()
CORS(app, 
     origins=cors_origins,
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With', 'Accept', 'Origin'],
     supports_credentials=True)

order_service = OrderService()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'service': 'order_service',
            'timestamp': datetime.now().isoformat(),
            'running': order_service.running,
            'total_orders': len(order_service.orders)
        }), 200
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return jsonify({
            'status': 'unhealthy',
            'service': 'order_service',
            'error': str(e)
        }), 503

@app.route('/orders', methods=['POST'])
def create_order():
    """Create a new order"""
    try:
        order_data = request.get_json()
        result = order_service.create_order(order_data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error("Error in create_order endpoint", error=str(e))
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """Get order by ID"""
    order = order_service.get_order(order_id)
    
    if order:
        return jsonify(order)
    else:
        return jsonify({'error': 'Order not found'}), 404

@app.route('/customers/<customer_id>/orders', methods=['GET'])
def get_customer_orders(customer_id):
    """Get all orders for a customer"""
    orders = order_service.get_orders_by_customer(customer_id)
    return jsonify({'orders': orders})

@app.route('/orders/<order_id>/validate', methods=['POST'])
def validate_order(order_id):
    """Manually trigger order validation"""
    order = order_service.get_order(order_id)
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    success = order_service.validate_order(order)
    
    return jsonify({
        'success': success,
        'order_id': order_id,
        'status': order['status']
    })

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get service metrics"""
    metrics = order_service.get_metrics()
    return jsonify(metrics)

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        logger.info("Starting Order Service", port=Config.ORDER_SERVICE_PORT)
        app.run(host='0.0.0.0', port=Config.ORDER_SERVICE_PORT, debug=False)
    except KeyboardInterrupt:
        logger.info("Shutting down Order Service")
        order_service.stop()
    except Exception as e:
        logger.error("Error starting Order Service", error=str(e))
        order_service.stop()