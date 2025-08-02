import pytest
import json
import time
import uuid
import requests
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any
from config import Config

# Import embedded Kafka adapter if needed
if Config.USE_EMBEDDED_KAFKA:
    from embedded_kafka_adapter import patch_kafka_imports
    patch_kafka_imports()

from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
try:
    from kafka.admin import NewTopic
except ImportError:
    NewTopic = str
from kafka_utils import KafkaConnectionManager, MessageProducer, MessageConsumer

class TestKafkaEcommerceSystem:
    """Comprehensive test suite for Kafka e-commerce system"""
    
    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        cls.connection_manager = KafkaConnectionManager()
        cls.producer = MessageProducer(cls.connection_manager)
        cls.test_messages = []
        cls.received_messages = []
        
        # Service endpoints
        cls.service_urls = {
            'order': f'http://localhost:{Config.ORDER_SERVICE_PORT}',
            'payment': f'http://localhost:{Config.PAYMENT_SERVICE_PORT}',
            'inventory': f'http://localhost:{Config.INVENTORY_SERVICE_PORT}',
            'notification': f'http://localhost:{Config.NOTIFICATION_SERVICE_PORT}',
            'orchestrator': f'http://localhost:{Config.ORCHESTRATOR_SERVICE_PORT}',
            'monitoring': f'http://localhost:{Config.MONITORING_SERVICE_PORT}'
        }
        
        # Wait for services to be ready
        cls._wait_for_services()
    
    @classmethod
    def _wait_for_services(cls, timeout=60):
        """Wait for all services to be ready"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            all_ready = True
            
            for service_name, url in cls.service_urls.items():
                try:
                    response = requests.get(f'{url}/health', timeout=5)
                    if response.status_code != 200:
                        all_ready = False
                        break
                except requests.exceptions.RequestException:
                    all_ready = False
                    break
            
            if all_ready:
                print("All services are ready")
                return
            
            print("Waiting for services to be ready...")
            time.sleep(2)
        
        raise Exception("Services did not become ready within timeout")
    
    def test_kafka_connectivity(self):
        """Test Kafka cluster connectivity"""
        # Test producer connectivity
        test_message = {
            'test_id': str(uuid.uuid4()),
            'message': 'connectivity_test',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        success = self.producer.send_message(
            topic=Config.TOPICS['ORDERS_CREATED'],
            message=test_message,
            key=test_message['test_id']
        )
        
        assert success, "Failed to send test message to Kafka"
        
        # Test consumer connectivity
        messages_received = []
        
        def test_consumer_handler(message):
            if message.get('test_id') == test_message['test_id']:
                messages_received.append(message)
            return True
        
        consumer = MessageConsumer(
            connection_manager=self.connection_manager,
            topics=[Config.TOPICS['ORDERS_CREATED']],
            group_id='test_connectivity_group',
            message_handler=test_consumer_handler
        )
        
        # Start consumer in thread
        consumer_thread = threading.Thread(target=consumer.start_consuming, daemon=True)
        consumer_thread.start()
        
        # Wait for message to be consumed
        timeout = 10
        start_time = time.time()
        
        while time.time() - start_time < timeout and not messages_received:
            time.sleep(0.1)
        
        assert len(messages_received) > 0, "Test message was not consumed"
        assert messages_received[0]['test_id'] == test_message['test_id']
    
    def test_service_health_checks(self):
        """Test health endpoints of all services"""
        for service_name, url in self.service_urls.items():
            response = requests.get(f'{url}/health', timeout=10)
            
            assert response.status_code == 200, f"{service_name} service health check failed"
            
            health_data = response.json()
            assert health_data['status'] == 'healthy', f"{service_name} service is not healthy"
    
    def test_order_creation_flow(self):
        """Test complete order creation and processing flow"""
        # Create test order
        order_data = {
            'customer_id': 'test_customer_001',
            'items': [
                {'product_id': 'laptop', 'quantity': 1, 'price': 999.99},
                {'product_id': 'mouse', 'quantity': 2, 'price': 25.00}
            ],
            'total_amount': 1049.99,
            'shipping_address': {
                'street': '123 Test St',
                'city': 'Test City',
                'zip': '12345'
            }
        }
        
        # Send order creation request
        response = requests.post(
            f'{self.service_urls["order"]}/orders',
            json=order_data,
            timeout=10
        )
        
        assert response.status_code == 201, "Order creation failed"
        
        order_response = response.json()
        order_id = order_response['order_id']
        
        assert order_id is not None, "Order ID not returned"
        assert order_response['status'] == 'created', "Order status is not 'created'"
        
        # Wait for order processing to complete
        self._wait_for_order_completion(order_id, timeout=30)
        
        # Verify order status
        order_status_response = requests.get(
            f'{self.service_urls["order"]}/orders/{order_id}',
            timeout=10
        )
        
        assert order_status_response.status_code == 200
        final_order = order_status_response.json()
        
        # Order should be completed or failed
        assert final_order['status'] in ['completed', 'failed'], f"Unexpected final order status: {final_order['status']}"
        
        return order_id, final_order['status']
    
    def test_payment_processing(self):
        """Test payment processing functionality"""
        payment_data = {
            'order_id': str(uuid.uuid4()),
            'amount': 100.00,
            'payment_method': 'credit_card',
            'customer_id': 'test_customer_002'
        }
        
        # Send payment request
        response = requests.post(
            f'{self.service_urls["payment"]}/payments',
            json=payment_data,
            timeout=10
        )
        
        assert response.status_code == 201, "Payment creation failed"
        
        payment_response = response.json()
        payment_id = payment_response['payment_id']
        
        # Wait for payment processing
        time.sleep(3)
        
        # Check payment status
        payment_status_response = requests.get(
            f'{self.service_urls["payment"]}/payments/{payment_id}',
            timeout=10
        )
        
        assert payment_status_response.status_code == 200
        payment_status = payment_status_response.json()
        
        assert payment_status['status'] in ['completed', 'failed'], f"Unexpected payment status: {payment_status['status']}"
    
    def test_inventory_management(self):
        """Test inventory reservation and release"""
        # Check initial inventory
        inventory_response = requests.get(
            f'{self.service_urls["inventory"]}/inventory',
            timeout=10
        )
        
        assert inventory_response.status_code == 200
        inventory_data = inventory_response.json()
        
        # Find a product with available stock
        available_product = None
        for product_id, stock_info in inventory_data.items():
            if stock_info['available'] > 0:
                available_product = product_id
                break
        
        assert available_product is not None, "No products with available stock found"
        
        initial_stock = inventory_data[available_product]['available']
        
        # Make reservation
        reservation_data = {
            'order_id': str(uuid.uuid4()),
            'items': [{'product_id': available_product, 'quantity': 1}]
        }
        
        reservation_response = requests.post(
            f'{self.service_urls["inventory"]}/reservations',
            json=reservation_data,
            timeout=10
        )
        
        assert reservation_response.status_code == 201, "Inventory reservation failed"
        
        reservation_result = reservation_response.json()
        reservation_id = reservation_result['reservation_id']
        
        # Check that inventory was reduced
        updated_inventory_response = requests.get(
            f'{self.service_urls["inventory"]}/inventory',
            timeout=10
        )
        
        updated_inventory = updated_inventory_response.json()
        new_stock = updated_inventory[available_product]['available']
        
        assert new_stock == initial_stock - 1, "Inventory was not properly reserved"
        
        # Release reservation
        release_response = requests.delete(
            f'{self.service_urls["inventory"]}/reservations/{reservation_id}',
            timeout=10
        )
        
        assert release_response.status_code == 200, "Inventory release failed"
        
        # Check that inventory was restored
        time.sleep(1)  # Allow time for processing
        
        final_inventory_response = requests.get(
            f'{self.service_urls["inventory"]}/inventory',
            timeout=10
        )
        
        final_inventory = final_inventory_response.json()
        final_stock = final_inventory[available_product]['available']
        
        assert final_stock == initial_stock, "Inventory was not properly released"
    
    def test_notification_service(self):
        """Test notification service functionality"""
        notification_data = {
            'customer_id': 'test_customer_003',
            'type': 'order_confirmation',
            'message': 'Your order has been confirmed',
            'channel': 'email'
        }
        
        # Send notification
        response = requests.post(
            f'{self.service_urls["notification"]}/notifications',
            json=notification_data,
            timeout=10
        )
        
        assert response.status_code == 201, "Notification sending failed"
        
        notification_response = response.json()
        notification_id = notification_response['notification_id']
        
        # Check notification status
        status_response = requests.get(
            f'{self.service_urls["notification"]}/notifications/{notification_id}',
            timeout=10
        )
        
        assert status_response.status_code == 200
        notification_status = status_response.json()
        
        assert notification_status['status'] in ['sent', 'failed'], f"Unexpected notification status: {notification_status['status']}"
    
    def test_monitoring_service(self):
        """Test monitoring service functionality"""
        # Test service health monitoring
        health_response = requests.get(
            f'{self.service_urls["monitoring"]}/services/health',
            timeout=10
        )
        
        assert health_response.status_code == 200
        health_data = health_response.json()
        
        # Check that all services are being monitored
        expected_services = ['order_service', 'payment_service', 'inventory_service', 
                           'notification_service', 'orchestrator_service']
        
        for service in expected_services:
            assert service in health_data, f"Service {service} not found in health data"
        
        # Test metrics endpoints
        metrics_endpoints = ['/metrics/kafka', '/metrics/orders', '/metrics/system']
        
        for endpoint in metrics_endpoints:
            response = requests.get(
                f'{self.service_urls["monitoring"]}{endpoint}',
                timeout=10
            )
            assert response.status_code == 200, f"Metrics endpoint {endpoint} failed"
    
    def test_order_failure_scenarios(self):
        """Test order failure scenarios"""
        # Test insufficient inventory scenario
        order_data = {
            'customer_id': 'test_customer_004',
            'items': [
                {'product_id': 'laptop', 'quantity': 1000, 'price': 999.99}  # Excessive quantity
            ],
            'total_amount': 999990.00
        }
        
        response = requests.post(
            f'{self.service_urls["order"]}/orders',
            json=order_data,
            timeout=10
        )
        
        assert response.status_code == 201
        order_response = response.json()
        order_id = order_response['order_id']
        
        # Wait for processing
        time.sleep(10)
        
        # Check that order failed due to insufficient inventory
        order_status_response = requests.get(
            f'{self.service_urls["order"]}/orders/{order_id}',
            timeout=10
        )
        
        assert order_status_response.status_code == 200
        final_order = order_status_response.json()
        
        # Order should fail due to insufficient inventory
        assert final_order['status'] == 'failed', "Order should have failed due to insufficient inventory"
    
    def test_payment_failure_scenarios(self):
        """Test payment failure scenarios"""
        # Create payment with invalid amount to trigger failure
        payment_data = {
            'order_id': str(uuid.uuid4()),
            'amount': -100.00,  # Invalid negative amount
            'payment_method': 'credit_card',
            'customer_id': 'test_customer_005'
        }
        
        response = requests.post(
            f'{self.service_urls["payment"]}/payments',
            json=payment_data,
            timeout=10
        )
        
        # Payment creation should fail or payment should be marked as failed
        if response.status_code == 201:
            payment_response = response.json()
            payment_id = payment_response['payment_id']
            
            # Wait for processing
            time.sleep(3)
            
            # Check payment status
            payment_status_response = requests.get(
                f'{self.service_urls["payment"]}/payments/{payment_id}',
                timeout=10
            )
            
            assert payment_status_response.status_code == 200
            payment_status = payment_status_response.json()
            
            assert payment_status['status'] == 'failed', "Payment should have failed due to invalid amount"
        else:
            # Payment creation failed, which is also acceptable
            assert response.status_code in [400, 422], "Payment should have been rejected"
    
    def test_performance_load(self):
        """Test system performance under load"""
        num_orders = 10
        order_ids = []
        
        # Create multiple orders concurrently
        def create_order(customer_id):
            order_data = {
                'customer_id': f'load_test_customer_{customer_id}',
                'items': [
                    {'product_id': 'mouse', 'quantity': 1, 'price': 25.00}
                ],
                'total_amount': 25.00
            }
            
            try:
                response = requests.post(
                    f'{self.service_urls["order"]}/orders',
                    json=order_data,
                    timeout=15
                )
                
                if response.status_code == 201:
                    order_response = response.json()
                    order_ids.append(order_response['order_id'])
            except Exception as e:
                print(f"Error creating order for customer {customer_id}: {e}")
        
        # Create orders in parallel
        threads = []
        for i in range(num_orders):
            thread = threading.Thread(target=create_order, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        assert len(order_ids) >= num_orders * 0.8, f"Only {len(order_ids)} out of {num_orders} orders were created successfully"
        
        # Wait for orders to be processed
        time.sleep(15)
        
        # Check that most orders were processed
        processed_count = 0
        for order_id in order_ids:
            try:
                response = requests.get(
                    f'{self.service_urls["order"]}/orders/{order_id}',
                    timeout=10
                )
                
                if response.status_code == 200:
                    order_data = response.json()
                    if order_data['status'] in ['completed', 'failed']:
                        processed_count += 1
            except Exception as e:
                print(f"Error checking order {order_id}: {e}")
        
        processing_rate = processed_count / len(order_ids) if order_ids else 0
        assert processing_rate >= 0.8, f"Only {processing_rate:.2%} of orders were processed"
    
    def test_data_consistency(self):
        """Test data consistency across services"""
        # Create an order and track its journey
        order_data = {
            'customer_id': 'consistency_test_customer',
            'items': [
                {'product_id': 'laptop', 'quantity': 1, 'price': 999.99}
            ],
            'total_amount': 999.99
        }
        
        response = requests.post(
            f'{self.service_urls["order"]}/orders',
            json=order_data,
            timeout=10
        )
        
        assert response.status_code == 201
        order_response = response.json()
        order_id = order_response['order_id']
        
        # Wait for processing
        time.sleep(10)
        
        # Check order status
        order_status_response = requests.get(
            f'{self.service_urls["order"]}/orders/{order_id}',
            timeout=10
        )
        
        assert order_status_response.status_code == 200
        order_status = order_status_response.json()
        
        if order_status['status'] == 'completed':
            # If order completed, check that payment was processed
            # and inventory was properly managed
            
            # Check orchestrator flow
            flow_response = requests.get(
                f'{self.service_urls["orchestrator"]}/flows/{order_id}',
                timeout=10
            )
            
            if flow_response.status_code == 200:
                flow_data = flow_response.json()
                assert flow_data['state'] == 'completed', "Orchestrator flow state inconsistent with order status"
                assert 'payment' in flow_data['steps_completed'], "Payment step not marked as completed"
                assert 'inventory_reservation' in flow_data['steps_completed'], "Inventory step not marked as completed"
    
    def _wait_for_order_completion(self, order_id: str, timeout: int = 30):
        """Wait for order to reach a final state"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    f'{self.service_urls["order"]}/orders/{order_id}',
                    timeout=5
                )
                
                if response.status_code == 200:
                    order_data = response.json()
                    if order_data['status'] in ['completed', 'failed']:
                        return order_data['status']
                
                time.sleep(1)
                
            except requests.exceptions.RequestException:
                time.sleep(1)
        
        raise Exception(f"Order {order_id} did not reach final state within {timeout} seconds")
    
    @classmethod
    def teardown_class(cls):
        """Cleanup test environment"""
        if hasattr(cls, 'connection_manager'):
            cls.connection_manager.close_connections()

# Utility functions for running tests
def run_integration_tests():
    """Run integration tests"""
    print("Running Kafka E-commerce Integration Tests...")
    
    # Run pytest with verbose output
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--capture=no'
    ])

def run_performance_tests():
    """Run performance tests only"""
    print("Running Performance Tests...")
    
    pytest.main([
        f'{__file__}::TestKafkaEcommerceSystem::test_performance_load',
        '-v',
        '--tb=short',
        '--capture=no'
    ])

def run_failure_tests():
    """Run failure scenario tests only"""
    print("Running Failure Scenario Tests...")
    
    pytest.main([
        f'{__file__}::TestKafkaEcommerceSystem::test_order_failure_scenarios',
        f'{__file__}::TestKafkaEcommerceSystem::test_payment_failure_scenarios',
        '-v',
        '--tb=short',
        '--capture=no'
    ])

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        if test_type == 'performance':
            run_performance_tests()
        elif test_type == 'failure':
            run_failure_tests()
        else:
            run_integration_tests()
    else:
        run_integration_tests()