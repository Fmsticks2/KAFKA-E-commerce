import json
import uuid
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import structlog
from config import Config
from kafka_utils import KafkaConnectionManager, MessageProducer, MessageConsumer

# Setup structured logging
logger = structlog.get_logger(__name__)

class InventoryService:
    """Inventory Service handles stock management and reservations"""
    
    def __init__(self):
        self.connection_manager = KafkaConnectionManager()
        self.producer = MessageProducer(self.connection_manager)
        self.inventory = {}  # In-memory inventory storage
        self.reservations = {}  # Active reservations
        self.running = False
        
        # Initialize sample inventory
        self._initialize_inventory()
        
        # Start consumer for inventory requests
        self._start_consumers()
        
        # Start reservation cleanup thread
        self._start_reservation_cleanup()
    
    def _initialize_inventory(self):
        """Initialize sample inventory data"""
        sample_products = [
            {'product_id': 'LAPTOP001', 'name': 'Gaming Laptop', 'quantity': 50, 'price': 1299.99},
            {'product_id': 'PHONE001', 'name': 'Smartphone', 'quantity': 100, 'price': 699.99},
            {'product_id': 'TABLET001', 'name': 'Tablet', 'quantity': 75, 'price': 399.99},
            {'product_id': 'HEADPHONES001', 'name': 'Wireless Headphones', 'quantity': 200, 'price': 199.99},
            {'product_id': 'MOUSE001', 'name': 'Gaming Mouse', 'quantity': 150, 'price': 79.99},
            {'product_id': 'KEYBOARD001', 'name': 'Mechanical Keyboard', 'quantity': 120, 'price': 149.99},
            {'product_id': 'MONITOR001', 'name': '4K Monitor', 'quantity': 30, 'price': 499.99},
            {'product_id': 'CAMERA001', 'name': 'Digital Camera', 'quantity': 25, 'price': 899.99},
            {'product_id': 'SPEAKER001', 'name': 'Bluetooth Speaker', 'quantity': 80, 'price': 129.99},
            {'product_id': 'WATCH001', 'name': 'Smart Watch', 'quantity': 60, 'price': 299.99}
        ]
        
        for product in sample_products:
            self.inventory[product['product_id']] = {
                'product_id': product['product_id'],
                'name': product['name'],
                'available_quantity': product['quantity'],
                'reserved_quantity': 0,
                'total_quantity': product['quantity'],
                'price': product['price'],
                'last_updated': datetime.utcnow().isoformat()
            }
        
        logger.info("Inventory initialized", product_count=len(sample_products))
    
    def reserve_inventory(self, order_id: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Reserve inventory for an order"""
        try:
            reservation_id = str(uuid.uuid4())
            reservation_items = []
            insufficient_items = []
            
            # Check availability for all items first
            for item in items:
                product_id = item['product_id']
                quantity = item['quantity']
                
                if product_id not in self.inventory:
                    insufficient_items.append({
                        'product_id': product_id,
                        'reason': 'Product not found',
                        'requested': quantity,
                        'available': 0
                    })
                    continue
                
                product = self.inventory[product_id]
                available = product['available_quantity']
                
                if available < quantity:
                    insufficient_items.append({
                        'product_id': product_id,
                        'reason': 'Insufficient stock',
                        'requested': quantity,
                        'available': available
                    })
            
            # If any items are insufficient, reject the entire reservation
            if insufficient_items:
                logger.warning("Inventory reservation failed", order_id=order_id, insufficient_items=insufficient_items)
                
                # Publish inventory reservation failed event
                self.producer.send_message(
                    topic=Config.TOPICS['INVENTORY_RELEASED'],
                    message={
                        'order_id': order_id,
                        'reservation_id': reservation_id,
                        'status': 'failed',
                        'reason': 'insufficient_inventory',
                        'insufficient_items': insufficient_items,
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    key=order_id
                )
                
                return {
                    'success': False,
                    'reservation_id': reservation_id,
                    'reason': 'insufficient_inventory',
                    'insufficient_items': insufficient_items
                }
            
            # Reserve all items
            for item in items:
                product_id = item['product_id']
                quantity = item['quantity']
                
                product = self.inventory[product_id]
                product['available_quantity'] -= quantity
                product['reserved_quantity'] += quantity
                product['last_updated'] = datetime.utcnow().isoformat()
                
                reservation_items.append({
                    'product_id': product_id,
                    'quantity': quantity,
                    'price': product['price']
                })
            
            # Create reservation record
            reservation = {
                'reservation_id': reservation_id,
                'order_id': order_id,
                'items': reservation_items,
                'status': 'active',
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(minutes=30)).isoformat()  # 30-minute expiry
            }
            
            self.reservations[reservation_id] = reservation
            
            # Publish inventory reserved event
            self.producer.send_message(
                topic=Config.TOPICS['INVENTORY_RESERVED'],
                message={
                    'order_id': order_id,
                    'reservation_id': reservation_id,
                    'items': reservation_items,
                    'status': 'reserved',
                    'timestamp': datetime.utcnow().isoformat()
                },
                key=order_id
            )
            
            logger.info("Inventory reserved successfully", order_id=order_id, reservation_id=reservation_id)
            
            return {
                'success': True,
                'reservation_id': reservation_id,
                'items': reservation_items,
                'expires_at': reservation['expires_at']
            }
            
        except Exception as e:
            logger.error("Error reserving inventory", order_id=order_id, error=str(e))
            return {
                'success': False,
                'error': 'Inventory reservation error'
            }
    
    def release_reservation(self, reservation_id: str, reason: str = 'Order cancelled') -> bool:
        """Release an inventory reservation"""
        try:
            if reservation_id not in self.reservations:
                logger.warning("Reservation not found", reservation_id=reservation_id)
                return False
            
            reservation = self.reservations[reservation_id]
            
            if reservation['status'] != 'active':
                logger.warning("Reservation not active", reservation_id=reservation_id, status=reservation['status'])
                return False
            
            # Release reserved quantities back to available
            for item in reservation['items']:
                product_id = item['product_id']
                quantity = item['quantity']
                
                if product_id in self.inventory:
                    product = self.inventory[product_id]
                    product['available_quantity'] += quantity
                    product['reserved_quantity'] -= quantity
                    product['last_updated'] = datetime.utcnow().isoformat()
            
            # Update reservation status
            reservation['status'] = 'released'
            reservation['released_at'] = datetime.utcnow().isoformat()
            reservation['release_reason'] = reason
            
            # Publish inventory released event
            self.producer.send_message(
                topic=Config.TOPICS['INVENTORY_RELEASED'],
                message={
                    'order_id': reservation['order_id'],
                    'reservation_id': reservation_id,
                    'items': reservation['items'],
                    'status': 'released',
                    'reason': reason,
                    'timestamp': datetime.utcnow().isoformat()
                },
                key=reservation['order_id']
            )
            
            logger.info("Inventory reservation released", reservation_id=reservation_id, reason=reason)
            return True
            
        except Exception as e:
            logger.error("Error releasing reservation", reservation_id=reservation_id, error=str(e))
            return False
    
    def confirm_reservation(self, reservation_id: str) -> bool:
        """Confirm a reservation (convert reserved to sold)"""
        try:
            if reservation_id not in self.reservations:
                logger.warning("Reservation not found", reservation_id=reservation_id)
                return False
            
            reservation = self.reservations[reservation_id]
            
            if reservation['status'] != 'active':
                logger.warning("Reservation not active", reservation_id=reservation_id, status=reservation['status'])
                return False
            
            # Confirm the reservation (reduce reserved quantity)
            for item in reservation['items']:
                product_id = item['product_id']
                quantity = item['quantity']
                
                if product_id in self.inventory:
                    product = self.inventory[product_id]
                    product['reserved_quantity'] -= quantity
                    product['total_quantity'] -= quantity  # Permanently reduce total
                    product['last_updated'] = datetime.utcnow().isoformat()
            
            # Update reservation status
            reservation['status'] = 'confirmed'
            reservation['confirmed_at'] = datetime.utcnow().isoformat()
            
            logger.info("Inventory reservation confirmed", reservation_id=reservation_id)
            return True
            
        except Exception as e:
            logger.error("Error confirming reservation", reservation_id=reservation_id, error=str(e))
            return False
    
    def handle_order_validated(self, message: Dict[str, Any]) -> bool:
        """Handle validated order event"""
        try:
            order_id = message['order_id']
            items = message['items']
            
            # Reserve inventory for the validated order
            result = self.reserve_inventory(order_id, items)
            
            return result['success']
            
        except Exception as e:
            logger.error("Error handling order validated event", error=str(e))
            return False
    
    def handle_payment_failed(self, message: Dict[str, Any]) -> bool:
        """Handle payment failed event"""
        try:
            order_id = message['order_id']
            
            # Find and release reservation for this order
            for reservation_id, reservation in self.reservations.items():
                if reservation['order_id'] == order_id and reservation['status'] == 'active':
                    self.release_reservation(reservation_id, 'Payment failed')
                    break
            
            return True
            
        except Exception as e:
            logger.error("Error handling payment failed event", error=str(e))
            return False
    
    def handle_order_completed(self, message: Dict[str, Any]) -> bool:
        """Handle order completed event"""
        try:
            order_id = message['order_id']
            
            # Find and confirm reservation for this order
            for reservation_id, reservation in self.reservations.items():
                if reservation['order_id'] == order_id and reservation['status'] == 'active':
                    self.confirm_reservation(reservation_id)
                    break
            
            return True
            
        except Exception as e:
            logger.error("Error handling order completed event", error=str(e))
            return False
    
    def get_product_inventory(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get inventory information for a product"""
        return self.inventory.get(product_id)
    
    def get_all_inventory(self) -> Dict[str, Any]:
        """Get all inventory information"""
        return self.inventory
    
    def update_inventory(self, product_id: str, quantity: int) -> bool:
        """Update inventory quantity for a product"""
        try:
            if product_id not in self.inventory:
                return False
            
            product = self.inventory[product_id]
            old_quantity = product['total_quantity']
            
            product['total_quantity'] = quantity
            product['available_quantity'] = quantity - product['reserved_quantity']
            product['last_updated'] = datetime.utcnow().isoformat()
            
            logger.info("Inventory updated", product_id=product_id, old_quantity=old_quantity, new_quantity=quantity)
            return True
            
        except Exception as e:
            logger.error("Error updating inventory", product_id=product_id, error=str(e))
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        total_products = len(self.inventory)
        total_available = sum(product['available_quantity'] for product in self.inventory.values())
        total_reserved = sum(product['reserved_quantity'] for product in self.inventory.values())
        total_inventory_value = sum(product['available_quantity'] * product['price'] for product in self.inventory.values())
        
        active_reservations = len([r for r in self.reservations.values() if r['status'] == 'active'])
        expired_reservations = len([r for r in self.reservations.values() if r['status'] == 'released'])
        confirmed_reservations = len([r for r in self.reservations.values() if r['status'] == 'confirmed'])
        
        low_stock_products = [p for p in self.inventory.values() if p['available_quantity'] < 10]
        
        producer_metrics = self.producer.get_metrics()
        
        return {
            'total_products': total_products,
            'total_available_quantity': total_available,
            'total_reserved_quantity': total_reserved,
            'total_inventory_value': round(total_inventory_value, 2),
            'active_reservations': active_reservations,
            'expired_reservations': expired_reservations,
            'confirmed_reservations': confirmed_reservations,
            'low_stock_products': len(low_stock_products),
            'low_stock_items': [{'product_id': p['product_id'], 'quantity': p['available_quantity']} for p in low_stock_products],
            'producer_metrics': producer_metrics
        }
    
    def _start_consumers(self):
        """Start Kafka consumers for inventory-related events"""
        def start_order_consumer():
            consumer = MessageConsumer(
                connection_manager=self.connection_manager,
                topics=[Config.TOPICS['ORDERS_VALIDATED']],
                group_id=Config.CONSUMER_GROUPS['INVENTORY_SERVICE'],
                message_handler=self.handle_order_validated
            )
            consumer.start_consuming()
        
        def start_payment_consumer():
            consumer = MessageConsumer(
                connection_manager=self.connection_manager,
                topics=[Config.TOPICS['PAYMENTS_FAILED']],
                group_id=f"{Config.CONSUMER_GROUPS['INVENTORY_SERVICE']}_payment",
                message_handler=self.handle_payment_failed
            )
            consumer.start_consuming()
        
        def start_completion_consumer():
            consumer = MessageConsumer(
                connection_manager=self.connection_manager,
                topics=[Config.TOPICS['ORDERS_COMPLETED']],
                group_id=f"{Config.CONSUMER_GROUPS['INVENTORY_SERVICE']}_completion",
                message_handler=self.handle_order_completed
            )
            consumer.start_consuming()
        
        # Start consumers in separate threads
        threading.Thread(target=start_order_consumer, daemon=True).start()
        threading.Thread(target=start_payment_consumer, daemon=True).start()
        threading.Thread(target=start_completion_consumer, daemon=True).start()
        
        self.running = True
        logger.info("Inventory service consumers started")
    
    def _start_reservation_cleanup(self):
        """Start background thread to clean up expired reservations"""
        def cleanup_expired_reservations():
            while self.running:
                try:
                    current_time = datetime.utcnow()
                    expired_reservations = []
                    
                    for reservation_id, reservation in self.reservations.items():
                        if reservation['status'] == 'active':
                            expires_at = datetime.fromisoformat(reservation['expires_at'])
                            if current_time > expires_at:
                                expired_reservations.append(reservation_id)
                    
                    for reservation_id in expired_reservations:
                        self.release_reservation(reservation_id, 'Reservation expired')
                        logger.info("Expired reservation cleaned up", reservation_id=reservation_id)
                    
                    time.sleep(60)  # Check every minute
                    
                except Exception as e:
                    logger.error("Error in reservation cleanup", error=str(e))
                    time.sleep(60)
        
        threading.Thread(target=cleanup_expired_reservations, daemon=True).start()
        logger.info("Reservation cleanup thread started")
    
    def stop(self):
        """Stop the service"""
        self.running = False
        self.connection_manager.close_connections()
        logger.info("Inventory service stopped")

# Flask web service for inventory management
app = Flask(__name__)

# Configure CORS for Vercel frontend integration
cors_origins = Config.get_cors_origins()
CORS(app, 
     origins=cors_origins,
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With', 'Accept', 'Origin'],
     supports_credentials=True)

inventory_service = InventoryService()

@app.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint"""
    try:
        from health_utils import create_standard_health_endpoint
        
        # Create health status with custom checks
        def check_inventory_service_state():
            return {
                'healthy': inventory_service.running,
                'total_products': len(inventory_service.inventory),
                'active_reservations': len(inventory_service.reservations),
                'consumer_running': inventory_service.running
            }
        
        health_status = create_standard_health_endpoint(
            'inventory_service',
            custom_checks=[
                {'name': 'service_state', 'check_func': check_inventory_service_state}
            ]
        )
        
        status = health_status.get_health_status()
        http_status = 200 if status['overall_healthy'] else 503
        
        return jsonify(status), http_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return jsonify({
            'status': 'unhealthy',
            'service': 'inventory_service',
            'error': str(e)
        }), 503

@app.route('/inventory', methods=['GET'])
def get_all_inventory():
    """Get all inventory"""
    inventory = inventory_service.get_all_inventory()
    return jsonify({'inventory': inventory})

@app.route('/inventory/<product_id>', methods=['GET'])
def get_product_inventory(product_id):
    """Get inventory for a specific product"""
    product = inventory_service.get_product_inventory(product_id)
    
    if product:
        return jsonify(product)
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/inventory/<product_id>', methods=['PUT'])
def update_inventory(product_id):
    """Update inventory quantity for a product"""
    try:
        data = request.get_json()
        quantity = data.get('quantity')
        
        if quantity is None or quantity < 0:
            return jsonify({'error': 'Invalid quantity'}), 400
        
        success = inventory_service.update_inventory(product_id, quantity)
        
        if success:
            return jsonify({'success': True, 'product_id': product_id, 'quantity': quantity})
        else:
            return jsonify({'error': 'Product not found'}), 404
            
    except Exception as e:
        logger.error("Error in update_inventory endpoint", error=str(e))
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/reservations', methods=['POST'])
def create_reservation():
    """Create an inventory reservation"""
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        items = data.get('items', [])
        
        if not order_id or not items:
            return jsonify({'error': 'Missing order_id or items'}), 400
        
        result = inventory_service.reserve_inventory(order_id, items)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error("Error in create_reservation endpoint", error=str(e))
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/reservations/<reservation_id>/release', methods=['POST'])
def release_reservation(reservation_id):
    """Release an inventory reservation"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'Manual release')
        
        success = inventory_service.release_reservation(reservation_id, reason)
        
        if success:
            return jsonify({'success': True, 'reservation_id': reservation_id})
        else:
            return jsonify({'error': 'Reservation not found or already released'}), 404
            
    except Exception as e:
        logger.error("Error in release_reservation endpoint", error=str(e))
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get service metrics"""
    metrics = inventory_service.get_metrics()
    return jsonify(metrics)

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        logger.info("Starting Inventory Service", port=Config.INVENTORY_SERVICE_PORT)
        app.run(host='0.0.0.0', port=Config.INVENTORY_SERVICE_PORT, debug=False)
    except KeyboardInterrupt:
        logger.info("Shutting down Inventory Service")
        inventory_service.stop()
    except Exception as e:
        logger.error("Error starting Inventory Service", error=str(e))
        inventory_service.stop()