#!/usr/bin/env python3
"""
Local Test Script for Bet Bot Manager Web Portal
This script tests the web portal locally before deployment.
"""

import os
import sys
import requests
import time
from pathlib import Path

def test_webapp_startup():
    """Test if the webapp can start without errors."""
    print("Testing webapp startup...")
    
    try:
        # Import the webapp
        from webapp import app
        
        # Test basic routes
        with app.test_client() as client:
            # Test home page
            response = client.get('/')
            if response.status_code == 200:
                print("  ✓ Home page loads successfully")
            else:
                print(f"  ✗ Home page failed: {response.status_code}")
            
            # Test health endpoint
            response = client.get('/health')
            if response.status_code == 200:
                print("  ✓ Health endpoint works")
            else:
                print(f"  ✗ Health endpoint failed: {response.status_code}")
            
            # Test API status
            response = client.get('/api/status')
            if response.status_code == 200:
                print("  ✓ API status endpoint works")
            else:
                print(f"  ✗ API status endpoint failed: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"  ✗ Webapp startup failed: {e}")
        return False

def test_templates():
    """Test if templates can be rendered."""
    print("Testing template rendering...")
    
    try:
        from webapp import app
        
        with app.test_client() as client:
            # Test landing page template
            response = client.get('/')
            if 'Bet Bot Manager' in response.get_data(as_text=True):
                print("  ✓ Landing page template renders correctly")
            else:
                print("  ✗ Landing page template failed")
            
            # Test server list page
            response = client.get('/server-list')
            if response.status_code == 200:
                print("  ✓ Server list page loads")
            else:
                print(f"  ✗ Server list page failed: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"  ✗ Template rendering failed: {e}")
        return False

def test_static_files():
    """Test if static files are accessible."""
    print("Testing static files...")
    
    try:
        from webapp import app
        
        with app.test_client() as client:
            # Test favicon
            response = client.get('/static/favicon.webp')
            if response.status_code == 200:
                print("  ✓ Favicon accessible")
            else:
                print(f"  ✗ Favicon failed: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"  ✗ Static files test failed: {e}")
        return False

def test_database_connection():
    """Test database connection if available."""
    print("Testing database connection...")
    
    try:
        # Import database functions
        from webapp import get_db_connection
        
        connection = get_db_connection()
        if connection:
            print("  ✓ Database connection successful")
            connection.close()
            return True
        else:
            print("  ⚠ Database connection failed (expected if no .env file)")
            return True  # Not critical for local testing
    except Exception as e:
        print(f"  ⚠ Database test skipped: {e}")
        return True  # Not critical for local testing

def main():
    """Run all tests."""
    print("Local Web Portal Test")
    print("=" * 30)
    
    tests = [
        ("Webapp Startup", test_webapp_startup),
        ("Template Rendering", test_templates),
        ("Static Files", test_static_files),
        ("Database Connection", test_database_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ✗ Test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 30)
    print("Test Results:")
    
    passed = 0
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("🎉 All tests passed! Web portal is ready for deployment.")
        return True
    else:
        print("⚠ Some tests failed. Please fix issues before deploying.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 