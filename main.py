#!/usr/bin/env python3
"""
Kafka E-commerce System Main Launcher

This script starts all services in the correct order and provides
a unified interface for managing the entire system.
"""

import os
import sys
import time
import signal
import subprocess
import threading
import requests
from typing import Dict, List, Optional
import structlog
from config import Config
from kafka_utils import create_topics_if_not_exist, health_check_kafka, KafkaConnectionManager

# Setup structured logging
logger = structlog.get_logger(__name__)

class SystemLauncher:
    """Main system launcher for Kafka e-commerce platform"""
    
    def __init__(self):
        self.processes = {}
        self.running = False
        self.shutdown_event = threading.Event()
        
        # Service startup order (dependencies first)
        self.service_order = [
            'order_service',
            'payment_service', 
            'inventory_service',
            'notification_service',
            'order_orchestrator',
            'monitoring_service'
        ]
        
        # Service configurations
        self.services = {
            'order_service': {
                'script': 'order_service.py',
                'port': Config.ORDER_SERVICE_PORT,
                'health_endpoint': '/health',
                'required': True
            },
            'payment_service': {
                'script': 'payment_service.py',
                'port': Config.PAYMENT_SERVICE_PORT,
                'health_endpoint': '/health',
                'required': True
            },
            'inventory_service': {
                'script': 'inventory_service.py',
                'port': Config.INVENTORY_SERVICE_PORT,
                'health_endpoint': '/health',
                'required': True
            },
            'notification_service': {
                'script': 'notification_service.py',
                'port': Config.NOTIFICATION_SERVICE_PORT,
                'health_endpoint': '/health',
                'required': True
            },
            'order_orchestrator': {
                'script': 'order_orchestrator.py',
                'port': Config.ORCHESTRATOR_SERVICE_PORT,
                'health_endpoint': '/health',
                'required': True
            },
            'monitoring_service': {
                'script': 'monitoring_service.py',
                'port': Config.MONITORING_SERVICE_PORT,
                'health_endpoint': '/health',
                'required': False
            }
        }
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Received shutdown signal", signal=signum)
        self.shutdown()
    
    def check_prerequisites(self) -> bool:
        """Check system prerequisites"""
        logger.info("Checking system prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 7):
            logger.error("Python 3.7 or higher is required")
            return False
        
        # Check required files
        required_files = [
            'config.py',
            'kafka_utils.py',
            'requirements.txt',
            'docker-compose.yml'
        ] + [service['script'] for service in self.services.values()]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            logger.error("Missing required files", files=missing_files)
            return False
        
        # Check Kafka connectivity
        logger.info("Checking Kafka connectivity...")
        try:
            connection_manager = KafkaConnectionManager()
            if not health_check_kafka(connection_manager):
                logger.error("Kafka is not available. Please start Kafka using 'docker-compose up -d'")
                return False
        except Exception as e:
            logger.error("Kafka connectivity check failed", error=str(e))
            return False
        
        logger.info("Prerequisites check passed")
        return True
    
    def setup_kafka_topics(self) -> bool:
        """Setup Kafka topics"""
        logger.info("Setting up Kafka topics...")
        try:
            connection_manager = KafkaConnectionManager()
            create_topics_if_not_exist(connection_manager)
            logger.info("Kafka topics setup completed")
            return True
        except Exception as e:
            logger.error("Failed to setup Kafka topics", error=str(e))
            return False
    
    def start_service(self, service_name: str) -> bool:
        """Start a specific service"""
        if service_name in self.processes:
            logger.warning("Service already running", service=service_name)
            return True
        
        service_config = self.services[service_name]
        script_path = service_config['script']
        
        logger.info("Starting service", service=service_name, script=script_path)
        
        try:
            # Start the service process
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True
            )
            
            self.processes[service_name] = {
                'process': process,
                'config': service_config,
                'start_time': time.time()
            }
            
            # Wait for service to be ready
            if self._wait_for_service_ready(service_name):
                logger.info("Service started successfully", service=service_name)
                return True
            else:
                logger.error("Service failed to start", service=service_name)
                self._stop_service(service_name)
                return False
                
        except Exception as e:
            logger.error("Error starting service", service=service_name, error=str(e))
            return False
    
    def _wait_for_service_ready(self, service_name: str, timeout: int = None) -> bool:
        """Wait for service to be ready with improved error handling"""
        if timeout is None:
            timeout = Config.SERVICE_STARTUP_TIMEOUT
            
        service_info = self.processes[service_name]
        config = service_info['config']
        
        health_url = f"http://localhost:{config['port']}{config['health_endpoint']}"
        start_time = time.time()
        
        logger.info("Waiting for service to be ready", service=service_name, url=health_url, timeout=timeout)
        
        # Give the service some time to initialize before first check
        time.sleep(2)
        
        while time.time() - start_time < timeout:
            # Check if process is still running
            if service_info['process'].poll() is not None:
                # Get process output for debugging
                stdout, stderr = service_info['process'].communicate()
                logger.error("Service process terminated", 
                           service=service_name, 
                           stdout=stdout[-500:] if stdout else None,
                           stderr=stderr[-500:] if stderr else None)
                return False
            
            try:
                response = requests.get(health_url, timeout=Config.SERVICE_HEALTH_CHECK_TIMEOUT)
                if response.status_code == 200:
                    # Verify the response contains expected health data
                    try:
                        health_data = response.json()
                        if health_data.get('status') == 'healthy':
                            logger.info("Service is ready and healthy", service=service_name)
                            return True
                        else:
                            logger.warning("Service responded but not healthy", 
                                         service=service_name, 
                                         health_data=health_data)
                    except (ValueError, KeyError) as e:
                        logger.warning("Invalid health response format", 
                                     service=service_name, 
                                     response_text=response.text[:200],
                                     error=str(e))
                else:
                    logger.warning("Service health check failed", 
                                 service=service_name, 
                                 status_code=response.status_code,
                                 response_text=response.text[:200])
                    
            except requests.exceptions.ConnectionError:
                logger.debug("Service not yet available", service=service_name)
            except requests.exceptions.Timeout:
                logger.warning("Health check timeout", service=service_name)
            except requests.exceptions.RequestException as e:
                logger.warning("Health check request failed", service=service_name, error=str(e))
            
            time.sleep(Config.SERVICE_READINESS_CHECK_INTERVAL)
        
        logger.error("Service did not become ready within timeout", 
                    service=service_name, 
                    timeout=timeout,
                    elapsed_time=time.time() - start_time)
        return False
    
    def start_all_services(self) -> bool:
        """Start all services in the correct order"""
        logger.info("Starting all services...")
        
        failed_services = []
        
        for service_name in self.service_order:
            if not self.start_service(service_name):
                failed_services.append(service_name)
                
                # Check if this is a required service
                if self.services[service_name]['required']:
                    logger.error("Required service failed to start", service=service_name)
                    return False
        
        if failed_services:
            logger.warning("Some non-required services failed to start", services=failed_services)
        
        logger.info("All required services started successfully")
        return True
    
    def _stop_service(self, service_name: str):
        """Stop a specific service"""
        if service_name not in self.processes:
            return
        
        logger.info("Stopping service", service=service_name)
        
        service_info = self.processes[service_name]
        process = service_info['process']
        
        try:
            # Try graceful shutdown first
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                logger.warning("Force killing service", service=service_name)
                process.kill()
                process.wait()
            
            logger.info("Service stopped", service=service_name)
            
        except Exception as e:
            logger.error("Error stopping service", service=service_name, error=str(e))
        
        finally:
            del self.processes[service_name]
    
    def stop_all_services(self):
        """Stop all running services"""
        logger.info("Stopping all services...")
        
        # Stop services in reverse order
        for service_name in reversed(self.service_order):
            if service_name in self.processes:
                self._stop_service(service_name)
        
        logger.info("All services stopped")
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        status = {
            'running': self.running,
            'services': {},
            'kafka_health': self._check_kafka_health()
        }
        
        for service_name, service_config in self.services.items():
            if service_name in self.processes:
                process_info = self.processes[service_name]
                process = process_info['process']
                
                # Check if process is still running
                is_running = process.poll() is None
                
                # Check health endpoint
                health_status = 'unknown'
                if is_running:
                    try:
                        health_url = f"http://localhost:{service_config['port']}{service_config['health_endpoint']}"
                        response = requests.get(health_url, timeout=2)
                        health_status = 'healthy' if response.status_code == 200 else 'unhealthy'
                    except requests.exceptions.RequestException:
                        health_status = 'unreachable'
                else:
                    health_status = 'stopped'
                
                status['services'][service_name] = {
                    'running': is_running,
                    'health': health_status,
                    'port': service_config['port'],
                    'uptime': time.time() - process_info['start_time'] if is_running else 0
                }
            else:
                status['services'][service_name] = {
                    'running': False,
                    'health': 'stopped',
                    'port': service_config['port'],
                    'uptime': 0
                }
        
        return status
    
    def monitor_services(self):
        """Monitor running services and restart if needed"""
        logger.info("Starting service monitoring...")
        
        while not self.shutdown_event.is_set():
            try:
                for service_name in list(self.processes.keys()):
                    process_info = self.processes[service_name]
                    process = process_info['process']
                    
                    # Check if process is still running
                    if process.poll() is not None:
                        logger.warning("Service process died", service=service_name)
                        
                        # Remove from processes
                        del self.processes[service_name]
                        
                        # Restart if it's a required service
                        if self.services[service_name]['required']:
                            logger.info("Restarting required service", service=service_name)
                            self.start_service(service_name)
                
                # Wait before next check
                self.shutdown_event.wait(10)
                
            except Exception as e:
                logger.error("Error in service monitoring", error=str(e))
                self.shutdown_event.wait(10)
    
    def run(self) -> bool:
        """Run the complete system"""
        logger.info("Starting Kafka E-commerce System...")
        
        try:
            # Check prerequisites
            if not self.check_prerequisites():
                return False
            
            # Setup Kafka topics
            if not self.setup_kafka_topics():
                return False
            
            # Start all services
            if not self.start_all_services():
                logger.error("Failed to start all required services")
                self.stop_all_services()
                return False
            
            self.running = True
            
            # Start monitoring in background
            monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
            monitor_thread.start()
            
            # Print system status
            self.print_system_info()
            
            # Wait for shutdown signal
            logger.info("System is running. Press Ctrl+C to shutdown.")
            
            try:
                while not self.shutdown_event.is_set():
                    self.shutdown_event.wait(1)
            except KeyboardInterrupt:
                pass
            
            return True
            
        except Exception as e:
            logger.error("Error running system", error=str(e))
            return False
        
        finally:
            self.shutdown()
    
    def print_system_info(self):
        """Print system information and endpoints"""
        print("\n" + "="*60)
        print("KAFKA E-COMMERCE SYSTEM - RUNNING")
        print("="*60)
        
        status = self.get_system_status()
        
        print(f"\nKafka Health: {'✓ Healthy' if status['kafka_health'] else '✗ Unhealthy'}")
    
    def _check_kafka_health(self) -> bool:
        """Check Kafka health using connection manager"""
        try:
            connection_manager = KafkaConnectionManager()
            return health_check_kafka(connection_manager)
        except Exception:
            return False
        
        print("\nService Status:")
        for service_name, service_status in status['services'].items():
            health_icon = "✓" if service_status['health'] == 'healthy' else "✗"
            uptime = int(service_status['uptime'])
            print(f"  {health_icon} {service_name:20} - Port {service_status['port']:5} - Uptime: {uptime}s")
        
        print("\nService Endpoints:")
        for service_name, config in self.services.items():
            if service_name in self.processes:
                print(f"  • {service_name:20} - http://localhost:{config['port']}")
        
        print("\nManagement Endpoints:")
        print(f"  • Monitoring Dashboard  - http://localhost:{Config.MONITORING_SERVICE_PORT}/dashboard")
        print(f"  • Order Orchestrator    - http://localhost:{Config.ORCHESTRATOR_SERVICE_PORT}/flows")
        print(f"  • Kafka UI              - http://localhost:8080")
        
        print("\nTo run tests:")
        print("  python test_suite.py")
        print("  python test_suite.py performance")
        print("  python test_suite.py failure")
        
        print("\n" + "="*60)
    
    def shutdown(self):
        """Shutdown the system"""
        if not self.running:
            return
        
        logger.info("Shutting down system...")
        self.running = False
        self.shutdown_event.set()
        
        # Stop all services
        self.stop_all_services()
        
        logger.info("System shutdown complete")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Kafka E-commerce System Launcher')
    parser.add_argument('--service', help='Start only a specific service')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--test', action='store_true', help='Run tests after startup')
    
    args = parser.parse_args()
    
    launcher = SystemLauncher()
    
    if args.status:
        # Just show status
        status = launcher.get_system_status()
        print(json.dumps(status, indent=2))
        return
    
    if args.service:
        # Start only specific service
        if args.service not in launcher.services:
            print(f"Unknown service: {args.service}")
            print(f"Available services: {list(launcher.services.keys())}")
            return
        
        if not launcher.check_prerequisites():
            return
        
        if not launcher.setup_kafka_topics():
            return
        
        success = launcher.start_service(args.service)
        if success:
            print(f"Service {args.service} started successfully")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                launcher._stop_service(args.service)
        else:
            print(f"Failed to start service {args.service}")
        return
    
    # Run complete system
    success = launcher.run()
    
    if success and args.test:
        print("\nRunning integration tests...")
        import subprocess
        subprocess.run([sys.executable, 'test_suite.py'])
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()