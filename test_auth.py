# For tesing authentication system in Django

#!/usr/bin/env python
"""
Test script to verify authentication system is working correctly
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SwasthCare_seller.settings")
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

def test_authentication_system():
    """Test the authentication system"""
    print("🔍 Testing SwasthCare Authentication System")
    print("=" * 50)
    
    # Test 1: Check if authentication URLs are accessible
    client = Client()
    
    print("\n1. Testing URL accessibility:")
    
    # Test login page
    try:
        response = client.get('/login/')
        print(f"   ✅ Login page: {response.status_code} - {'OK' if response.status_code == 200 else 'FAILED'}")
    except Exception as e:
        print(f"   ❌ Login page failed: {e}")
    
    # Test register page
    try:
        response = client.get('/register/')
        print(f"   ✅ Register page: {response.status_code} - {'OK' if response.status_code == 200 else 'FAILED'}")
    except Exception as e:
        print(f"   ❌ Register page failed: {e}")
    
    # Test profile page (should redirect to login)
    try:
        response = client.get('/profile/')
        print(f"   ✅ Profile page (unauthenticated): {response.status_code} - {'OK' if response.status_code == 302 else 'FAILED'}")
    except Exception as e:
        print(f"   ❌ Profile page failed: {e}")
    
    print("\n2. Testing user creation:")
    
    # Create a test user
    try:
        # Check if test user already exists
        if User.objects.filter(username='testuser').exists():
            User.objects.filter(username='testuser').delete()
        
        user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        print(f"   ✅ Test user created: {user.username}")
    except Exception as e:
        print(f"   ❌ User creation failed: {e}")
        return
    
    print("\n3. Testing authentication flow:")
    
    # Test login
    try:
        login_successful = client.login(username='testuser', password='testpass123')
        print(f"   ✅ Login: {'OK' if login_successful else 'FAILED'}")
    except Exception as e:
        print(f"   ❌ Login failed: {e}")
    
    # Test access to protected view
    try:
        response = client.get('/profile/')
        print(f"   ✅ Profile page (authenticated): {response.status_code} - {'OK' if response.status_code == 200 else 'FAILED'}")
    except Exception as e:
        print(f"   ❌ Profile access failed: {e}")
    
    # Test seller portal access
    try:
        response = client.get('/seller/upload/')
        print(f"   ✅ Seller portal: {response.status_code} - {'OK' if response.status_code == 200 else 'FAILED'}")
    except Exception as e:
        print(f"   ❌ Seller portal access failed: {e}")
    
    # Test logout
    try:
        client.logout()
        response = client.get('/profile/')
        print(f"   ✅ Logout: {response.status_code} - {'OK' if response.status_code == 302 else 'FAILED'}")
    except Exception as e:
        print(f"   ❌ Logout failed: {e}")
    
    print("\n4. Testing form submission:")
    
    # Test registration form
    try:
        response = client.post('/register/', {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'user_type': 'consumer',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        })
        print(f"   ✅ Registration form: {response.status_code} - {'OK' if response.status_code in [200, 302] else 'FAILED'}")
    except Exception as e:
        print(f"   ❌ Registration form failed: {e}")
    
    # Clean up test users
    try:
        User.objects.filter(username__in=['testuser', 'newuser']).delete()
        print(f"   ✅ Test users cleaned up")
    except Exception as e:
        print(f"   ❌ Cleanup failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Authentication system test completed!")
    print("🌐 You can now test the system at: http://127.0.0.1:8000/")
    print("📝 Available endpoints:")
    print("   - http://127.0.0.1:8000/login/")
    print("   - http://127.0.0.1:8000/register/")
    print("   - http://127.0.0.1:8000/profile/")
    print("   - http://127.0.0.1:8000/logout/")

if __name__ == '__main__':
    test_authentication_system()
