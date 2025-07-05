#!/usr/bin/env python3
"""
Azure Communication Services Setup Script for SwasthCare

This script helps you set up Azure Communication Services for email functionality.
Run this script to create the necessary Azure resources for sending emails.

Prerequisites:
- Azure CLI installed and logged in
- Azure subscription with appropriate permissions
- Python with azure-mgmt-communication package installed

Usage:
    python setup_azure_communication.py
"""

import os
import sys
from datetime import datetime

def print_header():
    print("=" * 60)
    print("SwasthCare - Azure Communication Services Setup")
    print("=" * 60)
    print()

def print_step(step_num, title):
    print(f"\n🔧 Step {step_num}: {title}")
    print("-" * 40)

def print_info(message):
    print(f"ℹ️  {message}")

def print_success(message):
    print(f"✅ {message}")

def print_warning(message):
    print(f"⚠️  {message}")

def print_error(message):
    print(f"❌ {message}")

def main():
    print_header()
    
    print_info("This script will guide you through setting up Azure Communication Services")
    print_info("for your SwasthCare application's email functionality.")
    print()
    
    # Get user input for configuration
    print_step(1, "Configuration Setup")
    
    resource_group = input("Enter your Azure Resource Group name: ").strip()
    if not resource_group:
        print_error("Resource group name is required!")
        sys.exit(1)
    
    location = input("Enter Azure region (e.g., 'East US'): ").strip() or "East US"
    
    communication_service_name = input("Enter Communication Service name (e.g., 'swasthcare-communication'): ").strip()
    if not communication_service_name:
        communication_service_name = "swasthcare-communication"
    
    email_service_name = input("Enter Email Service name (e.g., 'swasthcare-email'): ").strip()
    if not email_service_name:
        email_service_name = "swasthcare-email"
    
    print()
    print_step(2, "Azure CLI Commands to Execute")
    
    print_info("Execute the following Azure CLI commands in order:")
    print()
    
    # Communication Service
    print("# 1. Create Azure Communication Services resource")
    print(f"az communication create \\")
    print(f"  --name {communication_service_name} \\")
    print(f"  --resource-group {resource_group} \\")
    print(f"  --location '{location}' \\")
    print(f"  --data-location 'United States'")
    print()
    
    # Email Communication Service
    print("# 2. Create Email Communication Services resource")
    print(f"az communication email create \\")
    print(f"  --name {email_service_name} \\")
    print(f"  --resource-group {resource_group} \\")
    print(f"  --location 'Global' \\")
    print(f"  --data-location 'United States'")
    print()
    
    # Azure Managed Domain (easiest option)
    print("# 3. Add Azure Managed Domain (easiest setup)")
    print(f"az communication email domain create \\")
    print(f"  --name 'AzureManagedDomain' \\")
    print(f"  --resource-group {resource_group} \\")
    print(f"  --email-service-name {email_service_name} \\")
    print(f"  --location 'Global' \\")
    print(f"  --domain-management 'AzureManaged'")
    print()
    
    # Link domain to communication service
    print("# 4. Get the domain resource ID (run this to get the ID)")
    print(f"az communication email domain show \\")
    print(f"  --name 'AzureManagedDomain' \\")
    print(f"  --resource-group {resource_group} \\")
    print(f"  --email-service-name {email_service_name} \\")
    print(f"  --query 'id' -o tsv")
    print()
    
    print("# 5. Link the domain to Communication Service (replace <DOMAIN_ID> with output from step 4)")
    print(f"az communication update \\")
    print(f"  --name {communication_service_name} \\")
    print(f"  --resource-group {resource_group} \\")
    print(f"  --linked-domains '<DOMAIN_ID>'")
    print()
    
    # Get connection string
    print("# 6. Get the connection string")
    print(f"az communication list-key \\")
    print(f"  --name {communication_service_name} \\")
    print(f"  --resource-group {resource_group}")
    print()
    
    print_step(3, "Update Configuration")
    print_info("After running the above commands:")
    print("1. Copy the connection string from step 6")
    print("2. Update your .env file with:")
    print(f"   AZURE_COMMUNICATION_CONNECTION_STRING=\"<connection_string_from_step_6>\"")
    print(f"   AZURE_COMMUNICATION_FROM_EMAIL=\"DoNotReply@<domain_from_step_4>.azurecomm.net\"")
    print()
    
    print_step(4, "Alternative: Use Azure Portal")
    print_info("You can also set this up using the Azure Portal:")
    print("1. Go to https://portal.azure.com")
    print("2. Create 'Communication Services' resource")
    print("3. Create 'Email Communication Services' resource")
    print("4. Add Azure Managed Domain to Email Service")
    print("5. Connect the domain to Communication Service")
    print("6. Get connection string from Keys section")
    print()
    
    print_success("Setup guide complete!")
    print_warning("Remember to update your .env file with the actual values after creating the resources.")
    print()

if __name__ == "__main__":
    main()
