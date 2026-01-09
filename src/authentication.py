import streamlit as st
import hashlib
import sqlite3
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import re
import os
from pathlib import Path

class AuthenticationManager:
    """Secure authentication system for the multi-dataset analyzer"""
    
    def __init__(self, db_path: str = "data_storage/auth.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_database()
        
        # Email configuration (optional)
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
    
    def _init_database(self):
        """Initialize authentication database"""
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
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_email) REFERENCES users (email)
            )
        ''')
        
        # Invitations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invitations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                invited_by TEXT,
                invitation_token TEXT UNIQUE,
                role TEXT DEFAULT 'user',
                created_date TEXT,
                expires_date TEXT,
                used_date TEXT,
                is_used BOOLEAN DEFAULT 0
            )
        ''')
        
        # Email whitelist table for admin-controlled access
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
        
        # Access logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT,
                action TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TEXT,
                success BOOLEAN,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Create default admin user if no users exist
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user if no users exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Create default admin
            admin_email = "admin@dataanalyzer.com"
            admin_password = "admin123"  # Should be changed immediately
            
            salt = secrets.token_hex(32)
            password_hash = self._hash_password(admin_password, salt)
            
            cursor.execute('''
                INSERT INTO users (email, password_hash, salt, full_name, role, is_active, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                admin_email,
                password_hash,
                salt,
                "System Administrator",
                "admin",
                True,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            self.logger.info(f"Created default admin user: {admin_email}")
        
        conn.close()
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt"""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_password(self, password: str) -> Tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        return True, "Password is valid"
    
    def register_user(self, email: str, password: str, full_name: str, 
                     invitation_token: str = None) -> Tuple[bool, str]:
        """Register a new user with whitelist validation"""
        
        # Validate email
        if not self._validate_email(email):
            return False, "Invalid email format"
        
        # Validate password
        is_valid, message = self._validate_password(password)
        if not is_valid:
            return False, message
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute('SELECT email FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                conn.close()
                return False, "User already exists"
            
            # Check if email is whitelisted
            cursor.execute('''
                SELECT role, is_active FROM email_whitelist 
                WHERE email = ? AND is_active = 1
            ''', (email,))
            
            whitelist_entry = cursor.fetchone()
            if not whitelist_entry:
                conn.close()
                return False, "Email not authorized. Contact administrator for access."
            
            role = whitelist_entry[0]
            
            # If invitation token provided, validate it (legacy support)
            if invitation_token:
                cursor.execute('''
                    SELECT email, role, expires_date, is_used 
                    FROM invitations 
                    WHERE invitation_token = ?
                ''', (invitation_token,))
                
                invitation = cursor.fetchone()
                if invitation and not invitation[3] and datetime.fromisoformat(invitation[2]) > datetime.now():
                    if invitation[0] == email:
                        role = invitation[1]  # Use invitation role if valid
                        
                        # Mark invitation as used
                        cursor.execute('''
                            UPDATE invitations 
                            SET is_used = 1, used_date = ? 
                            WHERE invitation_token = ?
                        ''', (datetime.now().isoformat(), invitation_token))
            
            # Create user
            salt = secrets.token_hex(32)
            password_hash = self._hash_password(password, salt)
            
            cursor.execute('''
                INSERT INTO users (email, password_hash, salt, full_name, role, is_active, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                email,
                password_hash,
                salt,
                full_name,
                role,
                True,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            self._log_access(email, "register", "", "", True, f"User registered with role: {role}")
            return True, "User registered successfully"
            
        except Exception as e:
            self.logger.error(f"Registration error: {str(e)}")
            return False, "Registration failed"
    
    # Add whitelist management methods
    def add_to_whitelist(self, email: str, role: str, added_by: str, notes: str = "") -> bool:
        """Add email to whitelist (admin only)"""
        
        if not self._validate_email(email):
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO email_whitelist 
                (email, role, added_by, added_date, is_active, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                email,
                role,
                added_by,
                datetime.now().isoformat(),
                True,
                notes
            ))
            
            conn.commit()
            conn.close()
            
            self._log_access(added_by, "whitelist_add", "", "", True, f"Added {email} to whitelist with role {role}")
            return True
            
        except Exception as e:
            self.logger.error(f"Whitelist add error: {str(e)}")
            return False
    
    def list_whitelist(self, requester_role: str) -> List[Dict[str, Any]]:
        """List all whitelisted emails (admin only)"""
        
        if requester_role != 'admin':
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT email, role, added_by, added_date, is_active, notes
                FROM email_whitelist 
                ORDER BY added_date DESC
            ''')
            
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
    
    # Keep all your existing methods (authenticate_user, create_session, etc.)
    def authenticate_user(self, email: str, password: str, ip_address: str = "", 
                         user_agent: str = "") -> Tuple[bool, str, Dict[str, Any]]:
        """Authenticate user login"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user info
            cursor.execute('''
                SELECT password_hash, salt, full_name, role, is_active, 
                       login_attempts, locked_until
                FROM users WHERE email = ?
            ''', (email,))
            
            user_data = cursor.fetchone()
            if not user_data:
                conn.close()
                self._log_access(email, "login", ip_address, user_agent, False, "User not found")
                return False, "Invalid credentials", {}
            
            password_hash, salt, full_name, role, is_active, login_attempts, locked_until = user_data
            
            # Check if account is active
            if not is_active:
                conn.close()
                self._log_access(email, "login", ip_address, user_agent, False, "Account inactive")
                return False, "Account is inactive", {}
            
            # Check if account is locked
            if locked_until:
                lock_time = datetime.fromisoformat(locked_until)
                if datetime.now() < lock_time:
                    conn.close()
                    self._log_access(email, "login", ip_address, user_agent, False, "Account locked")
                    return False, f"Account locked until {lock_time.strftime('%Y-%m-%d %H:%M')}", {}
            
            # Verify password
            if self._hash_password(password, salt) != password_hash:
                # Increment login attempts
                login_attempts += 1
                
                # Lock account after 5 failed attempts
                if login_attempts >= 5:
                    lock_until = datetime.now() + timedelta(minutes=30)
                    cursor.execute('''
                        UPDATE users 
                        SET login_attempts = ?, locked_until = ? 
                        WHERE email = ?
                    ''', (login_attempts, lock_until.isoformat(), email))
                else:
                    cursor.execute('''
                        UPDATE users 
                        SET login_attempts = ? 
                        WHERE email = ?
                    ''', (login_attempts, email))
                
                conn.commit()
                conn.close()
                
                self._log_access(email, "login", ip_address, user_agent, False, f"Invalid password (attempt {login_attempts})")
                return False, "Invalid credentials", {}
            
            # Successful login - reset attempts and update last login
            cursor.execute('''
                UPDATE users 
                SET login_attempts = 0, locked_until = NULL, last_login = ? 
                WHERE email = ?
            ''', (datetime.now().isoformat(), email))
            
            conn.commit()
            conn.close()
            
            # Create session
            session_id = self.create_session(email, ip_address, user_agent)
            
            user_info = {
                'email': email,
                'full_name': full_name,
                'role': role,
                'session_id': session_id
            }
            
            self._log_access(email, "login", ip_address, user_agent, True, "Successful login")
            return True, "Login successful", user_info
            
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return False, "Authentication failed", {}
    
    def create_session(self, user_email: str, ip_address: str = "", user_agent: str = "") -> str:
        """Create a new user session"""
        
        session_id = secrets.token_urlsafe(32)
        expires_date = datetime.now() + timedelta(hours=24)  # 24 hour sessions
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_sessions 
                (session_id, user_email, created_date, expires_date, ip_address, user_agent, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                user_email,
                datetime.now().isoformat(),
                expires_date.isoformat(),
                ip_address,
                user_agent,
                True
            ))
            
            conn.commit()
            conn.close()
            
            return session_id
            
        except Exception as e:
            self.logger.error(f"Session creation error: {str(e)}")
            return ""
    
    def validate_session(self, session_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Validate a user session"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.user_email, s.expires_date, u.full_name, u.role, u.is_active
                FROM user_sessions s
                JOIN users u ON s.user_email = u.email
                WHERE s.session_id = ? AND s.is_active = 1
            ''', (session_id,))
            
            session_data = cursor.fetchone()
            if not session_data:
                conn.close()
                return False, {}
            
            user_email, expires_date, full_name, role, is_active = session_data
            
            # Check if session expired
            if datetime.fromisoformat(expires_date) < datetime.now():
                # Deactivate expired session
                cursor.execute('UPDATE user_sessions SET is_active = 0 WHERE session_id = ?', (session_id,))
                conn.commit()
                conn.close()
                return False, {}
            
            # Check if user is still active
            if not is_active:
                conn.close()
                return False, {}
            
            conn.close()
            
            return True, {
                'email': user_email,
                'full_name': full_name,
                'role': role,
                'session_id': session_id
            }
            
        except Exception as e:
            self.logger.error(f"Session validation error: {str(e)}")
            return False, {}
    
    def logout_user(self, session_id: str):
        """Logout user by deactivating session"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user email for logging
            cursor.execute('SELECT user_email FROM user_sessions WHERE session_id = ?', (session_id,))
            result = cursor.fetchone()
            user_email = result[0] if result else "unknown"
            
            # Deactivate session
            cursor.execute('UPDATE user_sessions SET is_active = 0 WHERE session_id = ?', (session_id,))
            conn.commit()
            conn.close()
            
            self._log_access(user_email, "logout", "", "", True, "User logged out")
            
        except Exception as e:
            self.logger.error(f"Logout error: {str(e)}")
    
    def list_users(self, requester_role: str) -> List[Dict[str, Any]]:
        """List all users (admin only)"""
        
        if requester_role != 'admin':
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT email, full_name, role, is_active, created_date, last_login
                FROM users ORDER BY created_date DESC
            ''')
            
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
    
    def _log_access(self, user_email: str, action: str, ip_address: str, 
                   user_agent: str, success: bool, details: str = ""):
        """Log access attempts and actions"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO access_logs 
                (user_email, action, ip_address, user_agent, timestamp, success, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_email,
                action,
                ip_address,
                user_agent,
                datetime.now().isoformat(),
                success,
                details
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Logging error: {str(e)}")

def get_auth_manager() -> AuthenticationManager:
    """Get singleton authentication manager"""
    if 'auth_manager' not in st.session_state:
        st.session_state.auth_manager = AuthenticationManager()
    return st.session_state.auth_manager

def require_authentication() -> Optional[Dict[str, Any]]:
    """Decorator function to require authentication"""
    
    auth_manager = get_auth_manager()
    
    # Check for invitation token in URL
    query_params = st.query_params
    invitation_token = query_params.get('invitation', None)
    
    if invitation_token and 'invitation_mode' not in st.session_state:
        st.session_state.invitation_mode = True
        st.session_state.invitation_token = invitation_token
    
    # Check if user is already authenticated
    if 'user_info' in st.session_state and 'session_id' in st.session_state:
        # Validate session
        is_valid, user_info = auth_manager.validate_session(st.session_state.session_id)
        if is_valid:
            st.session_state.user_info = user_info
            return user_info
        else:
            # Session expired
            del st.session_state.user_info
            del st.session_state.session_id
    
    # Show authentication interface
    return show_auth_interface(auth_manager)

def show_auth_interface(auth_manager: AuthenticationManager) -> Optional[Dict[str, Any]]:
    """Show authentication interface"""
    
    st.title("🔐 Multi-Dataset Analyzer")
    st.markdown("*Secure access to collaborative data analysis*")
    
    # Check for invitation mode
    if st.session_state.get('invitation_mode', False):
        return show_registration_form(auth_manager, st.session_state.get('invitation_token'))
    
    # Login/Register tabs
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
    
    with tab1:
        return show_login_form(auth_manager)
    
    with tab2:
        return show_registration_form(auth_manager)

def show_login_form(auth_manager: AuthenticationManager) -> Optional[Dict[str, Any]]:
    """Show login form"""
    
    st.subheader("Login to Your Account")
    
    with st.form("login_form"):
        email = st.text_input("Email Address", placeholder="your.email@company.com")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            login_button = st.form_submit_button("🔑 Login", type="primary")
        
        if login_button:
            if email and password:
                # Get client info
                ip_address = st.session_state.get('client_ip', 'unknown')
                user_agent = st.session_state.get('user_agent', 'unknown')
                
                success, message, user_info = auth_manager.authenticate_user(
                    email, password, ip_address, user_agent
                )
                
                if success:
                    st.session_state.user_info = user_info
                    st.session_state.session_id = user_info['session_id']
                    st.success(f"Welcome back, {user_info['full_name']}!")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("Please enter both email and password")
    
    return None

def show_registration_form(auth_manager: AuthenticationManager, invitation_token: str = None) -> Optional[Dict[str, Any]]:
    """Show registration form - Simplified version"""
    
    # Simple debug message
    st.write("🔧 Registration form is loading...")
    
    # Basic header
    st.subheader("Create New Account")
    st.info("Enter your details to create an account. Your email must be pre-authorized.")
    
    # Simple form without complex error handling
    email = st.text_input("Email Address")
    full_name = st.text_input("Full Name")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    
    if st.button("Create Account"):
        if email and full_name and password and confirm_password:
            if password == confirm_password:
                try:
                    success, message = auth_manager.register_user(email, password, full_name)
                    if success:
                        st.success("Account created! Please login.")
                    else:
                        st.error(message)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.error("Passwords don't match")
        else:
            st.error("Please fill all fields")
    
    # Simple info section
    st.markdown("**Note:** Your email must be authorized by an administrator.")
    
    return None
