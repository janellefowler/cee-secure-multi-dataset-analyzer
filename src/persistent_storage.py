import pandas as pd
import pickle
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import hashlib
import sqlite3

class PersistentDataStorage:
    """Manage persistent storage of datasets and metadata"""
    
    def __init__(self, storage_dir: str = "data_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.datasets_dir = self.storage_dir / "datasets"
        self.metadata_dir = self.storage_dir / "metadata"
        self.datasets_dir.mkdir(exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)
        
        # Initialize SQLite database for metadata
        self.db_path = self.storage_dir / "datasets.db"
        self._init_database()
        
        self.logger = logging.getLogger(__name__)
    
    def _init_database(self):
        """Initialize SQLite database for dataset metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create datasets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                filename TEXT,
                file_size_mb REAL,
                rows INTEGER,
                columns INTEGER,
                upload_date TEXT,
                uploaded_by TEXT,
                description TEXT,
                tags TEXT,
                is_public BOOLEAN DEFAULT 0,
                access_level TEXT DEFAULT 'private'
            )
        ''')
        
        # Create dataset_access table for user permissions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dataset_access (
                dataset_id TEXT,
                user_email TEXT,
                access_level TEXT,
                granted_by TEXT,
                granted_date TEXT,
                FOREIGN KEY (dataset_id) REFERENCES datasets (id)
            )
        ''')
        
        # Create analysis_sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_sessions (
                session_id TEXT PRIMARY KEY,
                user_email TEXT,
                datasets_used TEXT,
                created_date TEXT,
                last_accessed TEXT,
                query_count INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_dataset(self, dataset_id: str, name: str, data: pd.DataFrame, 
                    metadata: Dict[str, Any], uploaded_by: str) -> bool:
        """Save dataset to persistent storage"""
        try:
            # Save the actual data
            data_file = self.datasets_dir / f"{dataset_id}.pkl"
            with open(data_file, 'wb') as f:
                pickle.dump(data, f)
            
            # Save metadata to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO datasets 
                (id, name, filename, file_size_mb, rows, columns, upload_date, uploaded_by, description, tags, is_public, access_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dataset_id,
                name,
                metadata.get('filename', ''),
                metadata.get('file_size_mb', 0),
                len(data),
                len(data.columns),
                datetime.now().isoformat(),
                uploaded_by,
                metadata.get('description', ''),
                json.dumps(metadata.get('tags', [])),
                metadata.get('is_public', False),
                metadata.get('access_level', 'private')
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Saved dataset '{name}' with ID {dataset_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving dataset: {str(e)}")
            return False
    
    def load_dataset(self, dataset_id: str, user_email: str) -> Optional[pd.DataFrame]:
        """Load dataset from persistent storage with access control"""
        
        # Check if user has access
        if not self.check_dataset_access(dataset_id, user_email):
            self.logger.warning(f"Access denied for user {user_email} to dataset {dataset_id}")
            return None
        
        try:
            data_file = self.datasets_dir / f"{dataset_id}.pkl"
            if data_file.exists():
                with open(data_file, 'rb') as f:
                    data = pickle.load(f)
                return data
            else:
                self.logger.error(f"Dataset file not found: {dataset_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error loading dataset: {str(e)}")
            return None
    
    def list_datasets(self, user_email: str) -> List[Dict[str, Any]]:
        """List all datasets accessible to the user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get datasets the user can access
        cursor.execute('''
            SELECT DISTINCT d.* FROM datasets d
            LEFT JOIN dataset_access da ON d.id = da.dataset_id
            WHERE d.is_public = 1 
               OR d.uploaded_by = ?
               OR da.user_email = ?
            ORDER BY d.upload_date DESC
        ''', (user_email, user_email))
        
        datasets = []
        for row in cursor.fetchall():
            datasets.append({
                'id': row[0],
                'name': row[1],
                'filename': row[2],
                'file_size_mb': row[3],
                'rows': row[4],
                'columns': row[5],
                'upload_date': row[6],
                'uploaded_by': row[7],
                'description': row[8],
                'tags': json.loads(row[9]) if row[9] else [],
                'is_public': bool(row[10]),
                'access_level': row[11]
            })
        
        conn.close()
        return datasets
    
    def check_dataset_access(self, dataset_id: str, user_email: str) -> bool:
        """Check if user has access to a specific dataset"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if dataset is public, owned by user, or explicitly granted access
        cursor.execute('''
            SELECT COUNT(*) FROM datasets d
            LEFT JOIN dataset_access da ON d.id = da.dataset_id
            WHERE d.id = ? AND (
                d.is_public = 1 
                OR d.uploaded_by = ?
                OR da.user_email = ?
            )
        ''', (dataset_id, user_email, user_email))
        
        result = cursor.fetchone()[0] > 0
        conn.close()
        return result
    
    def grant_dataset_access(self, dataset_id: str, user_email: str, 
                           access_level: str, granted_by: str) -> bool:
        """Grant access to a dataset for a specific user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO dataset_access 
                (dataset_id, user_email, access_level, granted_by, granted_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (dataset_id, user_email, access_level, granted_by, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Granted {access_level} access to dataset {dataset_id} for user {user_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error granting access: {str(e)}")
            return False
    
    def revoke_dataset_access(self, dataset_id: str, user_email: str) -> bool:
        """Revoke access to a dataset for a specific user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM dataset_access 
                WHERE dataset_id = ? AND user_email = ?
            ''', (dataset_id, user_email))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Revoked access to dataset {dataset_id} for user {user_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error revoking access: {str(e)}")
            return False
    
    def delete_dataset(self, dataset_id: str, user_email: str) -> bool:
        """Delete a dataset (only by owner)"""
        try:
            # Check if user is the owner
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT uploaded_by FROM datasets WHERE id = ?', (dataset_id,))
            result = cursor.fetchone()
            
            if not result or result[0] != user_email:
                self.logger.warning(f"User {user_email} attempted to delete dataset {dataset_id} without permission")
                conn.close()
                return False
            
            # Delete from database
            cursor.execute('DELETE FROM datasets WHERE id = ?', (dataset_id,))
            cursor.execute('DELETE FROM dataset_access WHERE dataset_id = ?', (dataset_id,))
            
            conn.commit()
            conn.close()
            
            # Delete data file
            data_file = self.datasets_dir / f"{dataset_id}.pkl"
            if data_file.exists():
                data_file.unlink()
            
            self.logger.info(f"Deleted dataset {dataset_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting dataset: {str(e)}")
            return False
    
    def get_dataset_metadata(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific dataset"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM datasets WHERE id = ?', (dataset_id,))
        row = cursor.fetchone()
        
        if row:
            metadata = {
                'id': row[0],
                'name': row[1],
                'filename': row[2],
                'file_size_mb': row[3],
                'rows': row[4],
                'columns': row[5],
                'upload_date': row[6],
                'uploaded_by': row[7],
                'description': row[8],
                'tags': json.loads(row[9]) if row[9] else [],
                'is_public': bool(row[10]),
                'access_level': row[11]
            }
        else:
            metadata = None
        
        conn.close()
        return metadata
    
    def update_dataset_metadata(self, dataset_id: str, updates: Dict[str, Any], user_email: str) -> bool:
        """Update dataset metadata (only by owner)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check ownership
            cursor.execute('SELECT uploaded_by FROM datasets WHERE id = ?', (dataset_id,))
            result = cursor.fetchone()
            
            if not result or result[0] != user_email:
                conn.close()
                return False
            
            # Build update query
            update_fields = []
            values = []
            
            for field, value in updates.items():
                if field in ['name', 'description', 'is_public', 'access_level']:
                    update_fields.append(f"{field} = ?")
                    values.append(value)
                elif field == 'tags':
                    update_fields.append("tags = ?")
                    values.append(json.dumps(value))
            
            if update_fields:
                values.append(dataset_id)
                query = f"UPDATE datasets SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, values)
                conn.commit()
            
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating metadata: {str(e)}")
            return False
    
    def create_analysis_session(self, user_email: str, dataset_ids: List[str]) -> str:
        """Create a new analysis session"""
        session_id = hashlib.md5(f"{user_email}_{datetime.now().isoformat()}".encode()).hexdigest()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO analysis_sessions 
                (session_id, user_email, datasets_used, created_date, last_accessed, query_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                user_email,
                json.dumps(dataset_ids),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                0
            ))
            
            conn.commit()
            conn.close()
            
            return session_id
            
        except Exception as e:
            self.logger.error(f"Error creating session: {str(e)}")
            return ""
    
    def get_user_sessions(self, user_email: str) -> List[Dict[str, Any]]:
        """Get all analysis sessions for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM analysis_sessions 
            WHERE user_email = ? 
            ORDER BY last_accessed DESC
        ''', (user_email,))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'session_id': row[0],
                'user_email': row[1],
                'datasets_used': json.loads(row[2]),
                'created_date': row[3],
                'last_accessed': row[4],
                'query_count': row[5]
            })
        
        conn.close()
        return sessions
    
    def cleanup_old_sessions(self, days_old: int = 30):
        """Clean up old analysis sessions"""
        try:
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM analysis_sessions WHERE last_accessed < ?', (cutoff_date,))
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleaned up {deleted_count} old sessions")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up sessions: {str(e)}")

class DatasetManager:
    """High-level interface for dataset management with authentication"""
    
    def __init__(self, storage_dir: str = "data_storage"):
        self.storage = PersistentDataStorage(storage_dir)
        self.logger = logging.getLogger(__name__)
    
    def add_dataset(self, name: str, data: pd.DataFrame, metadata: Dict[str, Any], 
                   user_email: str) -> str:
        """Add a new dataset with automatic ID generation"""
        
        # Generate unique dataset ID
        dataset_id = hashlib.md5(f"{name}_{user_email}_{datetime.now().isoformat()}".encode()).hexdigest()
        
        # Add user info to metadata
        metadata['uploaded_by'] = user_email
        metadata['upload_date'] = datetime.now().isoformat()
        
        if self.storage.save_dataset(dataset_id, name, data, metadata, user_email):
            self.logger.info(f"Successfully added dataset '{name}' for user {user_email}")
            return dataset_id
        else:
            self.logger.error(f"Failed to add dataset '{name}' for user {user_email}")
            return ""
    
    def get_dataset(self, dataset_id: str, user_email: str) -> Optional[pd.DataFrame]:
        """Get a dataset with access control"""
        return self.storage.load_dataset(dataset_id, user_email)
    
    def list_user_datasets(self, user_email: str) -> List[Dict[str, Any]]:
        """List all datasets accessible to a user"""
        return self.storage.list_datasets(user_email)
    
    def share_dataset(self, dataset_id: str, target_user_email: str, 
                     access_level: str, owner_email: str) -> bool:
        """Share a dataset with another user"""
        
        # Check if the requester owns the dataset
        metadata = self.storage.get_dataset_metadata(dataset_id)
        if not metadata or metadata['uploaded_by'] != owner_email:
            self.logger.warning(f"User {owner_email} attempted to share dataset {dataset_id} without ownership")
            return False
        
        return self.storage.grant_dataset_access(dataset_id, target_user_email, access_level, owner_email)
    
    def unshare_dataset(self, dataset_id: str, target_user_email: str, owner_email: str) -> bool:
        """Remove sharing access for a dataset"""
        
        # Check ownership
        metadata = self.storage.get_dataset_metadata(dataset_id)
        if not metadata or metadata['uploaded_by'] != owner_email:
            return False
        
        return self.storage.revoke_dataset_access(dataset_id, target_user_email)
    
    def delete_dataset(self, dataset_id: str, user_email: str) -> bool:
        """Delete a dataset (owner only)"""
        return self.storage.delete_dataset(dataset_id, user_email)
    
    def update_dataset_info(self, dataset_id: str, updates: Dict[str, Any], user_email: str) -> bool:
        """Update dataset information (owner only)"""
        return self.storage.update_dataset_metadata(dataset_id, updates, user_email)
    
    def get_dataset_info(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get dataset metadata"""
        return self.storage.get_dataset_metadata(dataset_id)
    
    def create_session(self, user_email: str, dataset_ids: List[str]) -> str:
        """Create a new analysis session"""
        return self.storage.create_analysis_session(user_email, dataset_ids)
    
    def get_user_sessions(self, user_email: str) -> List[Dict[str, Any]]:
        """Get user's analysis sessions"""
        return self.storage.get_user_sessions(user_email)