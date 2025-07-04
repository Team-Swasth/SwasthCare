#!/usr/bin/env python
"""
Simple user management utility for SwasthCare
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

def create_test_users():
    """Create test users for demonstration"""
    print("🔧 Creating test users...")
    
    # Create seller user
    if not User.objects.filter(username='seller_demo').exists():
        seller = User.objects.create_user(
            username='seller_demo',
            email='seller@swasthcare.com',
            password='demo123',
            first_name='Demo',
            last_name='Seller'
        )
        print(f"✅ Created seller user: {seller.username}")
    else:
        print("ℹ️  Seller demo user already exists")
    
    # Create consumer user
    if not User.objects.filter(username='consumer_demo').exists():
        consumer = User.objects.create_user(
            username='consumer_demo',
            email='consumer@swasthcare.com',
            password='demo123',
            first_name='Demo',
            last_name='Consumer'
        )
        print(f"✅ Created consumer user: {consumer.username}")
    else:
        print("ℹ️  Consumer demo user already exists")
    
    print("\n📝 Test Credentials:")
    print("Seller Demo:")
    print("  Username: seller_demo")
    print("  Password: demo123")
    print("\nConsumer Demo:")
    print("  Username: consumer_demo")
    print("  Password: demo123")

def list_users():
    """List all users"""
    print("👥 Current Users:")
    print("-" * 40)
    for user in User.objects.all():
        print(f"  {user.username} ({user.email}) - {user.first_name} {user.last_name}")

def main():
    """Main function"""
    print("🏥 SwasthCare User Management")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'create':
            create_test_users()
        elif command == 'list':
            list_users()
        else:
            print("Usage: python manage_users.py [create|list]")
    else:
        print("Available commands:")
        print("  create - Create demo users")
        print("  list   - List all users")
        print("\nUsage: python manage_users.py [create|list]")

if __name__ == '__main__':
    main()
