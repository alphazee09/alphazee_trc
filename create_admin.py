#!/usr/bin/env python3
"""
Script to create a default admin user for the Alphazee09 system.
This should be run once after initial setup.
"""

import os
import sys
import requests
import json

# Add the src directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def create_default_admin():
    """Create a default admin user"""
    
    # Admin details
    admin_data = {
        "username": "admin",
        "email": "admin@alphazee09.com",
        "password": "Admin123!",
        "first_name": "System",
        "last_name": "Administrator",
        "role": "super_admin"
    }
    
    # API endpoint
    base_url = "https://zmhqivcm6ly1.manus.space/api"
    # For local testing, use: base_url = "http://localhost:5001/api"
    
    register_url = f"{base_url}/admin/register"
    
    try:
        print("Creating default admin user...")
        print(f"Username: {admin_data['username']}")
        print(f"Email: {admin_data['email']}")
        print(f"Password: {admin_data['password']}")
        print(f"Role: {admin_data['role']}")
        print()
        
        # Make the registration request
        response = requests.post(
            register_url,
            headers={"Content-Type": "application/json"},
            json=admin_data
        )
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Admin user created successfully!")
            print(f"Admin ID: {result['admin']['id']}")
            print(f"Username: {result['admin']['username']}")
            print(f"Email: {result['admin']['email']}")
            print(f"Role: {result['admin']['role']}")
            print()
            print("You can now login to the admin panel using these credentials.")
            
        elif response.status_code == 400:
            error = response.json()
            if "already exists" in error.get('message', ''):
                print("⚠️  Admin user already exists with this username or email.")
                print("You can use the existing credentials to login.")
            else:
                print(f"❌ Error creating admin user: {error.get('message', 'Unknown error')}")
                
        else:
            print(f"❌ Failed to create admin user. Status code: {response.status_code}")
            try:
                error = response.json()
                print(f"Error: {error.get('message', 'Unknown error')}")
            except:
                print(f"Response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to the API server.")
        print("Make sure the server is running and accessible.")
        
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")

def test_admin_login():
    """Test admin login functionality"""
    
    login_data = {
        "username": "admin",
        "password": "Admin123!"
    }
    
    base_url = "https://zmhqivcm6ly1.manus.space/api"
    # For local testing, use: base_url = "http://localhost:5001/api"
    
    login_url = f"{base_url}/admin/login"
    
    try:
        print("Testing admin login...")
        
        response = requests.post(
            login_url,
            headers={"Content-Type": "application/json"},
            json=login_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Admin login successful!")
            print(f"Token: {result['token'][:50]}...")
            print(f"Admin: {result['admin']['username']} ({result['admin']['role']})")
            
            # Test getting admin profile
            token = result['token']
            profile_url = f"{base_url}/admin/profile"
            
            profile_response = requests.get(
                profile_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )
            
            if profile_response.status_code == 200:
                profile = profile_response.json()
                print("✅ Admin profile retrieved successfully!")
                print(f"Last login: {profile['admin']['last_login']}")
            else:
                print("⚠️  Could not retrieve admin profile")
                
        else:
            print(f"❌ Admin login failed. Status code: {response.status_code}")
            try:
                error = response.json()
                print(f"Error: {error.get('message', 'Unknown error')}")
            except:
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ An error occurred during login test: {str(e)}")

if __name__ == "__main__":
    print("=== Alphazee09 Admin Setup Script ===")
    print()
    
    create_default_admin()
    print()
    print("-" * 50)
    print()
    test_admin_login()
    
    print()
    print("=== Setup Complete ===")
    print()
    print("📖 API Documentation: See API_DOCUMENTATION.md")
    print("🌐 Base URL: https://zmhqivcm6ly1.manus.space/api")
    print("👤 Default Admin Credentials:")
    print("   Username: admin")
    print("   Password: Admin123!")
    print("   Email: admin@alphazee09.com")
    print()
    print("🔗 Admin Endpoints:")
    print("   POST /api/admin/login")
    print("   GET  /api/admin/dashboard")
    print("   GET  /api/admin/users")
    print("   POST /api/admin/send-crypto")
    print("   GET  /api/admin/wallets")
    print()
    print("Happy coding! 🚀")