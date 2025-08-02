#!/usr/bin/env python3
import requests
import time

def test_order_service():
    print("Testing Order Service health endpoint...")
    
    try:
        print("Making request to http://localhost:5001/health...")
        start_time = time.time()
        
        response = requests.get('http://localhost:5001/health', timeout=10)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"Response received in {response_time:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Order Service is healthy!")
            return True
        else:
            print(f"❌ Order Service returned status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 10 seconds")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    test_order_service()