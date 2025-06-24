#!/usr/bin/env python3
"""
Debug script to test the Flask application
"""
from app import app

if __name__ == "__main__":
    with app.test_client() as client:
        print("Testing Flask application...")
        
        # Test main route
        response = client.get('/')
        print(f"Status Code: {response.status_code}")
        print(f"Content Type: {response.content_type}")
        print(f"Content Length: {len(response.data)}")
        
        # Check if content exists
        content = response.data.decode('utf-8')
        if 'CONSELHEIRO TUTELAR' in content:
            print("✓ Expected content found")
        else:
            print("✗ Expected content missing")
            print("First 500 characters:")
            print(content[:500])
            
        # Check for template errors
        if response.status_code != 200:
            print(f"Error response: {content}")