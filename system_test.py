#!/usr/bin/env python3
"""
Comprehensive System Test Script for Kafka E-commerce Platform
This script provides manual testing capabilities for all system components.
"""

import json
import time
import requests
import threading
from typing import Dict, Any, List
from datetime import datetime
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

class SystemTester:
    """Comprehensive system tester for the e-commerce platform"""
    
    def __init__(self):
        self.base_urls = {
            'order': 'http://localhost:5001',
            'payment': 'http://localhost:5002',
            'inventory': 'http://localhost:5003',
            'notification': 'http://localhost:5004',
            'monitoring': 'http://localhost:5005',
            'embedded_kafka': 'http://localhost:9093'
        }
        self.test_results = []
        
    def log_test_result(self, test_name: str, success: bool, message: str = "", data: Dict = None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'data': data or {}
        }
        self.test_results.append(result)
        
        if success:
            logger.info(f"✅ {test_name}: PASSED", message=message, data=data)
        else:
            logger.error(f"❌ {test_name}: FAILED", message=message, data=data)
    
    def check_service_health(self, service_name: str) -> bool:
        """Check if a service is healthy"""
        try:
            url = f"{self.base_urls[service_name]}/health"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                self.log_test_result(f"{service_name}_health", True, f"{service_name} service is healthy")
                return True
            else:
                self.log_test_result(f"{service_name}_health", False, f"{service_name} service returned {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result(f"{service_name}_health", False, f"{service_name} service is not accessible: {str(e)}")
            return False
    
    def test_kafka_connectivity(self) -> bool:
        """Test embedded Kafka connectivity"""
        try:
            response = requests.get(f"{self.base_urls['embedded_kafka']}/topics", timeout=5)
            
            if response.status_code == 200:
                topics = response.json().get('topics', [])
                self.log_test_result("kafka_connectivity", True, f"Kafka is accessible with {len(topics)} topics", {'topics': topics})
                return True
            else:
                self.log_test_result("kafka_connectivity", False, f"Kafka returned {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("kafka_connectivity", False, f"Kafka is not accessible: {str(e)}")
            return False
    
    def test_order_creation(self) -> Dict[str, Any]:
        """Test order creation flow"""
        try:
            order_data = {
                "customer_id": "test_customer_123",
                "items": [
                    {"product_id": "product_1", "quantity": 2, "price": 29.99},
                    {"product_id": "product_2", "quantity": 1, "price": 15.50}
                ],
                "total_amount": 75.48
            }
            
            response = requests.post(
                f"{self.base_urls['order']}/orders",
                json=order_data,
                timeout=10
            )
            
            if response.status_code == 201:
                order = response.json()
                self.log_test_result("order_creation", True, "Order created successfully", order)
                return order
            else:
                self.log_test_result("order_creation", False, f"Order creation failed: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            self.log_test_result("order_creation", False, f"Order creation error: {str(e)}")
            return {}
    
    def test_payment_processing(self, order_id: str) -> bool:
        """Test payment processing"""
        try:
            payment_data = {
                "order_id": order_id,
                "amount": 75.48,
                "payment_method": "credit_card",
                "card_details": {
                    "number": "4111111111111111",
                    "expiry": "12/25",
                    "cvv": "123"
                }
            }
            
            response = requests.post(
                f"{self.base_urls['payment']}/payments",
                json=payment_data,
                timeout=10
            )
            
            if response.status_code == 200:
                payment = response.json()
                self.log_test_result("payment_processing", True, "Payment processed successfully", payment)
                return True
            else:
                self.log_test_result("payment_processing", False, f"Payment failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test_result("payment_processing", False, f"Payment error: {str(e)}")
            return False
    
    def test_inventory_check(self) -> bool:
        """Test inventory management"""
        try:
            # Check inventory for a product
            response = requests.get(
                f"{self.base_urls['inventory']}/inventory/product_1",
                timeout=5
            )
            
            if response.status_code == 200:
                inventory = response.json()
                self.log_test_result("inventory_check", True, "Inventory check successful", inventory)
                return True
            else:
                self.log_test_result("inventory_check", False, f"Inventory check failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("inventory_check", False, f"Inventory error: {str(e)}")
            return False
    
    def test_notification_service(self) -> bool:
        """Test notification service"""
        try:
            notification_data = {
                "customer_id": "test_customer_123",
                "type": "order_confirmation",
                "message": "Your order has been confirmed!",
                "channel": "email"
            }
            
            response = requests.post(
                f"{self.base_urls['notification']}/notifications",
                json=notification_data,
                timeout=5
            )
            
            if response.status_code == 200:
                notification = response.json()
                self.log_test_result("notification_service", True, "Notification sent successfully", notification)
                return True
            else:
                self.log_test_result("notification_service", False, f"Notification failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("notification_service", False, f"Notification error: {str(e)}")
            return False
    
    def test_monitoring_metrics(self) -> bool:
        """Test monitoring service"""
        try:
            response = requests.get(
                f"{self.base_urls['monitoring']}/metrics",
                timeout=5
            )
            
            if response.status_code == 200:
                metrics = response.json()
                self.log_test_result("monitoring_metrics", True, "Monitoring metrics retrieved", metrics)
                return True
            else:
                self.log_test_result("monitoring_metrics", False, f"Monitoring failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("monitoring_metrics", False, f"Monitoring error: {str(e)}")
            return False
    
    def test_kafka_message_flow(self) -> bool:
        """Test Kafka message production and consumption"""
        try:
            # Test message production
            test_message = {
                "test_id": "system_test_" + str(int(time.time())),
                "message": "Test message from system tester",
                "timestamp": datetime.now().isoformat()
            }
            
            # Send message to test topic
            response = requests.post(
                f"{self.base_urls['embedded_kafka']}/produce/test.topic",
                json={
                    "key": test_message["test_id"],
                    "value": json.dumps(test_message)
                },
                timeout=5
            )
            
            if response.status_code == 200:
                self.log_test_result("kafka_produce", True, "Message produced to Kafka", test_message)
                
                # Wait a bit and try to consume
                time.sleep(2)
                
                consume_response = requests.get(
                    f"{self.base_urls['embedded_kafka']}/consume/test.topic",
                    params={"group_id": "system_test_group", "max_records": 10},
                    timeout=5
                )
                
                if consume_response.status_code == 200:
                    messages = consume_response.json().get('messages', [])
                    self.log_test_result("kafka_consume", True, f"Consumed {len(messages)} messages", {'message_count': len(messages)})
                    return True
                else:
                    self.log_test_result("kafka_consume", False, f"Failed to consume: {consume_response.status_code}")
                    return False
            else:
                self.log_test_result("kafka_produce", False, f"Failed to produce: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("kafka_message_flow", False, f"Kafka message flow error: {str(e)}")
            return False
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all system tests"""
        logger.info("🚀 Starting comprehensive system test...")
        
        # Test 1: Service Health Checks
        logger.info("📋 Testing service health...")
        services = ['order', 'payment', 'inventory', 'notification', 'monitoring']
        healthy_services = []
        
        for service in services:
            if self.check_service_health(service):
                healthy_services.append(service)
        
        # Test 2: Kafka Connectivity
        logger.info("📡 Testing Kafka connectivity...")
        kafka_healthy = self.test_kafka_connectivity()
        
        # Test 3: Kafka Message Flow
        if kafka_healthy:
            logger.info("💬 Testing Kafka message flow...")
            self.test_kafka_message_flow()
        
        # Test 4: End-to-End Order Flow
        if 'order' in healthy_services:
            logger.info("🛒 Testing order creation flow...")
            order = self.test_order_creation()
            
            if order and 'order_id' in order:
                # Test payment processing
                if 'payment' in healthy_services:
                    logger.info("💳 Testing payment processing...")
                    self.test_payment_processing(order['order_id'])
        
        # Test 5: Individual Service Tests
        if 'inventory' in healthy_services:
            logger.info("📦 Testing inventory management...")
            self.test_inventory_check()
        
        if 'notification' in healthy_services:
            logger.info("📧 Testing notification service...")
            self.test_notification_service()
        
        if 'monitoring' in healthy_services:
            logger.info("📊 Testing monitoring service...")
            self.test_monitoring_metrics()
        
        # Generate summary
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        summary = {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'healthy_services': healthy_services,
            'kafka_healthy': kafka_healthy,
            'test_results': self.test_results
        }
        
        logger.info("📈 Test Summary", 
                   total=total_tests, 
                   passed=passed_tests, 
                   failed=failed_tests, 
                   success_rate=f"{summary['success_rate']:.1f}%")
        
        return summary
    
    def print_detailed_report(self):
        """Print a detailed test report"""
        print("\n" + "="*80)
        print("🔍 DETAILED TEST REPORT")
        print("="*80)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"\n{status} | {result['test']}")
            print(f"   Time: {result['timestamp']}")
            if result['message']:
                print(f"   Message: {result['message']}")
            if result['data']:
                print(f"   Data: {json.dumps(result['data'], indent=2)}")
        
        print("\n" + "="*80)

def main():
    """Main function to run system tests"""
    print("🎯 Kafka E-commerce System Tester")
    print("==================================\n")
    
    tester = SystemTester()
    
    try:
        # Run comprehensive tests
        summary = tester.run_comprehensive_test()
        
        # Print summary
        print("\n" + "="*50)
        print("📊 TEST SUMMARY")
        print("="*50)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Healthy Services: {', '.join(summary['healthy_services'])}")
        print(f"Kafka Status: {'✅ Healthy' if summary['kafka_healthy'] else '❌ Unhealthy'}")
        
        # Print detailed report
        tester.print_detailed_report()
        
        # Save results to file
        with open('test_results.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: test_results.json")
        
        return summary['success_rate'] > 80  # Consider success if >80% tests pass
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        logger.error("Test execution failed", error=str(e))
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)