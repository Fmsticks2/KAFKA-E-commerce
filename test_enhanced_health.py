#!/usr/bin/env python3
"""
Enhanced Health Check Test Suite
Tests the improved health endpoints, startup timing, and service dependencies
"""

import requests
import time
import json
from typing import Dict, List
from config import Config

class EnhancedHealthTester:
    def __init__(self):
        self.services = {
            'order_service': {'port': Config.ORDER_SERVICE_PORT, 'endpoint': '/health'},
            'payment_service': {'port': Config.PAYMENT_SERVICE_PORT, 'endpoint': '/health'},
            'inventory_service': {'port': Config.INVENTORY_SERVICE_PORT, 'endpoint': '/health'},
            'notification_service': {'port': Config.NOTIFICATION_SERVICE_PORT, 'endpoint': '/health'},
            'order_orchestrator': {'port': Config.ORCHESTRATOR_SERVICE_PORT, 'endpoint': '/health'},
            'monitoring_service': {'port': Config.MONITORING_SERVICE_PORT, 'endpoint': '/health'}
        }
        self.test_results = []
    
    def test_enhanced_health_endpoints(self) -> Dict[str, bool]:
        """Test all enhanced health endpoints"""
        print("\n=== Testing Enhanced Health Endpoints ===")
        results = {}
        
        for service_name, config in self.services.items():
            print(f"\nTesting {service_name}...")
            
            try:
                url = f"http://localhost:{config['port']}{config['endpoint']}"
                response = requests.get(url, timeout=Config.SERVICE_HEALTH_CHECK_TIMEOUT)
                
                if response.status_code in [200, 503]:  # Both healthy and unhealthy are valid responses
                    try:
                        data = response.json()
                        
                        # Check for enhanced health response format
                        required_fields = ['status', 'service', 'timestamp']
                        has_enhanced_format = all(field in data for field in required_fields)
                        
                        if has_enhanced_format:
                            print(f"  ✓ Enhanced health endpoint working")
                            print(f"  ✓ Status: {data.get('status')}")
                            print(f"  ✓ Service: {data.get('service')}")
                            print(f"  ✓ Response time: {response.elapsed.total_seconds():.3f}s")
                            
                            # Check for custom checks
                            if 'custom_checks' in data:
                                print(f"  ✓ Custom checks: {len(data['custom_checks'])} found")
                            
                            results[service_name] = True
                        else:
                            print(f"  ⚠ Basic health endpoint (not enhanced)")
                            results[service_name] = False
                            
                    except json.JSONDecodeError:
                        print(f"  ✗ Invalid JSON response")
                        results[service_name] = False
                else:
                    print(f"  ✗ HTTP {response.status_code}: {response.text[:100]}")
                    results[service_name] = False
                    
            except requests.exceptions.ConnectionError:
                print(f"  ✗ Connection refused - service may not be running")
                results[service_name] = False
            except requests.exceptions.Timeout:
                print(f"  ✗ Request timeout")
                results[service_name] = False
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                results[service_name] = False
        
        return results
    
    def test_service_startup_timing(self) -> Dict[str, float]:
        """Test service startup and readiness timing"""
        print("\n=== Testing Service Startup Timing ===")
        timing_results = {}
        
        for service_name, config in self.services.items():
            print(f"\nTesting startup timing for {service_name}...")
            
            start_time = time.time()
            max_attempts = Config.SERVICE_STARTUP_TIMEOUT // Config.SERVICE_READINESS_CHECK_INTERVAL
            
            for attempt in range(int(max_attempts)):
                try:
                    url = f"http://localhost:{config['port']}{config['endpoint']}"
                    response = requests.get(url, timeout=Config.SERVICE_HEALTH_CHECK_TIMEOUT)
                    
                    if response.status_code == 200:
                        elapsed = time.time() - start_time
                        timing_results[service_name] = elapsed
                        print(f"  ✓ Service ready in {elapsed:.2f}s")
                        break
                        
                except requests.exceptions.ConnectionError:
                    pass  # Service not ready yet
                
                time.sleep(Config.SERVICE_READINESS_CHECK_INTERVAL)
            else:
                elapsed = time.time() - start_time
                timing_results[service_name] = elapsed
                print(f"  ✗ Service not ready after {elapsed:.2f}s")
        
        return timing_results
    
    def test_inter_service_communication(self) -> Dict[str, bool]:
        """Test inter-service communication and dependency management"""
        print("\n=== Testing Inter-Service Communication ===")
        results = {}
        
        # Test monitoring service's ability to check other services
        try:
            url = f"http://localhost:{Config.MONITORING_SERVICE_PORT}/health/summary"
            response = requests.get(url, timeout=Config.SERVICE_REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✓ Monitoring service health summary available")
                print(f"  ✓ Services monitored: {len(data.get('services', {}))}")
                
                # Check if startup order information is included
                for service_name, health_info in data.get('services', {}).items():
                    if 'startup_order' in health_info:
                        print(f"  ✓ {service_name} startup order: {health_info['startup_order']}")
                
                results['monitoring_integration'] = True
            else:
                print(f"  ✗ Monitoring service health summary failed: HTTP {response.status_code}")
                results['monitoring_integration'] = False
                
        except Exception as e:
            print(f"  ✗ Monitoring service communication error: {str(e)}")
            results['monitoring_integration'] = False
        
        return results
    
    def test_retry_and_timeout_configuration(self) -> Dict[str, bool]:
        """Test retry logic and timeout configurations"""
        print("\n=== Testing Retry and Timeout Configuration ===")
        results = {}
        
        # Test with a non-existent service to verify retry logic
        print("\nTesting retry logic with non-existent service...")
        start_time = time.time()
        
        try:
            # Try to connect to a non-existent port
            url = "http://localhost:9999/health"
            response = requests.get(url, timeout=Config.SERVICE_HEALTH_CHECK_TIMEOUT)
        except requests.exceptions.ConnectionError:
            elapsed = time.time() - start_time
            expected_min_time = Config.SERVICE_RETRY_DELAY * (Config.SERVICE_RETRY_ATTEMPTS - 1)
            
            if elapsed >= expected_min_time:
                print(f"  ✓ Retry logic working (took {elapsed:.2f}s, expected >= {expected_min_time:.2f}s)")
                results['retry_logic'] = True
            else:
                print(f"  ⚠ Retry logic may not be working properly (took {elapsed:.2f}s)")
                results['retry_logic'] = False
        except requests.exceptions.Timeout:
            print(f"  ✓ Timeout configuration working")
            results['timeout_config'] = True
        except Exception as e:
            print(f"  ⚠ Unexpected error: {str(e)}")
            results['retry_logic'] = False
        
        return results
    
    def run_all_tests(self) -> Dict[str, any]:
        """Run all enhanced health check tests"""
        print("Starting Enhanced Health Check Test Suite...")
        print(f"Configuration:")
        print(f"  - Service startup timeout: {Config.SERVICE_STARTUP_TIMEOUT}s")
        print(f"  - Health check timeout: {Config.SERVICE_HEALTH_CHECK_TIMEOUT}s")
        print(f"  - Retry attempts: {Config.SERVICE_RETRY_ATTEMPTS}")
        print(f"  - Retry delay: {Config.SERVICE_RETRY_DELAY}s")
        print(f"  - Readiness check interval: {Config.SERVICE_READINESS_CHECK_INTERVAL}s")
        
        all_results = {
            'enhanced_endpoints': self.test_enhanced_health_endpoints(),
            'startup_timing': self.test_service_startup_timing(),
            'inter_service_communication': self.test_inter_service_communication(),
            'retry_timeout_config': self.test_retry_and_timeout_configuration()
        }
        
        # Generate summary
        print("\n=== Test Summary ===")
        total_tests = 0
        passed_tests = 0
        
        for category, results in all_results.items():
            if isinstance(results, dict):
                for test_name, result in results.items():
                    total_tests += 1
                    if result:
                        passed_tests += 1
                        print(f"  ✓ {category}.{test_name}")
                    else:
                        print(f"  ✗ {category}.{test_name}")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\nOverall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Save results to file
        with open('enhanced_health_test_results.json', 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        print(f"\nDetailed results saved to: enhanced_health_test_results.json")
        
        return all_results

if __name__ == "__main__":
    tester = EnhancedHealthTester()
    results = tester.run_all_tests()