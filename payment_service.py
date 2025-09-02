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

class PaymentService:
    """Payment Service handles payment processing and state management"""
    
    def __init__(self):
        self.connection_manager = KafkaConnectionManager()
        self.producer = MessageProducer(self.connection_manager)
        self.payments = {}  # In-memory payment storage
        self.running = False
        
        # Payment methods and their success rates (for simulation)
        self.payment_methods = {
            'credit_card': 0.95,  # 95% success rate
            'debit_card': 0.98,   # 98% success rate
            'paypal': 0.92,       # 92% success rate
            'bank_transfer': 0.99, # 99% success rate
            'crypto': 0.85        # 85% success rate
        }
        
        # Start consumer for payment requests
        self._start_consumers()
    
    def process_payment(self, payment_request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a payment request"""
        try:
            order_id = payment_request['order_id']
            amount = payment_request['amount']
            payment_method = payment_request.get('payment_method', 'credit_card')
            
            # Generate payment ID
            payment_id = str(uuid.uuid4())
            
            # Create payment record
            payment = {
                'payment_id': payment_id,
                'order_id': order_id,
                'amount': amount,
                'payment_method': payment_method,
                'status': 'processing',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Store payment
            self.payments[payment_id] = payment
            
            logger.info("Payment processing started", payment_id=payment_id, order_id=order_id, amount=amount)
            
            # Simulate payment processing
            success = self._simulate_payment_processing(payment_method, amount)
            
            if success:
                # Payment successful
                payment['status'] = 'completed'
                payment['completed_at'] = datetime.utcnow().isoformat()
                payment['updated_at'] = datetime.utcnow().isoformat()
                
                # Publish payment completed event
                self.producer.send_message(
                    topic=Config.TOPICS['PAYMENTS_COMPLETED'],
                    message=payment,
                    key=order_id
                )
                
                logger.info("Payment completed successfully", payment_id=payment_id, order_id=order_id)
                
                return {
                    'success': True,
                    'payment_id': payment_id,
                    'status': 'completed',
                    'amount': amount
                }
            else:
                # Payment failed
                failure_reason = self._get_failure_reason(payment_method)
                payment['status'] = 'failed'
                payment['failure_reason'] = failure_reason
                payment['failed_at'] = datetime.utcnow().isoformat()
                payment['updated_at'] = datetime.utcnow().isoformat()
                
                # Publish payment failed event
                self.producer.send_message(
                    topic=Config.TOPICS['PAYMENTS_FAILED'],
                    message=payment,
                    key=order_id
                )
                
                logger.error("Payment failed", payment_id=payment_id, order_id=order_id, reason=failure_reason)
                
                return {
                    'success': False,
                    'payment_id': payment_id,
                    'status': 'failed',
                    'failure_reason': failure_reason
                }
                
        except Exception as e:
            logger.error("Error processing payment", error=str(e))
            return {
                'success': False,
                'error': 'Payment processing error'
            }
    
    def handle_payment_request(self, message: Dict[str, Any]) -> bool:
        """Handle payment request from Kafka"""
        try:
            order_id = message['order_id']
            amount = message['amount']
            payment_method = message.get('payment_method', 'credit_card')
            
            # Process the payment
            result = self.process_payment({
                'order_id': order_id,
                'amount': amount,
                'payment_method': payment_method
            })
            
            return result['success']
            
        except Exception as e:
            logger.error("Error handling payment request", error=str(e))
            return False
    
    def refund_payment(self, payment_id: str, reason: str = 'Order cancelled') -> Dict[str, Any]:
        """Process a payment refund"""
        try:
            if payment_id not in self.payments:
                return {
                    'success': False,
                    'error': 'Payment not found'
                }
            
            payment = self.payments[payment_id]
            
            if payment['status'] != 'completed':
                return {
                    'success': False,
                    'error': 'Payment not eligible for refund'
                }
            
            # Generate refund ID
            refund_id = str(uuid.uuid4())
            
            # Create refund record
            refund = {
                'refund_id': refund_id,
                'payment_id': payment_id,
                'order_id': payment['order_id'],
                'amount': payment['amount'],
                'reason': reason,
                'status': 'processing',
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Simulate refund processing (always successful for demo)
            refund['status'] = 'completed'
            refund['completed_at'] = datetime.utcnow().isoformat()
            
            # Update payment status
            payment['status'] = 'refunded'
            payment['refund_id'] = refund_id
            payment['updated_at'] = datetime.utcnow().isoformat()
            
            logger.info("Refund processed successfully", refund_id=refund_id, payment_id=payment_id)
            
            return {
                'success': True,
                'refund_id': refund_id,
                'amount': refund['amount'],
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error("Error processing refund", payment_id=payment_id, error=str(e))
            return {
                'success': False,
                'error': 'Refund processing error'
            }
    
    def _simulate_payment_processing(self, payment_method: str, amount: float) -> bool:
        """Simulate payment processing with realistic success rates"""
        # Add some processing delay
        time.sleep(random.uniform(0.5, 2.0))
        
        # Get success rate for payment method
        success_rate = self.payment_methods.get(payment_method, 0.90)
        
        # Reduce success rate for high amounts (simulate fraud detection)
        if amount > 1000:
            success_rate *= 0.9
        elif amount > 5000:
            success_rate *= 0.8
        
        # Random success/failure based on success rate
        return random.random() < success_rate
    
    def _get_failure_reason(self, payment_method: str) -> str:
        """Get a realistic failure reason based on payment method"""
        failure_reasons = {
            'credit_card': [
                'Insufficient funds',
                'Card expired',
                'Invalid CVV',
                'Card blocked by issuer',
                'Transaction declined by bank'
            ],
            'debit_card': [
                'Insufficient funds',
                'Card expired',
                'Daily limit exceeded',
                'Card blocked'
            ],
            'paypal': [
                'PayPal account suspended',
                'Insufficient PayPal balance',
                'Payment method not verified',
                'Transaction limit exceeded'
            ],
            'bank_transfer': [
                'Account not found',
                'Insufficient funds',
                'Transfer limit exceeded',
                'Bank system unavailable'
            ],
            'crypto': [
                'Insufficient wallet balance',
                'Network congestion',
                'Invalid wallet address',
                'Transaction fee too low'
            ]
        }
        
        reasons = failure_reasons.get(payment_method, ['Payment processing failed'])
        return random.choice(reasons)
    
    def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Get payment by ID"""
        return self.payments.get(payment_id)
    
    def get_payments_by_order(self, order_id: str) -> List[Dict[str, Any]]:
        """Get all payments for an order"""
        return [payment for payment in self.payments.values() if payment['order_id'] == order_id]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        total_payments = len(self.payments)
        status_counts = {}
        method_counts = {}
        total_amount = 0
        
        for payment in self.payments.values():
            status = payment['status']
            method = payment['payment_method']
            amount = payment['amount']
            
            status_counts[status] = status_counts.get(status, 0) + 1
            method_counts[method] = method_counts.get(method, 0) + 1
            
            if status == 'completed':
                total_amount += amount
        
        success_rate = (status_counts.get('completed', 0) / total_payments * 100) if total_payments > 0 else 0
        
        producer_metrics = self.producer.get_metrics()
        
        return {
            'total_payments': total_payments,
            'status_distribution': status_counts,
            'payment_method_distribution': method_counts,
            'total_amount_processed': total_amount,
            'success_rate': round(success_rate, 2),
            'producer_metrics': producer_metrics
        }
    
    def _start_consumers(self):
        """Start Kafka consumers for payment requests"""
        def start_payment_request_consumer():
            consumer = MessageConsumer(
                connection_manager=self.connection_manager,
                topics=[Config.TOPICS['PAYMENTS_REQUESTED']],
                group_id=Config.CONSUMER_GROUPS['PAYMENT_SERVICE'],
                message_handler=self.handle_payment_request
            )
            consumer.start_consuming()
        
        # Start consumer in separate thread
        threading.Thread(target=start_payment_request_consumer, daemon=True).start()
        
        self.running = True
        logger.info("Payment service consumers started")
    
    def stop(self):
        """Stop the service"""
        self.running = False
        self.connection_manager.close_connections()
        logger.info("Payment service stopped")

# Flask web service for payment management
app = Flask(__name__)

# Configure CORS for Vercel frontend integration
cors_origins = Config.get_cors_origins()
CORS(app, 
     origins=cors_origins,
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With', 'Accept', 'Origin'],
     supports_credentials=True)

payment_service = PaymentService()

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'service': 'payment_service',
            'running': payment_service.running,
            'total_payments': len(payment_service.payments),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return jsonify({
            'status': 'unhealthy',
            'service': 'payment_service',
            'error': str(e)
        }), 503

@app.route('/payments', methods=['POST'])
def process_payment():
    """Process a payment"""
    try:
        payment_data = request.get_json()
        
        # Validate required fields
        required_fields = ['order_id', 'amount']
        for field in required_fields:
            if field not in payment_data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        result = payment_service.process_payment(payment_data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error("Error in process_payment endpoint", error=str(e))
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/payments/<payment_id>', methods=['GET'])
def get_payment(payment_id):
    """Get payment by ID"""
    payment = payment_service.get_payment(payment_id)
    
    if payment:
        return jsonify(payment)
    else:
        return jsonify({'error': 'Payment not found'}), 404

@app.route('/orders/<order_id>/payments', methods=['GET'])
def get_order_payments(order_id):
    """Get all payments for an order"""
    payments = payment_service.get_payments_by_order(order_id)
    return jsonify({'payments': payments})

@app.route('/payments/<payment_id>/refund', methods=['POST'])
def refund_payment(payment_id):
    """Process a payment refund"""
    try:
        refund_data = request.get_json() or {}
        reason = refund_data.get('reason', 'Order cancelled')
        
        result = payment_service.refund_payment(payment_id, reason)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error("Error in refund_payment endpoint", error=str(e))
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get service metrics"""
    metrics = payment_service.get_metrics()
    return jsonify(metrics)

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        logger.info("Starting Payment Service", port=Config.PAYMENT_SERVICE_PORT)
        app.run(host='0.0.0.0', port=Config.PAYMENT_SERVICE_PORT, debug=False)
    except KeyboardInterrupt:
        logger.info("Shutting down Payment Service")
        payment_service.stop()
    except Exception as e:
        logger.error("Error starting Payment Service", error=str(e))
        payment_service.stop()