import json
import time
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
import structlog
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from config import Config
from kafka_utils import KafkaConnectionManager, MessageConsumer

# Setup structured logging
logger = structlog.get_logger(__name__)

# Prometheus metrics
service_health_gauge = Gauge('service_health_status', 'Health status of services', ['service_name'])
kafka_message_counter = Counter('kafka_messages_total', 'Total Kafka messages processed', ['topic', 'service'])
kafka_message_errors = Counter('kafka_message_errors_total', 'Total Kafka message processing errors', ['topic', 'service'])
order_processing_time = Histogram('order_processing_duration_seconds', 'Order processing time in seconds')
order_status_gauge = Gauge('orders_by_status', 'Number of orders by status', ['status'])
service_response_time = Histogram('service_response_time_seconds', 'Service response time', ['service', 'endpoint'])

class MonitoringService:
    """Monitoring service for tracking system health and metrics"""
    
    def __init__(self):
        self.connection_manager = KafkaConnectionManager()
        self.running = False
        
        # Service endpoints for health checks with retry configuration
        self.service_endpoints = {
            'order_service': f'http://localhost:{Config.ORDER_SERVICE_PORT}/health',
            'payment_service': f'http://localhost:{Config.PAYMENT_SERVICE_PORT}/health',
            'inventory_service': f'http://localhost:{Config.INVENTORY_SERVICE_PORT}/health',
            'notification_service': f'http://localhost:{Config.NOTIFICATION_SERVICE_PORT}/health',
            'orchestrator_service': f'http://localhost:{Config.ORCHESTRATOR_SERVICE_PORT}/health'
        }
        
        # Service dependency order for startup checks
        self.service_startup_order = [
            'order_service',
            'payment_service', 
            'inventory_service',
            'notification_service',
            'orchestrator_service'
        ]
        
        # Metrics storage
        self.metrics_data = {
            'service_health': {},
            'kafka_metrics': {},
            'order_metrics': {},
            'system_metrics': {},
            'alerts': []
        }
        
        # Alert thresholds
        self.alert_thresholds = {
            'service_down_threshold': 3,  # consecutive failures
            'high_error_rate_threshold': 0.1,  # 10% error rate
            'slow_response_threshold': 5.0,  # 5 seconds
            'kafka_lag_threshold': 1000  # messages
        }
        
        # Start monitoring components
        self._start_health_monitoring()
        self._start_kafka_monitoring()
        self._start_metrics_collection()
        
        logger.info("Monitoring service initialized")
    
    def _get_service_port(self, service_name: str) -> int:
        """Get port number for a service"""
        port_mapping = {
            'order_service': Config.ORDER_SERVICE_PORT,
            'payment_service': Config.PAYMENT_SERVICE_PORT,
            'inventory_service': Config.INVENTORY_SERVICE_PORT,
            'notification_service': Config.NOTIFICATION_SERVICE_PORT,
            'orchestrator_service': Config.ORCHESTRATOR_SERVICE_PORT
        }
        return port_mapping.get(service_name, 8000)
    
    def _start_health_monitoring(self):
        """Start health monitoring for all services"""
        def monitor_service_health():
            while self.running:
                try:
                    for service_name, endpoint in self.service_endpoints.items():
                        health_status = self._check_service_health(service_name, endpoint)
                        
                        # Update Prometheus metric
                        service_health_gauge.labels(service_name=service_name).set(
                            1 if health_status['healthy'] else 0
                        )
                        
                        # Store health data
                        if service_name not in self.metrics_data['service_health']:
                            self.metrics_data['service_health'][service_name] = []
                        
                        self.metrics_data['service_health'][service_name].append({
                            'timestamp': datetime.utcnow().isoformat(),
                            'healthy': health_status['healthy'],
                            'response_time': health_status['response_time'],
                            'error': health_status.get('error')
                        })
                        
                        # Keep only last 100 health checks per service
                        if len(self.metrics_data['service_health'][service_name]) > 100:
                            self.metrics_data['service_health'][service_name] = \
                                self.metrics_data['service_health'][service_name][-100:]
                        
                        # Check for alerts
                        self._check_service_alerts(service_name, health_status)
                    
                    time.sleep(Config.HEALTH_CHECK_INTERVAL)
                    
                except Exception as e:
                    logger.error("Error in health monitoring", error=str(e))
                    time.sleep(Config.HEALTH_CHECK_INTERVAL)
        
        threading.Thread(target=monitor_service_health, daemon=True).start()
        logger.info("Health monitoring started")
    
    def _check_service_health(self, service_name: str, endpoint: str) -> Dict[str, Any]:
        """Check health of a specific service with retry logic using enhanced health utilities"""
        start_time = time.time()
        
        try:
            from health_utils import ServiceHealthChecker
            
            health_checker = ServiceHealthChecker()
            port = self._get_service_port(service_name)
            is_healthy = health_checker.check_service_health(
                service_name=service_name,
                port=port,
                endpoint='/health'
            )
            
            response_time = time.time() - start_time
            service_response_time.labels(service=service_name, endpoint='health').observe(response_time)
            
            if is_healthy:
                return {
                    'healthy': True,
                    'response_time': response_time,
                    'status_code': 200,
                    'service_name': service_name
                }
            else:
                return {
                    'healthy': False,
                    'response_time': response_time,
                    'error': f'Service {service_name} is not healthy'
                }
                
        except ImportError:
            # Fallback to original implementation if health_utils is not available
            last_error = None
            
            for attempt in range(Config.SERVICE_RETRY_ATTEMPTS):
                try:
                    response = requests.get(endpoint, timeout=Config.SERVICE_HEALTH_CHECK_TIMEOUT)
                    response_time = time.time() - start_time
                    
                    # Update response time metric
                    service_response_time.labels(service=service_name, endpoint='health').observe(response_time)
                    
                    if response.status_code == 200:
                        # Validate response format
                        try:
                            health_data = response.json()
                            if health_data.get('status') == 'healthy':
                                return {
                                    'healthy': True,
                                    'response_time': response_time,
                                    'status_code': response.status_code,
                                    'service_name': health_data.get('service', service_name)
                                }
                            else:
                                return {
                                    'healthy': False,
                                    'response_time': response_time,
                                    'status_code': response.status_code,
                                    'error': f'Service reports unhealthy status: {health_data.get("status")}'
                                }
                        except (ValueError, KeyError) as e:
                            return {
                                'healthy': False,
                                'response_time': response_time,
                                'status_code': response.status_code,
                                'error': f'Invalid health response format: {str(e)}'
                            }
                    else:
                        last_error = f'HTTP {response.status_code}: {response.text[:100]}'
                        
                except requests.exceptions.ConnectionError as e:
                    last_error = f'Connection refused: {str(e)}'
                except requests.exceptions.Timeout as e:
                    last_error = f'Request timeout: {str(e)}'
                except requests.exceptions.RequestException as e:
                    last_error = f'Request failed: {str(e)}'
                
                # Wait before retry (except on last attempt)
                if attempt < Config.SERVICE_RETRY_ATTEMPTS - 1:
                    time.sleep(Config.SERVICE_RETRY_DELAY)
            
            response_time = time.time() - start_time
            return {
                'healthy': False,
                'response_time': response_time,
                'error': last_error or 'Unknown error',
                'attempts': Config.SERVICE_RETRY_ATTEMPTS
            }
    
    def _check_service_alerts(self, service_name: str, health_status: Dict[str, Any]):
        """Check for service-related alerts"""
        try:
            # Check for service down alert
            if not health_status['healthy']:
                recent_checks = self.metrics_data['service_health'].get(service_name, [])[-3:]
                if len(recent_checks) >= 3 and all(not check['healthy'] for check in recent_checks):
                    self._create_alert(
                        alert_type='service_down',
                        service=service_name,
                        message=f'Service {service_name} has been down for {len(recent_checks)} consecutive checks',
                        severity='critical'
                    )
            
            # Check for slow response alert
            if health_status['response_time'] > self.alert_thresholds['slow_response_threshold']:
                self._create_alert(
                    alert_type='slow_response',
                    service=service_name,
                    message=f'Service {service_name} response time is {health_status["response_time"]:.2f}s',
                    severity='warning'
                )
                
        except Exception as e:
            logger.error("Error checking service alerts", service=service_name, error=str(e))
    
    def _start_kafka_monitoring(self):
        """Start Kafka monitoring"""
        def monitor_kafka_events():
            # Monitor all topics for message flow
            all_topics = list(Config.TOPICS.values())
            
            consumer = MessageConsumer(
                connection_manager=self.connection_manager,
                topics=all_topics,
                group_id=Config.CONSUMER_GROUPS['MONITORING_SERVICE'],
                message_handler=self._handle_kafka_message
            )
            
            consumer.start_consuming()
        
        threading.Thread(target=monitor_kafka_events, daemon=True).start()
        logger.info("Kafka monitoring started")
    
    def _handle_kafka_message(self, message: Dict[str, Any]) -> bool:
        """Handle Kafka messages for monitoring"""
        try:
            topic = message.get('_topic', 'unknown')
            service = self._get_service_from_topic(topic)
            
            # Update Prometheus metrics
            kafka_message_counter.labels(topic=topic, service=service).inc()
            
            # Store Kafka metrics
            if topic not in self.metrics_data['kafka_metrics']:
                self.metrics_data['kafka_metrics'][topic] = {
                    'message_count': 0,
                    'error_count': 0,
                    'last_message_time': None
                }
            
            self.metrics_data['kafka_metrics'][topic]['message_count'] += 1
            self.metrics_data['kafka_metrics'][topic]['last_message_time'] = datetime.utcnow().isoformat()
            
            # Track order-specific metrics
            if 'order_id' in message:
                self._track_order_metrics(message)
            
            return True
            
        except Exception as e:
            logger.error("Error handling Kafka message for monitoring", error=str(e))
            
            # Update error metrics
            topic = message.get('_topic', 'unknown')
            service = self._get_service_from_topic(topic)
            kafka_message_errors.labels(topic=topic, service=service).inc()
            
            if topic in self.metrics_data['kafka_metrics']:
                self.metrics_data['kafka_metrics'][topic]['error_count'] += 1
            
            return False
    
    def _get_service_from_topic(self, topic: str) -> str:
        """Get service name from topic"""
        topic_service_mapping = {
            Config.TOPICS['ORDERS_CREATED']: 'order_service',
            Config.TOPICS['ORDERS_VALIDATED']: 'order_service',
            Config.TOPICS['ORDERS_COMPLETED']: 'orchestrator_service',
            Config.TOPICS['ORDERS_FAILED']: 'orchestrator_service',
            Config.TOPICS['PAYMENTS_REQUESTED']: 'orchestrator_service',
            Config.TOPICS['PAYMENTS_COMPLETED']: 'payment_service',
            Config.TOPICS['PAYMENTS_FAILED']: 'payment_service',
            Config.TOPICS['INVENTORY_RESERVED']: 'inventory_service',
            Config.TOPICS['INVENTORY_RELEASED']: 'inventory_service',
            Config.TOPICS['NOTIFICATIONS_SENT']: 'notification_service'
        }
        
        return topic_service_mapping.get(topic, 'unknown')
    
    def _track_order_metrics(self, message: Dict[str, Any]):
        """Track order-specific metrics"""
        try:
            order_id = message['order_id']
            status = message.get('status')
            
            # Initialize order tracking if not exists
            if order_id not in self.metrics_data['order_metrics']:
                self.metrics_data['order_metrics'][order_id] = {
                    'created_at': None,
                    'completed_at': None,
                    'failed_at': None,
                    'status_history': [],
                    'processing_time': None
                }
            
            order_data = self.metrics_data['order_metrics'][order_id]
            
            # Track status changes
            if status:
                order_data['status_history'].append({
                    'status': status,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                # Update Prometheus gauge
                order_status_gauge.labels(status=status).inc()
            
            # Track timing
            if status == 'created':
                order_data['created_at'] = datetime.utcnow().isoformat()
            elif status == 'completed':
                order_data['completed_at'] = datetime.utcnow().isoformat()
                if order_data['created_at']:
                    created_time = datetime.fromisoformat(order_data['created_at'])
                    completed_time = datetime.fromisoformat(order_data['completed_at'])
                    processing_time = (completed_time - created_time).total_seconds()
                    order_data['processing_time'] = processing_time
                    
                    # Update Prometheus histogram
                    order_processing_time.observe(processing_time)
            elif status == 'failed':
                order_data['failed_at'] = datetime.utcnow().isoformat()
            
        except Exception as e:
            logger.error("Error tracking order metrics", error=str(e))
    
    def _start_metrics_collection(self):
        """Start periodic metrics collection"""
        def collect_system_metrics():
            while self.running:
                try:
                    # Collect system-wide metrics
                    self._collect_system_metrics()
                    
                    # Clean up old data
                    self._cleanup_old_data()
                    
                    time.sleep(Config.METRICS_COLLECTION_INTERVAL)
                    
                except Exception as e:
                    logger.error("Error in metrics collection", error=str(e))
                    time.sleep(Config.METRICS_COLLECTION_INTERVAL)
        
        threading.Thread(target=collect_system_metrics, daemon=True).start()
        logger.info("Metrics collection started")
    
    def _collect_system_metrics(self):
        """Collect system-wide metrics"""
        try:
            # Calculate order processing statistics
            completed_orders = [order for order in self.metrics_data['order_metrics'].values() 
                              if order['processing_time'] is not None]
            
            if completed_orders:
                avg_processing_time = sum(order['processing_time'] for order in completed_orders) / len(completed_orders)
                max_processing_time = max(order['processing_time'] for order in completed_orders)
                min_processing_time = min(order['processing_time'] for order in completed_orders)
            else:
                avg_processing_time = max_processing_time = min_processing_time = 0
            
            # Calculate error rates
            total_messages = sum(metrics['message_count'] for metrics in self.metrics_data['kafka_metrics'].values())
            total_errors = sum(metrics['error_count'] for metrics in self.metrics_data['kafka_metrics'].values())
            error_rate = (total_errors / total_messages) if total_messages > 0 else 0
            
            # Store system metrics
            system_metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'total_orders': len(self.metrics_data['order_metrics']),
                'completed_orders': len(completed_orders),
                'avg_processing_time': avg_processing_time,
                'max_processing_time': max_processing_time,
                'min_processing_time': min_processing_time,
                'total_kafka_messages': total_messages,
                'total_kafka_errors': total_errors,
                'kafka_error_rate': error_rate
            }
            
            if 'snapshots' not in self.metrics_data['system_metrics']:
                self.metrics_data['system_metrics']['snapshots'] = []
            
            self.metrics_data['system_metrics']['snapshots'].append(system_metrics)
            
            # Keep only last 100 snapshots
            if len(self.metrics_data['system_metrics']['snapshots']) > 100:
                self.metrics_data['system_metrics']['snapshots'] = \
                    self.metrics_data['system_metrics']['snapshots'][-100:]
            
            # Check for system-wide alerts
            if error_rate > self.alert_thresholds['high_error_rate_threshold']:
                self._create_alert(
                    alert_type='high_error_rate',
                    message=f'System error rate is {error_rate:.2%}',
                    severity='warning'
                )
            
        except Exception as e:
            logger.error("Error collecting system metrics", error=str(e))
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            # Clean up old order metrics (keep only last 24 hours)
            orders_to_remove = []
            for order_id, order_data in self.metrics_data['order_metrics'].items():
                if order_data['created_at']:
                    created_time = datetime.fromisoformat(order_data['created_at'])
                    if created_time < cutoff_time:
                        orders_to_remove.append(order_id)
            
            for order_id in orders_to_remove:
                del self.metrics_data['order_metrics'][order_id]
            
            # Clean up old alerts (keep only last 100)
            if len(self.metrics_data['alerts']) > 100:
                self.metrics_data['alerts'] = self.metrics_data['alerts'][-100:]
            
        except Exception as e:
            logger.error("Error cleaning up old data", error=str(e))
    
    def _create_alert(self, alert_type: str, message: str, severity: str, service: str = None):
        """Create a new alert"""
        try:
            alert = {
                'id': str(time.time()),
                'type': alert_type,
                'message': message,
                'severity': severity,
                'service': service,
                'timestamp': datetime.utcnow().isoformat(),
                'resolved': False
            }
            
            self.metrics_data['alerts'].append(alert)
            
            logger.warning("Alert created", 
                         alert_type=alert_type, 
                         message=message, 
                         severity=severity, 
                         service=service)
            
        except Exception as e:
            logger.error("Error creating alert", error=str(e))
    
    def get_service_health(self) -> Dict[str, Any]:
        """Get current service health status with dependency information"""
        health_summary = {}
        
        for service_name, health_data in self.metrics_data['service_health'].items():
            if health_data:
                latest_check = health_data[-1]
                health_summary[service_name] = {
                    'healthy': latest_check['healthy'],
                    'last_check': latest_check['timestamp'],
                    'response_time': latest_check['response_time'],
                    'error': latest_check.get('error'),
                    'startup_order': self.service_startup_order.index(service_name) if service_name in self.service_startup_order else -1
                }
            else:
                health_summary[service_name] = {
                    'healthy': False,
                    'last_check': None,
                    'response_time': None,
                    'error': 'No health data available',
                    'startup_order': self.service_startup_order.index(service_name) if service_name in self.service_startup_order else -1
                }
        
        return health_summary
    
    def get_kafka_metrics(self) -> Dict[str, Any]:
        """Get Kafka metrics"""
        return self.metrics_data['kafka_metrics']
    
    def get_order_metrics(self) -> Dict[str, Any]:
        """Get order processing metrics"""
        completed_orders = [order for order in self.metrics_data['order_metrics'].values() 
                          if order['processing_time'] is not None]
        
        failed_orders = [order for order in self.metrics_data['order_metrics'].values() 
                        if order['failed_at'] is not None]
        
        total_orders = len(self.metrics_data['order_metrics'])
        
        return {
            'total_orders': total_orders,
            'completed_orders': len(completed_orders),
            'failed_orders': len(failed_orders),
            'success_rate': (len(completed_orders) / total_orders * 100) if total_orders > 0 else 0,
            'avg_processing_time': (sum(order['processing_time'] for order in completed_orders) / len(completed_orders)) if completed_orders else 0
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics"""
        return self.metrics_data['system_metrics']
    
    def get_alerts(self, severity: str = None, resolved: bool = None) -> List[Dict[str, Any]]:
        """Get alerts with optional filtering"""
        alerts = self.metrics_data['alerts']
        
        if severity:
            alerts = [alert for alert in alerts if alert['severity'] == severity]
        
        if resolved is not None:
            alerts = [alert for alert in alerts if alert['resolved'] == resolved]
        
        return sorted(alerts, key=lambda x: x['timestamp'], reverse=True)
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        for alert in self.metrics_data['alerts']:
            if alert['id'] == alert_id:
                alert['resolved'] = True
                alert['resolved_at'] = datetime.utcnow().isoformat()
                return True
        return False
    
    def start(self):
        """Start the monitoring service"""
        self.running = True
        logger.info("Monitoring service started")
    
    def stop(self):
        """Stop the monitoring service"""
        self.running = False
        self.connection_manager.close_connections()
        logger.info("Monitoring service stopped")

# Flask web service for monitoring dashboard
app = Flask(__name__)
monitoring_service = MonitoringService()
monitoring_service.start()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'monitoring_service'})

@app.route('/services/health', methods=['GET'])
def get_services_health():
    """Get health status of all services"""
    health_data = monitoring_service.get_service_health()
    return jsonify(health_data)

@app.route('/metrics/kafka', methods=['GET'])
def get_kafka_metrics():
    """Get Kafka metrics"""
    kafka_metrics = monitoring_service.get_kafka_metrics()
    return jsonify(kafka_metrics)

@app.route('/metrics/orders', methods=['GET'])
def get_order_metrics():
    """Get order processing metrics"""
    order_metrics = monitoring_service.get_order_metrics()
    return jsonify(order_metrics)

@app.route('/metrics/system', methods=['GET'])
def get_system_metrics():
    """Get system-wide metrics"""
    system_metrics = monitoring_service.get_system_metrics()
    return jsonify(system_metrics)

@app.route('/metrics/prometheus', methods=['GET'])
def get_prometheus_metrics():
    """Get Prometheus metrics"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/alerts', methods=['GET'])
def get_alerts():
    """Get alerts with optional filtering"""
    severity = request.args.get('severity')
    resolved = request.args.get('resolved')
    
    if resolved is not None:
        resolved = resolved.lower() == 'true'
    
    alerts = monitoring_service.get_alerts(severity=severity, resolved=resolved)
    return jsonify({'alerts': alerts})

@app.route('/alerts/<alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Resolve an alert"""
    success = monitoring_service.resolve_alert(alert_id)
    
    if success:
        return jsonify({'message': 'Alert resolved successfully'})
    else:
        return jsonify({'error': 'Alert not found'}), 404

@app.route('/dashboard', methods=['GET'])
def get_dashboard():
    """Get comprehensive dashboard data"""
    dashboard_data = {
        'services_health': monitoring_service.get_service_health(),
        'kafka_metrics': monitoring_service.get_kafka_metrics(),
        'order_metrics': monitoring_service.get_order_metrics(),
        'system_metrics': monitoring_service.get_system_metrics(),
        'recent_alerts': monitoring_service.get_alerts(resolved=False)[:10],
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return jsonify(dashboard_data)

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        logger.info("Starting Monitoring Service", port=Config.MONITORING_SERVICE_PORT)
        app.run(host='0.0.0.0', port=Config.MONITORING_SERVICE_PORT, debug=False)
    except KeyboardInterrupt:
        logger.info("Shutting down Monitoring Service")
        monitoring_service.stop()
    except Exception as e:
        logger.error("Error starting Monitoring Service", error=str(e))
        monitoring_service.stop()