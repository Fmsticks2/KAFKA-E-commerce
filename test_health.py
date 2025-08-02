#!/usr/bin/env python3
import requests
import sys

def test_service_health(service_name, port):
    try:
        print(f"Testing {service_name} on port {port}...")
        response = requests.get(f'http://localhost:{port}/health', timeout=5)
        print(f"✅ {service_name} (port {port}): {response.status_code} - {response.text}")
        return True
    except Exception as e:
        print(f"❌ {service_name} (port {port}): {str(e)}")
        return False

if __name__ == '__main__':
    services = [
        ('Order Service', 5001),
        ('Payment Service', 5002),
        ('Inventory Service', 5003),
        ('Notification Service', 5004),
        ('Monitoring Service', 5005)
    ]
    
    print("Testing service health endpoints...")
    all_healthy = True
    
    for service_name, port in services:
        if not test_service_health(service_name, port):
            all_healthy = False
    
    if all_healthy:
        print("\n🎉 All services are healthy!")
        sys.exit(0)
    else:
        print("\n⚠️  Some services are not responding")
        sys.exit(1)