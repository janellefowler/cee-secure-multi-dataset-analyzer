#!/usr/bin/env python3
"""
Setup script for Content Effectiveness Engine authentication
Run this script to set up user passwords and authentication configuration
"""

import bcrypt
import yaml
import getpass
import os

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def setup_users():
    """Interactive setup for user authentication"""
    print("Content Effectiveness Engine - Authentication Setup")
    print("=" * 50)
    
    # Load existing config or create new one
    config_file = 'config.yaml'
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
    else:
        config = {
            'credentials': {'usernames': {}},
            'cookie': {
                'expiry_days': 30,
                'key': 'some_signature_key_change_this',
                'name': 'some_cookie_name'
            }
        }
    
    print("\nCurrent users:")
    for username in config['credentials']['usernames'].keys():
        user_info = config['credentials']['usernames'][username]
        print(f"  - {username} ({user_info.get('name', 'No name')}) - {user_info.get('email', 'No email')}")
    
    while True:
        print("\nOptions:")
        print("1. Add new user")
        print("2. Update existing user password")
        print("3. Remove user")
        print("4. Update cookie settings")
        print("5. Save and exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            add_user(config)
        elif choice == '2':
            update_user_password(config)
        elif choice == '3':
            remove_user(config)
        elif choice == '4':
            update_cookie_settings(config)
        elif choice == '5':
            save_config(config, config_file)
            print("Configuration saved successfully!")
            break
        else:
            print("Invalid choice. Please try again.")

def add_user(config):
    """Add a new user"""
    print("\n--- Add New User ---")
    username = input("Username: ").strip()
    
    if username in config['credentials']['usernames']:
        print(f"User '{username}' already exists!")
        return
    
    name = input("Full Name: ").strip()
    email = input("Email: ").strip()
    password = getpass.getpass("Password: ")
    confirm_password = getpass.getpass("Confirm Password: ")
    
    if password != confirm_password:
        print("Passwords don't match!")
        return
    
    if len(password) < 8:
        print("Password must be at least 8 characters long!")
        return
    
    hashed_password = hash_password(password)
    
    config['credentials']['usernames'][username] = {
        'email': email,
        'name': name,
        'password': hashed_password
    }
    
    print(f"User '{username}' added successfully!")

def update_user_password(config):
    """Update existing user password"""
    print("\n--- Update User Password ---")
    username = input("Username: ").strip()
    
    if username not in config['credentials']['usernames']:
        print(f"User '{username}' not found!")
        return
    
    password = getpass.getpass("New Password: ")
    confirm_password = getpass.getpass("Confirm New Password: ")
    
    if password != confirm_password:
        print("Passwords don't match!")
        return
    
    if len(password) < 8:
        print("Password must be at least 8 characters long!")
        return
    
    hashed_password = hash_password(password)
    config['credentials']['usernames'][username]['password'] = hashed_password
    
    print(f"Password updated for user '{username}'!")

def remove_user(config):
    """Remove a user"""
    print("\n--- Remove User ---")
    username = input("Username to remove: ").strip()
    
    if username not in config['credentials']['usernames']:
        print(f"User '{username}' not found!")
        return
    
    confirm = input(f"Are you sure you want to remove user '{username}'? (yes/no): ").strip().lower()
    if confirm == 'yes':
        del config['credentials']['usernames'][username]
        print(f"User '{username}' removed successfully!")
    else:
        print("User removal cancelled.")

def update_cookie_settings(config):
    """Update cookie settings"""
    print("\n--- Update Cookie Settings ---")
    print(f"Current expiry days: {config['cookie']['expiry_days']}")
    print(f"Current cookie name: {config['cookie']['name']}")
    print(f"Current signature key: {config['cookie']['key']}")
    
    expiry = input(f"New expiry days (current: {config['cookie']['expiry_days']}): ").strip()
    if expiry:
        try:
            config['cookie']['expiry_days'] = int(expiry)
        except ValueError:
            print("Invalid number for expiry days!")
            return
    
    cookie_name = input(f"New cookie name (current: {config['cookie']['name']}): ").strip()
    if cookie_name:
        config['cookie']['name'] = cookie_name
    
    signature_key = input(f"New signature key (current: {config['cookie']['key']}): ").strip()
    if signature_key:
        config['cookie']['key'] = signature_key
    
    print("Cookie settings updated!")

def save_config(config, config_file):
    """Save configuration to file"""
    with open(config_file, 'w') as file:
        yaml.dump(config, file, default_flow_style=False, sort_keys=False)

if __name__ == "__main__":
    setup_users()