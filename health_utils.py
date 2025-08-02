#!/usr/bin/env python3
"""
Health Check Utilities for E-commerce Microservices

Provides standardized health check functionality with:
- Consistent response format
- Service dependency validation
- Enhanced error handling
- Startup readiness checks
"""

import time
import requests
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
import structlog
from config import Config
from kafka_utils import KafkaConnectionManager, health_check_kafka

logger = structlog.get_logger(__name__)

class HealthStatus:
    """Standard health status response format"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.start_time = datetime.utcnow()
        self.dependencies = []
        self.custom_checks = []
        
    def add_dependency(self, name: str, check_func: Callable[[], bool], critical: bool = True):
        """Add a dependency check"""
        self.dependencies.append({
            'name': name,
            'check_func': check_func,
            'critical': critical
        })
    
    def add_custom_check(self, name: str, check_func: Callable[[], Dict[str, Any]]):
        """Add a custom health check"""
        self.custom_checks.append({
            'name': name,
            'check_func': check_func
        })
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        status = {
            'status': 'healthy',
            'service': self.service_name,
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
            'dependencies': {},
            'checks': {},
            'overall_healthy': True
        }
        
        # Check dependencies
        for dep in self.dependencies:
            try:
                is_healthy = dep['check_func']()
                status['dependencies'][dep['name']] = {
                    'healthy': is_healthy,
                    'critical': dep['critical']
                }
                
                if dep['critical'] and not is_healthy:
                    status['overall_healthy'] = False
                    
            except Exception as e:
                logger.error("Dependency check failed", 
                           service=self.service_name,
                           dependency=dep['name'], 
                           error=str(e))
                status['dependencies'][dep['name']] = {
                    'healthy': False,
                    'critical': dep['critical'],
                    'error': str(e)
                }
                
                if dep['critical']:
                    status['overall_healthy'] = False
        
        # Run custom checks
        for check in self.custom_checks:
            try:
                check_result = check['check_func']()
                status['checks'][check['name']] = check_result
                
                # If check result indicates unhealthy state
                if isinstance(check_result, dict) and not check_result.get('healthy', True):
                    status['overall_healthy'] = False
                    
            except Exception as e:
                logger.error("Custom check failed", 
                           service=self.service_name,
                           check=check['name'], 
                           error=str(e))
                status['checks'][check['name']] = {
                    'healthy': False,
                    'error': str(e)
                }
                status['overall_healthy'] = False
        
        # Set overall status
        if not status['overall_healthy']:
            status['status'] = 'unhealthy'
        
        return status

class ServiceHealthChecker:
    """Enhanced service health checker with dependency management"""
    
    def __init__(self):
        self.kafka_connection = None
        self._initialize_kafka()
    
    def _initialize_kafka(self):
        """Initialize Kafka connection for health checks"""
        try:
            self.kafka_connection = KafkaConnectionManager()
            logger.info("Kafka connection initialized for health checks")
        except Exception as e:
            logger.warning("Failed to initialize Kafka connection", error=str(e))
    
    def check_kafka_health(self) -> bool:
        """Check Kafka connectivity"""
        try:
            if self.kafka_connection:
                return health_check_kafka(self.kafka_connection)
            return False
        except Exception as e:
            logger.error("Kafka health check failed", error=str(e))
            return False
    
    def check_service_endpoint(self, service_name: str, url: str, timeout: int = None) -> Dict[str, Any]:
        """Check health of a service endpoint with retry logic"""
        if timeout is None:
            timeout = Config.SERVICE_HEALTH_CHECK_TIMEOUT
        
        for attempt in range(Config.SERVICE_RETRY_ATTEMPTS):
            try:
                start_time = time.time()
                response = requests.get(url, timeout=timeout)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    try:
                        health_data = response.json()
                        return {
                            'healthy': health_data.get('status') == 'healthy',
                            'response_time': response_time,
                            'status_code': response.status_code,
                            'data': health_data
                        }
                    except ValueError:
                        return {
                            'healthy': True,  # Assume healthy if 200 but no JSON
                            'response_time': response_time,
                            'status_code': response.status_code,
                            'data': {'status': 'healthy', 'service': service_name}
                        }
                else:
                    if attempt == Config.SERVICE_RETRY_ATTEMPTS - 1:  # Last attempt
                        return {
                            'healthy': False,
                            'response_time': time.time() - start_time,
                            'status_code': response.status_code,
                            'error': f'HTTP {response.status_code}'
                        }
                    
            except requests.exceptions.ConnectionError:
                if attempt == Config.SERVICE_RETRY_ATTEMPTS - 1:
                    return {
                        'healthy': False,
                        'response_time': time.time() - start_time if 'start_time' in locals() else 0,
                        'error': 'Connection refused'
                    }
            except requests.exceptions.Timeout:
                if attempt == Config.SERVICE_RETRY_ATTEMPTS - 1:
                    return {
                        'healthy': False,
                        'response_time': timeout,
                        'error': 'Request timeout'
                    }
            except Exception as e:
                if attempt == Config.SERVICE_RETRY_ATTEMPTS - 1:
                    return {
                        'healthy': False,
                        'response_time': time.time() - start_time if 'start_time' in locals() else 0,
                        'error': str(e)
                    }
            
            # Wait before retry
            if attempt < Config.SERVICE_RETRY_ATTEMPTS - 1:
                time.sleep(Config.SERVICE_RETRY_DELAY)
        
        return {
            'healthy': False,
            'error': 'All retry attempts failed'
        }
    
    def wait_for_services_ready(self, services: Dict[str, str], timeout: int = None) -> Dict[str, bool]:
        """Wait for multiple services to become ready"""
        if timeout is None:
            timeout = Config.SERVICE_STARTUP_TIMEOUT
        
        results = {}
        start_time = time.time()
        
        logger.info("Waiting for services to become ready", 
                   services=list(services.keys()), 
                   timeout=timeout)
        
        while time.time() - start_time < timeout:
            all_ready = True
            
            for service_name, health_url in services.items():
                if service_name not in results or not results[service_name]:
                    health_result = self.check_service_endpoint(service_name, health_url, timeout=5)
                    results[service_name] = health_result.get('healthy', False)
                    
                    if results[service_name]:
                        logger.info("Service is ready", service=service_name)
                    else:
                        all_ready = False
            
            if all_ready:
                logger.info("All services are ready")
                break
            
            time.sleep(Config.SERVICE_READINESS_CHECK_INTERVAL)
        
        # Log final status
        ready_services = [name for name, ready in results.items() if ready]
        failed_services = [name for name, ready in results.items() if not ready]
        
        if failed_services:
            logger.warning("Some services failed to become ready", 
                         ready=ready_services, 
                         failed=failed_services,
                         elapsed_time=time.time() - start_time)
        else:
            logger.info("All services ready", 
                       services=ready_services,
                       elapsed_time=time.time() - start_time)
        
        return results

def create_standard_health_endpoint(service_name: str, 
                                  dependencies: List[Dict[str, Any]] = None,
                                  custom_checks: List[Dict[str, Any]] = None) -> HealthStatus:
    """Create a standard health status object for a service"""
    health_status = HealthStatus(service_name)
    
    # Add Kafka dependency by default
    health_checker = ServiceHealthChecker()
    health_status.add_dependency('kafka', health_checker.check_kafka_health, critical=True)
    
    # Add custom dependencies
    if dependencies:
        for dep in dependencies:
            health_status.add_dependency(
                dep['name'], 
                dep['check_func'], 
                dep.get('critical', True)
            )
    
    # Add custom checks
    if custom_checks:
        for check in custom_checks:
            health_status.add_custom_check(check['name'], check['check_func'])
    
    return health_status