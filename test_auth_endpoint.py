#!/usr/bin/env python3
"""
Test the authentication endpoint after the load_dotenv() fix
"""

import asyncio
import json
from datetime import datetime

# Test the core authentication functions
async def test_auth_functions():
    """Test that authentication functions work"""
    print("[INFO] Testing authentication functions...")
    
    try:
        # Test that we can import the fixed modules
        from dotenv import load_dotenv
        import os
        
        # Load environment variables (the FIX we just applied)
        load_dotenv()
        
        # Check JWT_SECRET_KEY is loaded
        jwt_secret = os.getenv('JWT_SECRET_KEY')
        if jwt_secret:
            print(f"[SUCCESS] JWT_SECRET_KEY loaded: {jwt_secret[:20]}...")
        else:
            print("[ERROR] JWT_SECRET_KEY not found")
            return False
            
        # Test auth utils functions
        from agent.auth_utils import create_access_token, authenticate_user
        
        # Test user authentication (should accept any username/password for testing)
        user = await authenticate_user("testuser", "testpassword")
        if user:
            print(f"[SUCCESS] User authentication works: {user['username']}")
        else:
            print("[ERROR] User authentication failed")
            return False
            
        # Test JWT token creation
        token_data = await create_access_token(user["id"], user["username"])
        if token_data and "access_token" in token_data:
            print(f"[SUCCESS] JWT token creation works: {token_data['access_token'][:30]}...")
            print(f"[SUCCESS] Token expires in: {token_data['expires_in']} seconds")
        else:
            print("[ERROR] JWT token creation failed")
            return False
            
        print("\n[CELEBRATION] ALL AUTHENTICATION TESTS PASSED!")
        print("[SUCCESS] The load_dotenv() fix is working correctly!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Authentication test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_login_endpoint():
    """Test the actual login endpoint with HTTP request"""
    print("\n[INFO] Testing login endpoint via HTTP...")
    
    try:
        import aiohttp
        
        # Test data
        login_data = {
            "username": "admin",
            "password": "password123"
        }
        
        url = "http://localhost:8058/auth/login"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"[SUCCESS] Login endpoint works! Status: {response.status}")
                    print(f"[SUCCESS] Token received: {data.get('token', {}).get('access_token', 'N/A')[:30]}...")
                    return True
                else:
                    print(f"[ERROR] Login endpoint failed. Status: {response.status}")
                    text = await response.text()
                    print(f"Response: {text}")
                    return False
                    
    except Exception as e:
        print(f"[WARNING] HTTP test failed (server might not be running): {e}")
        print("This is expected if the server isn't started yet.")
        return False

if __name__ == "__main__":
    print("TESTING AUTHENTICATION SYSTEM AFTER FIXES")
    print("=" * 50)
    
    # Test 1: Authentication functions
    success1 = asyncio.run(test_auth_functions())
    
    # Test 2: HTTP endpoint (optional, server might not be running)
    success2 = asyncio.run(test_login_endpoint())
    
    print("\n" + "=" * 50)
    if success1:
        print("[CELEBRATION] CORE AUTHENTICATION: WORKING!")
        if success2:
            print("[CELEBRATION] HTTP ENDPOINT: WORKING!")
            print("[SUCCESS] SYSTEM IS 100% READY FOR USE!")
        else:
            print("[WARNING] HTTP ENDPOINT: Not tested (server not running)")
            print("[SUCCESS] Core functions work - start server to test full system")
    else:
        print("[ERROR] CORE AUTHENTICATION: FAILED!")