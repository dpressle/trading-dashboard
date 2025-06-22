#!/usr/bin/env python3
"""
Test script to debug IBKR connection issues
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ibkr_client import fetch_ibkr_account_details, fetch_ibkr_tickle

def test_ibkr_connection():
    """Test IBKR connection directly"""
    print("=== Testing IBKR Connection Directly ===\n")

    print(f"1. Testing IBKR tickle...")
    try:
        fetch_ibkr_tickle()
        print(f"   ✅ IBKR tickle successful")
    except Exception as e:
        print(f"   ❌ IBKR tickle failed: {e}")
        return False

    print(f"\n2. Testing account details fetch...")
    try:
        account_details = fetch_ibkr_account_details()
        if account_details:
            print(f"   ✅ Account details fetched successfully")
            print(f"   📊 Account ID: {account_details.get('accountId', 'N/A')}")
            print(f"   📊 Name: {account_details.get('displayName', 'N/A')}")
            print(f"   📊 Type: {account_details.get('type', 'N/A')}")
            print(f"   📊 Currency: {account_details.get('currency', 'N/A')}")
            return True
        else:
            print(f"   ❌ Account details returned None/empty")
            return False
    except Exception as e:
        print(f"   ❌ Account details fetch failed: {e}")
        return False

def check_environment():
    """Check environment variables"""
    print("=== Checking Environment Variables ===\n")

    env_vars = {
        'IBKR_GATEWAY_URL': os.environ.get('IBKR_GATEWAY_URL', 'Not set (default: localhost)'),
        'IBIND_PORT': os.environ.get('IBIND_PORT', 'Not set (default: 5001)'),
        'IBIND_ACCOUNT_ID': os.environ.get('IBIND_ACCOUNT_ID', 'Not set')
    }

    for var, value in env_vars.items():
        print(f"{var}: {value}")

    print(f"\nExpected IBKR Gateway URL: http://{env_vars['IBKR_GATEWAY_URL']}:{env_vars['IBIND_PORT']}")

if __name__ == "__main__":
    print("Starting IBKR connection debug...")
    print(f"Time: {datetime.now()}")
    print()

    check_environment()
    print("\n" + "="*50)

    success = test_ibkr_connection()

    print("\n" + "="*50)
    if success:
        print("✅ IBKR connection is working!")
        print("The issue might be in the Flask app logic.")
    else:
        print("❌ IBKR connection is failing!")
        print("Check your IBKR Gateway configuration and network connectivity.")
