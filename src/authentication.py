import streamlit as st
import hashlib
import sqlite3
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import re
import os
from pathlib import Path

class AuthenticationManager:
    """Minimal working authentication system"""
    
    def __init__(self, db_path: str = "data_storage/auth.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize authentication database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    full_name TEXT,
                    role TEXT DEFAULT 'user',
                    is_active BOOLEAN DEFAULT 1,
                    created_date TEXT,
                    last_login TEXT,
                    login_attempts INTEGER DEFAULT 0,
                    locked_until TEXT
                )
            ''')
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_email TEXT,
                    created_date TEXT,
                    expires_date TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Email whitelist table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_whitelist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    role TEXT DEFAULT 'user',
                    added_by TEXT,
                    added_date TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    notes TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
            # Create default admin
            self._create_default_admin()
            
        except Exception as e:
            self.logger.error(f"Database init error: {str(e)}")
    
    def _create_default_admin(self):
        """Create default admin user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0]
            
            if user_count == 0:
                admin_email = "admin@dataanalyzer.com"
                admin_password = "admin123"
                
                salt = secrets.token_hex(32)
                password_hash = hashlib.pbkdf2_hmac('sha256', admin_password.encode(), salt.encode(), 100000).hex()
                
                cursor.execute('''
                    INSERT INTO users (email, password_hash, salt, full_name, role, is_active, created_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (admin_email, password_hash, salt, "System Administrator", "admin", True, datetime.now().isoformat()))
                
                conn.commit()
            
            conn.close()
        except Exception as e:
            self.logger.error(f"Admin creation error: {str(e)}")
    
    def authenticate_user(self, email: str, password: str, ip_address: str = "", user_agent: str = "") -> Tuple[bool, str, Dict[str, Any]]:
        """Authenticate user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT password_hash, salt, full_name, role FROM users WHERE email = ? AND is_active = 1', (email,))
            user_data = cursor.fetchone()
            
            if not user_data:
                conn.close()
                return False, "Invalid credentials", {}
            
            password_hash, salt, full_name, role = user_data
            
            # Verify password
            if hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() != password_hash:
                conn.close()
                return False, "Invalid credentials", {}
            
            # Create session
            session_id = secrets.token_urlsafe(32)
            expires_date = datetime.now() + timedelta(hours=24)
            
            cursor.execute('''
                INSERT INTO user_sessions (session_id, user_email, created_date, expires_date, is_active)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, email, datetime.now().isoformat(), expires_date.isoformat(), True))
            
            conn.commit()
            conn.close()
            
            return True, "Login successful", {
                'email': email,
                'full_name': full_name,
                'role': role,
                'session_id': session_id
            }
            
        except Exception as e:
            self.logger.error(f"Auth error: {str(e)}")
            return False, "Authentication failed", {}
    
    def validate_session(self, session_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Validate session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.user_email, u.full_name, u.role
                FROM user_sessions s
                JOIN users u ON s.user_email = u.email
                WHERE s.session_id = ? AND s.is_active = 1 AND u.is_active = 1
            ''', (session_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return True, {
                    'email': result[0],
                    'full_name': result[1],
                    'role': result[2],
                    'session_id': session_id
                }
            
            return False, {}
            
        except Exception as e:
            self.logger.error(f"Session validation error: {str(e)}")
            return False, {}
    
    def logout_user(self, session_id: str):
        """Logout user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('UPDATE user_sessions SET is_active = 0 WHERE session_id = ?', (session_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Logout error: {str(e)}")
    
    def list_users(self, requester_role: str) -> List[Dict[str, Any]]:
        """List users"""
        if requester_role != 'admin':
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT email, full_name, role, is_active, created_date, last_login FROM users')
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'email': row[0],
                    'full_name': row[1],
                    'role': row[2],
                    'is_active': bool(row[3]),
                    'created_date': row[4],
                    'last_login': row[5]
                })
            
            conn.close()
            return users
        except Exception as e:
            self.logger.error(f"List users error: {str(e)}")
            return []
    
    def update_user_role(self, email: str, new_role: str, updated_by: str) -> bool:
        """Update user role"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET role = ? WHERE email = ?', (new_role, email))
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            self.logger.error(f"Update role error: {str(e)}")
            return False
    
    def deactivate_user(self, email: str, deactivated_by: str) -> bool:
        """Deactivate user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_active = 0 WHERE email = ?', (email,))
            cursor.execute('UPDATE user_sessions SET is_active = 0 WHERE user_email = ?', (email,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"Deactivate error: {str(e)}")
            return False
    
    def add_to_whitelist(self, email: str, role: str, added_by: str, notes: str = "") -> bool:
        """Add to whitelist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO email_whitelist (email, role, added_by, added_date, is_active, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (email, role, added_by, datetime.now().isoformat(), True, notes))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"Whitelist add error: {str(e)}")
            return False
    
    def list_whitelist(self, requester_role: str) -> List[Dict[str, Any]]:
        """List whitelist"""
        if requester_role != 'admin':
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT email, role, added_by, added_date, is_active, notes FROM email_whitelist ORDER BY added_date DESC')
            
            whitelist = []
            for row in cursor.fetchall():
                whitelist.append({
                    'email': row[0],
                    'role': row[1],
                    'added_by': row[2],
                    'added_date': row[3],
                    'is_active': bool(row[4]),
                    'notes': row[5] or ""
                })
            
            conn.close()
            return whitelist
        except Exception as e:
            self.logger.error(f"List whitelist error: {str(e)}")
            return []
    
    def register_user(self, email: str, password: str, full_name: str, invitation_token: str = None) -> Tuple[bool, str]:
        """Register user with whitelist check"""
        try:
            # Basic validation
            if len(password) < 8:
                return False, "Password must be at least 8 characters"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT email FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                conn.close()
                return False, "User already exists"
            
            # Check whitelist
            cursor.execute('SELECT role FROM email_whitelist WHERE email = ? AND is_active = 1', (email,))
            whitelist_entry = cursor.fetchone()
            
            if not whitelist_entry:
                conn.close()
                return False, "Email not authorized. Contact administrator."
            
            # Create user
            salt = secrets.token_hex(32)
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
            
            cursor.execute('''
                INSERT INTO users (email, password_hash, salt, full_name, role, is_active, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (email, password_hash, salt, full_name, whitelist_entry[0], True, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            return True, "User registered successfully"
            
        except Exception as e:
            self.logger.error(f"Registration error: {str(e)}")
            return False, "Registration failed"

def get_auth_manager() -> AuthenticationManager:
    """Get auth manager"""
    if 'auth_manager' not in st.session_state:
        st.session_state.auth_manager = AuthenticationManager()
    return st.session_state.auth_manager

def require_authentication() -> Optional[Dict[str, Any]]:
    """Require authentication"""
    auth_manager = get_auth_manager()
    
    # Check existing session
    if 'user_info' in st.session_state and 'session_id' in st.session_state:
        is_valid, user_info = auth_manager.validate_session(st.session_state.session_id)
        if is_valid:
            st.session_state.user_info = user_info
            return user_info
        else:
            del st.session_state.user_info
            del st.session_state.session_id
    
    # Show auth interface
    return show_auth_interface(auth_manager)

def show_auth_interface(auth_manager: AuthenticationManager) -> Optional[Dict[str, Any]]:
    """Show auth interface"""
    st.title("🔐 Multi-Dataset Analyzer")
    st.markdown("*Secure access to collaborative data analysis*")
    
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
    
    with tab1:
        return show_login_form(auth_manager)
    
    with tab2:
        return show_registration_form(auth_manager)

def show_login_form(auth_manager: AuthenticationManager) -> Optional[Dict[str, Any]]:
    """Show login form"""
    st.subheader("Login to Your Account")
    
    with st.form("login_form"):
        email = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("🔑 Login", type="primary")
        
        if login_button and email and password:
            success, message, user_info = auth_manager.authenticate_user(email, password)
            if success:
                st.session_state.user_info = user_info
                st.session_state.session_id = user_info['session_id']
                st.success(f"Welcome back, {user_info['full_name']}!")
                st.rerun()
            else:
                st.error(f"❌ {message}")
    
    return None

def show_registration_form(auth_manager: AuthenticationManager, invitation_token: str = None) -> Optional[Dict[str, Any]]:
    """Show registration form"""
    st.subheader("Create New Account")
    st.info("Your email must be pre-authorized by an administrator.")
    
    email = st.text_input("Email Address")
    full_name = st.text_input("Full Name")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    
    if st.button("Create Account"):
        if email and full_name and password and confirm_password:
            if password == confirm_password:
                success, message = auth_manager.register_user(email, password, full_name)
                if success:
                    st.success("Account created! Please login.")
                else:
                    st.error(message)
            else:
                st.error("Passwords don't match")
        else:
            st.error("Please fill all fields")
    
    return None
