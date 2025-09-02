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

class NotificationService:
    """Notification Service handles customer notifications"""
    
    def __init__(self):
        self.connection_manager = KafkaConnectionManager()
        self.producer = MessageProducer(self.connection_manager)
        self.notifications = {}  # In-memory notification storage
        self.notification_templates = {}
        self.running = False
        
        # Initialize notification templates
        self._initialize_templates()
        
        # Start consumers for notification events
        self._start_consumers()
    
    def _initialize_templates(self):
        """Initialize notification templates"""
        self.notification_templates = {
            'order_created': {
                'subject': 'Order Confirmation - Order #{order_id}',
                'template': '''
                Dear {customer_name},
                
                Thank you for your order! We have received your order and are processing it.
                
                Order Details:
                Order ID: {order_id}
                Total Amount: ${total_amount:.2f}
                Items: {items_summary}
                
                We will send you another notification once your order is shipped.
                
                Best regards,
                E-Commerce Team
                '''
            },
            'payment_completed': {
                'subject': 'Payment Confirmed - Order #{order_id}',
                'template': '''
                Dear {customer_name},
                
                Your payment has been successfully processed!
                
                Payment Details:
                Order ID: {order_id}
                Amount: ${amount:.2f}
                Payment Method: {payment_method}
                Payment ID: {payment_id}
                
                Your order is now being prepared for shipment.
                
                Best regards,
                E-Commerce Team
                '''
            },
            'payment_failed': {
                'subject': 'Payment Failed - Order #{order_id}',
                'template': '''
                Dear {customer_name},
                
                We were unable to process your payment for order #{order_id}.
                
                Reason: {failure_reason}
                Amount: ${amount:.2f}
                
                Please try again with a different payment method or contact our support team.
                Your order has been cancelled and any reserved items have been released.
                
                Best regards,
                E-Commerce Team
                '''
            },
            'inventory_reserved': {
                'subject': 'Items Reserved - Order #{order_id}',
                'template': '''
                Dear {customer_name},
                
                Great news! We have reserved all items in your order.
                
                Order ID: {order_id}
                Reserved Items: {items_summary}
                
                Please complete your payment to secure these items.
                
                Best regards,
                E-Commerce Team
                '''
            },
            'inventory_shortage': {
                'subject': 'Item Unavailable - Order #{order_id}',
                'template': '''
                Dear {customer_name},
                
                We apologize, but some items in your order are currently out of stock.
                
                Order ID: {order_id}
                Unavailable Items: {unavailable_items}
                
                Your order has been cancelled and any payment will be refunded.
                We will notify you when these items are back in stock.
                
                Best regards,
                E-Commerce Team
                '''
            },
            'order_completed': {
                'subject': 'Order Shipped - Order #{order_id}',
                'template': '''
                Dear {customer_name},
                
                Excellent news! Your order has been completed and shipped.
                
                Order Details:
                Order ID: {order_id}
                Total Amount: ${total_amount:.2f}
                Items: {items_summary}
                
                You should receive your items within 3-5 business days.
                
                Thank you for shopping with us!
                
                Best regards,
                E-Commerce Team
                '''
            },
            'order_failed': {
                'subject': 'Order Cancelled - Order #{order_id}',
                'template': '''
                Dear {customer_name},
                
                We regret to inform you that your order has been cancelled.
                
                Order ID: {order_id}
                Reason: {failure_reason}
                
                Any payment made will be refunded within 3-5 business days.
                
                We apologize for any inconvenience caused.
                
                Best regards,
                E-Commerce Team
                '''
            }
        }
        
        logger.info("Notification templates initialized", template_count=len(self.notification_templates))
    
    def send_notification(self, notification_type: str, recipient: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a notification"""
        try:
            notification_id = str(uuid.uuid4())
            
            # Get template
            template = self.notification_templates.get(notification_type)
            if not template:
                logger.error("Unknown notification type", notification_type=notification_type)
                return {
                    'success': False,
                    'error': f'Unknown notification type: {notification_type}'
                }
            
            # Prepare notification data
            notification_data = {
                'customer_name': data.get('customer_name', 'Valued Customer'),
                'order_id': data.get('order_id', 'N/A'),
                'total_amount': data.get('total_amount', 0),
                'amount': data.get('amount', 0),
                'payment_method': data.get('payment_method', 'N/A'),
                'payment_id': data.get('payment_id', 'N/A'),
                'failure_reason': data.get('failure_reason', 'Unknown error'),
                'items_summary': self._format_items_summary(data.get('items', [])),
                'unavailable_items': self._format_unavailable_items(data.get('insufficient_items', []))
            }
            
            # Format subject and content
            subject = template['subject'].format(**notification_data)
            content = template['template'].format(**notification_data)
            
            # Create notification record
            notification = {
                'notification_id': notification_id,
                'type': notification_type,
                'recipient': recipient,
                'subject': subject,
                'content': content,
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat(),
                'data': data
            }
            
            # Store notification
            self.notifications[notification_id] = notification
            
            # Simulate sending notification (in production, integrate with email service)
            success = self._simulate_send_notification(notification)
            
            if success:
                notification['status'] = 'sent'
                notification['sent_at'] = datetime.utcnow().isoformat()
                
                logger.info(
                    "Notification sent successfully",
                    notification_id=notification_id,
                    type=notification_type,
                    recipient=recipient
                )
                
                return {
                    'success': True,
                    'notification_id': notification_id,
                    'status': 'sent'
                }
            else:
                notification['status'] = 'failed'
                notification['failed_at'] = datetime.utcnow().isoformat()
                notification['failure_reason'] = 'Delivery failed'
                
                logger.error(
                    "Notification delivery failed",
                    notification_id=notification_id,
                    type=notification_type,
                    recipient=recipient
                )
                
                return {
                    'success': False,
                    'notification_id': notification_id,
                    'error': 'Notification delivery failed'
                }
                
        except Exception as e:
            logger.error("Error sending notification", notification_type=notification_type, error=str(e))
            return {
                'success': False,
                'error': 'Notification processing error'
            }
    
    def _simulate_send_notification(self, notification: Dict[str, Any]) -> bool:
        """Simulate sending notification (replace with actual email service integration)"""
        # Simulate processing time
        time.sleep(0.1)
        
        # Simulate 95% success rate
        import random
        success = random.random() < 0.95
        
        if success:
            # In production, this would integrate with email service like SendGrid, AWS SES, etc.
            logger.info(
                "[SIMULATED EMAIL SENT]",
                to=notification['recipient'],
                subject=notification['subject'],
                content_preview=notification['content'][:100] + "..."
            )
        
        return success
    
    def _format_items_summary(self, items: List[Dict[str, Any]]) -> str:
        """Format items list for notification"""
        if not items:
            return "No items"
        
        summary = []
        for item in items:
            product_id = item.get('product_id', 'Unknown')
            quantity = item.get('quantity', 0)
            price = item.get('price', 0)
            summary.append(f"- {product_id} (Qty: {quantity}, Price: ${price:.2f})")
        
        return "\n".join(summary)
    
    def _format_unavailable_items(self, insufficient_items: List[Dict[str, Any]]) -> str:
        """Format unavailable items for notification"""
        if not insufficient_items:
            return "None"
        
        summary = []
        for item in insufficient_items:
            product_id = item.get('product_id', 'Unknown')
            requested = item.get('requested', 0)
            available = item.get('available', 0)
            reason = item.get('reason', 'Unknown')
            summary.append(f"- {product_id} (Requested: {requested}, Available: {available}, Reason: {reason})")
        
        return "\n".join(summary)
    
    def handle_order_created(self, message: Dict[str, Any]) -> bool:
        """Handle order created event"""
        try:
            customer_id = message.get('customer_id')
            recipient = f"{customer_id}@example.com"  # In production, lookup actual email
            
            result = self.send_notification('order_created', recipient, message)
            return result['success']
            
        except Exception as e:
            logger.error("Error handling order created event", error=str(e))
            return False
    
    def handle_payment_completed(self, message: Dict[str, Any]) -> bool:
        """Handle payment completed event"""
        try:
            # Extract customer info from order (in production, lookup from order service)
            order_id = message.get('order_id')
            customer_id = f"customer_{order_id.split('-')[0]}"  # Simplified for demo
            recipient = f"{customer_id}@example.com"
            
            result = self.send_notification('payment_completed', recipient, message)
            return result['success']
            
        except Exception as e:
            logger.error("Error handling payment completed event", error=str(e))
            return False
    
    def handle_payment_failed(self, message: Dict[str, Any]) -> bool:
        """Handle payment failed event"""
        try:
            order_id = message.get('order_id')
            customer_id = f"customer_{order_id.split('-')[0]}"  # Simplified for demo
            recipient = f"{customer_id}@example.com"
            
            result = self.send_notification('payment_failed', recipient, message)
            return result['success']
            
        except Exception as e:
            logger.error("Error handling payment failed event", error=str(e))
            return False
    
    def handle_inventory_reserved(self, message: Dict[str, Any]) -> bool:
        """Handle inventory reserved event"""
        try:
            order_id = message.get('order_id')
            customer_id = f"customer_{order_id.split('-')[0]}"  # Simplified for demo
            recipient = f"{customer_id}@example.com"
            
            result = self.send_notification('inventory_reserved', recipient, message)
            return result['success']
            
        except Exception as e:
            logger.error("Error handling inventory reserved event", error=str(e))
            return False
    
    def handle_inventory_released(self, message: Dict[str, Any]) -> bool:
        """Handle inventory released event"""
        try:
            # Only send notification if it's due to shortage
            if message.get('reason') == 'insufficient_inventory':
                order_id = message.get('order_id')
                customer_id = f"customer_{order_id.split('-')[0]}"  # Simplified for demo
                recipient = f"{customer_id}@example.com"
                
                result = self.send_notification('inventory_shortage', recipient, message)
                return result['success']
            
            return True  # No notification needed for other release reasons
            
        except Exception as e:
            logger.error("Error handling inventory released event", error=str(e))
            return False
    
    def handle_order_completed(self, message: Dict[str, Any]) -> bool:
        """Handle order completed event"""
        try:
            order_id = message.get('order_id')
            customer_id = f"customer_{order_id.split('-')[0]}"  # Simplified for demo
            recipient = f"{customer_id}@example.com"
            
            result = self.send_notification('order_completed', recipient, message)
            return result['success']
            
        except Exception as e:
            logger.error("Error handling order completed event", error=str(e))
            return False
    
    def handle_order_failed(self, message: Dict[str, Any]) -> bool:
        """Handle order failed event"""
        try:
            order_id = message.get('order_id')
            customer_id = f"customer_{order_id.split('-')[0]}"  # Simplified for demo
            recipient = f"{customer_id}@example.com"
            
            result = self.send_notification('order_failed', recipient, message)
            return result['success']
            
        except Exception as e:
            logger.error("Error handling order failed event", error=str(e))
            return False
    
    def get_notification(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """Get notification by ID"""
        return self.notifications.get(notification_id)
    
    def get_notifications_by_recipient(self, recipient: str) -> List[Dict[str, Any]]:
        """Get all notifications for a recipient"""
        return [notif for notif in self.notifications.values() if notif['recipient'] == recipient]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        total_notifications = len(self.notifications)
        status_counts = {}
        type_counts = {}
        
        for notification in self.notifications.values():
            status = notification['status']
            notif_type = notification['type']
            
            status_counts[status] = status_counts.get(status, 0) + 1
            type_counts[notif_type] = type_counts.get(notif_type, 0) + 1
        
        success_rate = (status_counts.get('sent', 0) / total_notifications * 100) if total_notifications > 0 else 0
        
        producer_metrics = self.producer.get_metrics()
        
        return {
            'total_notifications': total_notifications,
            'status_distribution': status_counts,
            'type_distribution': type_counts,
            'success_rate': round(success_rate, 2),
            'available_templates': list(self.notification_templates.keys()),
            'producer_metrics': producer_metrics
        }
    
    def _start_consumers(self):
        """Start Kafka consumers for notification events"""
        def start_order_consumer():
            consumer = MessageConsumer(
                connection_manager=self.connection_manager,
                topics=[Config.TOPICS['ORDERS_CREATED']],
                group_id=Config.CONSUMER_GROUPS['NOTIFICATION_SERVICE'],
                message_handler=self.handle_order_created
            )
            consumer.start_consuming()
        
        def start_payment_consumer():
            consumer = MessageConsumer(
                connection_manager=self.connection_manager,
                topics=[Config.TOPICS['PAYMENTS_COMPLETED'], Config.TOPICS['PAYMENTS_FAILED']],
                group_id=f"{Config.CONSUMER_GROUPS['NOTIFICATION_SERVICE']}_payment",
                message_handler=self._handle_payment_events
            )
            consumer.start_consuming()
        
        def start_inventory_consumer():
            consumer = MessageConsumer(
                connection_manager=self.connection_manager,
                topics=[Config.TOPICS['INVENTORY_RESERVED'], Config.TOPICS['INVENTORY_RELEASED']],
                group_id=f"{Config.CONSUMER_GROUPS['NOTIFICATION_SERVICE']}_inventory",
                message_handler=self._handle_inventory_events
            )
            consumer.start_consuming()
        
        def start_completion_consumer():
            consumer = MessageConsumer(
                connection_manager=self.connection_manager,
                topics=[Config.TOPICS['ORDERS_COMPLETED'], Config.TOPICS['ORDERS_FAILED']],
                group_id=f"{Config.CONSUMER_GROUPS['NOTIFICATION_SERVICE']}_completion",
                message_handler=self._handle_order_completion_events
            )
            consumer.start_consuming()
        
        # Start consumers in separate threads
        threading.Thread(target=start_order_consumer, daemon=True).start()
        threading.Thread(target=start_payment_consumer, daemon=True).start()
        threading.Thread(target=start_inventory_consumer, daemon=True).start()
        threading.Thread(target=start_completion_consumer, daemon=True).start()
        
        self.running = True
        logger.info("Notification service consumers started")
    
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
    
    def _handle_inventory_events(self, message: Dict[str, Any]) -> bool:
        """Route inventory events to appropriate handlers"""
        status = message.get('status')
        
        if status == 'reserved':
            return self.handle_inventory_reserved(message)
        elif status in ['released', 'failed']:
            return self.handle_inventory_released(message)
        else:
            logger.warning("Unknown inventory status", status=status)
            return True
    
    def _handle_order_completion_events(self, message: Dict[str, Any]) -> bool:
        """Route order completion events to appropriate handlers"""
        # Determine if this is from orders.completed or orders.failed topic
        if message.get('status') == 'completed' or 'completed_at' in message:
            return self.handle_order_completed(message)
        else:
            return self.handle_order_failed(message)
    
    def stop(self):
        """Stop the service"""
        self.running = False
        self.connection_manager.close_connections()
        logger.info("Notification service stopped")

# Flask web service for notification management
app = Flask(__name__)

# Configure CORS for Vercel frontend integration
cors_origins = Config.get_cors_origins()
CORS(app, 
     origins=cors_origins,
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With', 'Accept', 'Origin'],
     supports_credentials=True)

notification_service = NotificationService()

@app.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint"""
    try:
        from health_utils import create_standard_health_endpoint
        
        # Create health status with custom checks
        def check_notification_service_state():
            return {
                'healthy': notification_service.running,
                'total_notifications': len(notification_service.notifications),
                'consumer_running': notification_service.running
            }
        
        health_status = create_standard_health_endpoint(
            'notification_service',
            custom_checks=[
                {'name': 'service_state', 'check_func': check_notification_service_state}
            ]
        )
        
        status = health_status.get_health_status()
        http_status = 200 if status['overall_healthy'] else 503
        
        return jsonify(status), http_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return jsonify({
            'status': 'unhealthy',
            'service': 'notification_service',
            'error': str(e)
        }), 503

@app.route('/notifications', methods=['POST'])
def send_notification():
    """Send a notification"""
    try:
        data = request.get_json()
        
        notification_type = data.get('type')
        recipient = data.get('recipient')
        notification_data = data.get('data', {})
        
        if not notification_type or not recipient:
            return jsonify({'error': 'Missing type or recipient'}), 400
        
        result = notification_service.send_notification(notification_type, recipient, notification_data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error("Error in send_notification endpoint", error=str(e))
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/notifications/<notification_id>', methods=['GET'])
def get_notification(notification_id):
    """Get notification by ID"""
    notification = notification_service.get_notification(notification_id)
    
    if notification:
        return jsonify(notification)
    else:
        return jsonify({'error': 'Notification not found'}), 404

@app.route('/recipients/<recipient>/notifications', methods=['GET'])
def get_recipient_notifications(recipient):
    """Get all notifications for a recipient"""
    notifications = notification_service.get_notifications_by_recipient(recipient)
    return jsonify({'notifications': notifications})

@app.route('/templates', methods=['GET'])
def get_templates():
    """Get available notification templates"""
    templates = notification_service.notification_templates
    return jsonify({'templates': list(templates.keys())})

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get service metrics"""
    metrics = notification_service.get_metrics()
    return jsonify(metrics)

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        logger.info("Starting Notification Service", port=Config.NOTIFICATION_SERVICE_PORT)
        app.run(host='0.0.0.0', port=Config.NOTIFICATION_SERVICE_PORT, debug=False)
    except KeyboardInterrupt:
        logger.info("Shutting down Notification Service")
        notification_service.stop()
    except Exception as e:
        logger.error("Error starting Notification Service", error=str(e))
        notification_service.stop()