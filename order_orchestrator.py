import json
import uuid
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
import structlog
from config import Config
from kafka_utils import KafkaConnectionManager, MessageProducer, MessageConsumer

# Setup structured logging
logger = structlog.get_logger(__name__)

class OrderOrchestrator:
    """Order Orchestrator coordinates the entire order processing flow"""
    
    def __init__(self):
        self.connection_manager = KafkaConnectionManager()
        self.producer = MessageProducer(self.connection_manager)
        self.order_flows = {}  # Track order processing flows
        self.running = False
        
        # Order flow states
        self.flow_states = {
            'CREATED': 'created',
            'VALIDATING': 'validating',
            'VALIDATED': 'validated',
            'RESERVING_INVENTORY': 'reserving_inventory',
            'INVENTORY_RESERVED': 'inventory_reserved',
            'PROCESSING_PAYMENT': 'processing_payment',
            'PAYMENT_COMPLETED': 'payment_completed',
            'COMPLETING_ORDER': 'completing_order',
            'COMPLETED': 'completed',
            'FAILED': 'failed',
            'CANCELLED': 'cancelled'
        }
        
        # Start consumers for orchestration events
        self._start_consumers()
        
        # Start flow monitoring
        self._start_flow_monitoring()
    
    def start_order_flow(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new order processing flow"""
        try:
            order_id = order_data['order_id']
            
            # Create order flow record
            flow = {
                'order_id': order_id,
                'customer_id': order_data['customer_id'],
                'items': order_data['items'],
                'total_amount': order_data['total_amount'],
                'state': self.flow_states['CREATED'],
                'steps_completed': [],
                'steps_failed': [],
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'timeout_at': (datetime.utcnow() + timedelta(minutes=Config.ORDER_PROCESSING_TIMEOUT // 60)).isoformat(),
                'metadata': {
                    'payment_id': None,
                    'reservation_id': None,
                    'failure_reason': None,
                    'retry_count': 0
                }
            }
            
            self.order_flows[order_id] = flow
            
            # Start validation step
            self._transition_to_validation(order_id)
            
            logger.info("Order flow started", order_id=order_id, customer_id=order_data['customer_id'])
            
            return {
                'success': True,
                'order_id': order_id,
                'flow_state': flow['state']
            }
            
        except Exception as e:
            logger.error("Error starting order flow", error=str(e))
            return {
                'success': False,
                'error': 'Failed to start order flow'
            }
    
    def _transition_to_validation(self, order_id: str):
        """Transition order to validation step"""
        try:
            flow = self.order_flows[order_id]
            flow['state'] = self.flow_states['VALIDATING']
            flow['updated_at'] = datetime.utcnow().isoformat()
            
            # Trigger order validation (order service will handle this)
            logger.info("Order validation initiated", order_id=order_id)
            
        except Exception as e:
            logger.error("Error transitioning to validation", order_id=order_id, error=str(e))
            self._handle_flow_failure(order_id, "validation_transition_failed")
    
    def handle_order_validated(self, message: Dict[str, Any]) -> bool:
        """Handle order validated event"""
        try:
            order_id = message['order_id']
            
            if order_id not in self.order_flows:
                logger.warning("Order flow not found", order_id=order_id)
                return True
            
            flow = self.order_flows[order_id]
            
            if flow['state'] != self.flow_states['VALIDATING']:
                logger.warning("Unexpected state for validation", order_id=order_id, current_state=flow['state'])
                return True
            
            # Update flow state
            flow['state'] = self.flow_states['VALIDATED']
            flow['steps_completed'].append('validation')
            flow['updated_at'] = datetime.utcnow().isoformat()
            
            # Transition to inventory reservation
            self._transition_to_inventory_reservation(order_id)
            
            logger.info("Order validation completed", order_id=order_id)
            return True
            
        except Exception as e:
            logger.error("Error handling order validated event", error=str(e))
            return False
    
    def _transition_to_inventory_reservation(self, order_id: str):
        """Transition to inventory reservation step"""
        try:
            flow = self.order_flows[order_id]
            flow['state'] = self.flow_states['RESERVING_INVENTORY']
            flow['updated_at'] = datetime.utcnow().isoformat()
            
            # Inventory service will handle reservation automatically via order.validated event
            logger.info("Inventory reservation initiated", order_id=order_id)
            
        except Exception as e:
            logger.error("Error transitioning to inventory reservation", order_id=order_id, error=str(e))
            self._handle_flow_failure(order_id, "inventory_reservation_transition_failed")
    
    def handle_inventory_reserved(self, message: Dict[str, Any]) -> bool:
        """Handle inventory reserved event"""
        try:
            order_id = message['order_id']
            reservation_id = message.get('reservation_id')
            
            if order_id not in self.order_flows:
                logger.warning("Order flow not found", order_id=order_id)
                return True
            
            flow = self.order_flows[order_id]
            
            if flow['state'] != self.flow_states['RESERVING_INVENTORY']:
                logger.warning("Unexpected state for inventory reservation", order_id=order_id, current_state=flow['state'])
                return True
            
            # Update flow state
            flow['state'] = self.flow_states['INVENTORY_RESERVED']
            flow['steps_completed'].append('inventory_reservation')
            flow['metadata']['reservation_id'] = reservation_id
            flow['updated_at'] = datetime.utcnow().isoformat()
            
            # Transition to payment processing
            self._transition_to_payment_processing(order_id)
            
            logger.info("Inventory reservation completed", order_id=order_id, reservation_id=reservation_id)
            return True
            
        except Exception as e:
            logger.error("Error handling inventory reserved event", error=str(e))
            return False
    
    def handle_inventory_released(self, message: Dict[str, Any]) -> bool:
        """Handle inventory released event (failure case)"""
        try:
            order_id = message['order_id']
            reason = message.get('reason', 'Unknown')
            
            if order_id not in self.order_flows:
                logger.warning("Order flow not found", order_id=order_id)
                return True
            
            flow = self.order_flows[order_id]
            
            # Only handle if this is a failure (insufficient inventory)
            if reason == 'insufficient_inventory':
                self._handle_flow_failure(order_id, f"inventory_shortage: {reason}")
            
            logger.info("Inventory released handled", order_id=order_id, reason=reason)
            return True
            
        except Exception as e:
            logger.error("Error handling inventory released event", error=str(e))
            return False
    
    def _transition_to_payment_processing(self, order_id: str):
        """Transition to payment processing step"""
        try:
            flow = self.order_flows[order_id]
            flow['state'] = self.flow_states['PROCESSING_PAYMENT']
            flow['updated_at'] = datetime.utcnow().isoformat()
            
            # Send payment request
            payment_request = {
                'order_id': order_id,
                'amount': flow['total_amount'],
                'payment_method': 'credit_card',  # Default payment method
                'customer_id': flow['customer_id']
            }
            
            self.producer.send_message(
                topic=Config.TOPICS['PAYMENTS_REQUESTED'],
                message=payment_request,
                key=order_id
            )
            
            logger.info("Payment processing initiated", order_id=order_id, amount=flow['total_amount'])
            
        except Exception as e:
            logger.error("Error transitioning to payment processing", order_id=order_id, error=str(e))
            self._handle_flow_failure(order_id, "payment_processing_transition_failed")
    
    def handle_payment_completed(self, message: Dict[str, Any]) -> bool:
        """Handle payment completed event"""
        try:
            order_id = message['order_id']
            payment_id = message.get('payment_id')
            
            if order_id not in self.order_flows:
                logger.warning("Order flow not found", order_id=order_id)
                return True
            
            flow = self.order_flows[order_id]
            
            if flow['state'] != self.flow_states['PROCESSING_PAYMENT']:
                logger.warning("Unexpected state for payment completion", order_id=order_id, current_state=flow['state'])
                return True
            
            # Update flow state
            flow['state'] = self.flow_states['PAYMENT_COMPLETED']
            flow['steps_completed'].append('payment')
            flow['metadata']['payment_id'] = payment_id
            flow['updated_at'] = datetime.utcnow().isoformat()
            
            # Transition to order completion
            self._transition_to_order_completion(order_id)
            
            logger.info("Payment completed", order_id=order_id, payment_id=payment_id)
            return True
            
        except Exception as e:
            logger.error("Error handling payment completed event", error=str(e))
            return False
    
    def handle_payment_failed(self, message: Dict[str, Any]) -> bool:
        """Handle payment failed event"""
        try:
            order_id = message['order_id']
            failure_reason = message.get('failure_reason', 'Payment processing failed')
            
            if order_id not in self.order_flows:
                logger.warning("Order flow not found", order_id=order_id)
                return True
            
            # Handle payment failure
            self._handle_flow_failure(order_id, f"payment_failed: {failure_reason}")
            
            logger.error("Payment failed", order_id=order_id, reason=failure_reason)
            return True
            
        except Exception as e:
            logger.error("Error handling payment failed event", error=str(e))
            return False
    
    def _transition_to_order_completion(self, order_id: str):
        """Transition to order completion step"""
        try:
            flow = self.order_flows[order_id]
            flow['state'] = self.flow_states['COMPLETING_ORDER']
            flow['updated_at'] = datetime.utcnow().isoformat()
            
            # Send order completion event
            completion_message = {
                'order_id': order_id,
                'customer_id': flow['customer_id'],
                'items': flow['items'],
                'total_amount': flow['total_amount'],
                'payment_id': flow['metadata']['payment_id'],
                'reservation_id': flow['metadata']['reservation_id'],
                'status': 'completed',
                'completed_at': datetime.utcnow().isoformat()
            }
            
            self.producer.send_message(
                topic=Config.TOPICS['ORDERS_COMPLETED'],
                message=completion_message,
                key=order_id
            )
            
            # Update flow to completed
            flow['state'] = self.flow_states['COMPLETED']
            flow['steps_completed'].append('completion')
            flow['completed_at'] = datetime.utcnow().isoformat()
            flow['updated_at'] = datetime.utcnow().isoformat()
            
            logger.info("Order completion initiated", order_id=order_id)
            
        except Exception as e:
            logger.error("Error transitioning to order completion", order_id=order_id, error=str(e))
            self._handle_flow_failure(order_id, "order_completion_transition_failed")
    
    def _handle_flow_failure(self, order_id: str, failure_reason: str):
        """Handle order flow failure"""
        try:
            if order_id not in self.order_flows:
                logger.warning("Order flow not found for failure handling", order_id=order_id)
                return
            
            flow = self.order_flows[order_id]
            flow['state'] = self.flow_states['FAILED']
            flow['metadata']['failure_reason'] = failure_reason
            flow['failed_at'] = datetime.utcnow().isoformat()
            flow['updated_at'] = datetime.utcnow().isoformat()
            
            # Send order failed event
            failure_message = {
                'order_id': order_id,
                'customer_id': flow['customer_id'],
                'items': flow['items'],
                'total_amount': flow['total_amount'],
                'failure_reason': failure_reason,
                'status': 'failed',
                'failed_at': datetime.utcnow().isoformat(),
                'steps_completed': flow['steps_completed']
            }
            
            self.producer.send_message(
                topic=Config.TOPICS['ORDERS_FAILED'],
                message=failure_message,
                key=order_id
            )
            
            logger.error("Order flow failed", order_id=order_id, reason=failure_reason)
            
        except Exception as e:
            logger.error("Error handling flow failure", order_id=order_id, error=str(e))
    
    def get_order_flow(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order flow by ID"""
        return self.order_flows.get(order_id)
    
    def get_flows_by_state(self, state: str) -> List[Dict[str, Any]]:
        """Get all flows in a specific state"""
        return [flow for flow in self.order_flows.values() if flow['state'] == state]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics"""
        total_flows = len(self.order_flows)
        state_counts = {}
        
        for flow in self.order_flows.values():
            state = flow['state']
            state_counts[state] = state_counts.get(state, 0) + 1
        
        # Calculate success rate
        completed = state_counts.get(self.flow_states['COMPLETED'], 0)
        failed = state_counts.get(self.flow_states['FAILED'], 0)
        success_rate = (completed / (completed + failed) * 100) if (completed + failed) > 0 else 0
        
        # Calculate average processing time for completed orders
        completed_flows = [f for f in self.order_flows.values() if f['state'] == self.flow_states['COMPLETED']]
        avg_processing_time = 0
        
        if completed_flows:
            total_time = 0
            for flow in completed_flows:
                created = datetime.fromisoformat(flow['created_at'])
                completed_at = datetime.fromisoformat(flow['completed_at'])
                processing_time = (completed_at - created).total_seconds()
                total_time += processing_time
            avg_processing_time = total_time / len(completed_flows)
        
        producer_metrics = self.producer.get_metrics()
        
        return {
            'total_flows': total_flows,
            'state_distribution': state_counts,
            'success_rate': round(success_rate, 2),
            'average_processing_time_seconds': round(avg_processing_time, 2),
            'producer_metrics': producer_metrics
        }
    
    def _start_consumers(self):
        """Start Kafka consumers for orchestration events"""
        def start_order_consumer():
            consumer = MessageConsumer(
                connection_manager=self.connection_manager,
                topics=[Config.TOPICS['ORDERS_CREATED'], Config.TOPICS['ORDERS_VALIDATED']],
                group_id=Config.CONSUMER_GROUPS['ORCHESTRATOR_SERVICE'],
                message_handler=self._handle_order_events
            )
            consumer.start_consuming()
        
        def start_inventory_consumer():
            consumer = MessageConsumer(
                connection_manager=self.connection_manager,
                topics=[Config.TOPICS['INVENTORY_RESERVED'], Config.TOPICS['INVENTORY_RELEASED']],
                group_id=f"{Config.CONSUMER_GROUPS['ORCHESTRATOR_SERVICE']}_inventory",
                message_handler=self._handle_inventory_events
            )
            consumer.start_consuming()
        
        def start_payment_consumer():
            consumer = MessageConsumer(
                connection_manager=self.connection_manager,
                topics=[Config.TOPICS['PAYMENTS_COMPLETED'], Config.TOPICS['PAYMENTS_FAILED']],
                group_id=f"{Config.CONSUMER_GROUPS['ORCHESTRATOR_SERVICE']}_payment",
                message_handler=self._handle_payment_events
            )
            consumer.start_consuming()
        
        # Start consumers in separate threads
        threading.Thread(target=start_order_consumer, daemon=True).start()
        threading.Thread(target=start_inventory_consumer, daemon=True).start()
        threading.Thread(target=start_payment_consumer, daemon=True).start()
        
        self.running = True
        logger.info("Order orchestrator consumers started")
    
    def _handle_order_events(self, message: Dict[str, Any]) -> bool:
        """Route order events to appropriate handlers"""
        status = message.get('status')
        
        if status == 'created':
            return self.start_order_flow(message)['success']
        elif status == 'validated':
            return self.handle_order_validated(message)
        else:
            logger.warning("Unknown order status", status=status)
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
    
    def _start_flow_monitoring(self):
        """Start background thread to monitor flow timeouts"""
        def monitor_flow_timeouts():
            while self.running:
                try:
                    current_time = datetime.utcnow()
                    timed_out_flows = []
                    
                    for order_id, flow in self.order_flows.items():
                        if flow['state'] not in [self.flow_states['COMPLETED'], self.flow_states['FAILED'], self.flow_states['CANCELLED']]:
                            timeout_at = datetime.fromisoformat(flow['timeout_at'])
                            if current_time > timeout_at:
                                timed_out_flows.append(order_id)
                    
                    for order_id in timed_out_flows:
                        self._handle_flow_failure(order_id, "Processing timeout")
                        logger.warning("Order flow timed out", order_id=order_id)
                    
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    logger.error("Error in flow monitoring", error=str(e))
                    time.sleep(30)
        
        threading.Thread(target=monitor_flow_timeouts, daemon=True).start()
        logger.info("Flow monitoring thread started")
    
    def stop(self):
        """Stop the orchestrator"""
        self.running = False
        self.connection_manager.close_connections()
        logger.info("Order orchestrator stopped")

# Flask web service for orchestrator management
app = Flask(__name__)
orchestrator = OrderOrchestrator()

@app.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint"""
    try:
        from health_utils import create_standard_health_endpoint
        
        # Create health status with custom checks
        def check_orchestrator_service_state():
            return {
                'healthy': orchestrator.running,
                'active_flows': len(orchestrator.order_flows),
                'consumer_running': orchestrator.running
            }
        
        health_status = create_standard_health_endpoint(
            'order_orchestrator',
            custom_checks=[
                {'name': 'service_state', 'check_func': check_orchestrator_service_state}
            ]
        )
        
        status = health_status.get_health_status()
        http_status = 200 if status['overall_healthy'] else 503
        
        return jsonify(status), http_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return jsonify({
            'status': 'unhealthy',
            'service': 'order_orchestrator',
            'error': str(e)
        }), 503

@app.route('/flows/<order_id>', methods=['GET'])
def get_order_flow(order_id):
    """Get order flow by ID"""
    flow = orchestrator.get_order_flow(order_id)
    
    if flow:
        return jsonify(flow)
    else:
        return jsonify({'error': 'Order flow not found'}), 404

@app.route('/flows', methods=['GET'])
def get_flows():
    """Get flows by state"""
    state = request.args.get('state')
    
    if state:
        flows = orchestrator.get_flows_by_state(state)
        return jsonify({'flows': flows, 'state': state})
    else:
        all_flows = list(orchestrator.order_flows.values())
        return jsonify({'flows': all_flows})

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get orchestrator metrics"""
    metrics = orchestrator.get_metrics()
    return jsonify(metrics)

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        logger.info("Starting Order Orchestrator", port=Config.ORCHESTRATOR_SERVICE_PORT)
        app.run(host='0.0.0.0', port=Config.ORCHESTRATOR_SERVICE_PORT, debug=False)
    except KeyboardInterrupt:
        logger.info("Shutting down Order Orchestrator")
        orchestrator.stop()
    except Exception as e:
        logger.error("Error starting Order Orchestrator", error=str(e))
        orchestrator.stop()