"""
Database operations for users and commitments.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional


class Database:
    """Database manager for users and commitments."""
    
    def __init__(self, db_path: str = "webapp/database/commitments.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self._init_db()
    
    def _get_connection(self):
        """Get a new database connection for each operation."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Commitments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commitments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    description TEXT,
                    deadline TEXT,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    priority TEXT DEFAULT 'Medium',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Add priority column if it doesn't exist (for existing databases)
            try:
                cursor.execute("ALTER TABLE commitments ADD COLUMN priority TEXT DEFAULT 'Medium'")
                conn.commit()
            except sqlite3.OperationalError:
                # Column already exists
                pass
            
            conn.commit()
        finally:
            conn.close()
    
    # User operations
    def create_user(self, username: str) -> Optional[int]:
        """Create a new user. Returns user_id if created, None if exists."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO users (username, created_at)
                    VALUES (?, ?)
                """, (username, datetime.now().isoformat()))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None
        finally:
            conn.close()
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    # Commitment operations
    def create_commitment(self, user_id: int, subject: str, description: str = "",
                         deadline: Optional[str] = None, status: str = "Pending",
                         priority: str = "Medium") -> int:
        """Create a new commitment."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO commitments 
                (user_id, subject, description, deadline, status, priority, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, subject, description, deadline, status, priority, now, now))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def get_user_commitments(self, user_id: int, status: Optional[str] = None, 
                           sort_by_priority: Optional[str] = None) -> List[Dict]:
        """
        Get commitments for a user.
        
        Args:
            user_id: User ID
            status: Optional status filter
            sort_by_priority: 'high_to_low' or 'low_to_high' for priority sorting
            
        Returns:
            List of commitment dictionaries
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Build ORDER BY clause based on sort preference
            if sort_by_priority == 'high_to_low':
                # High priority first, then Medium, then Low
                priority_order = """
                    CASE priority
                        WHEN 'High' THEN 1
                        WHEN 'Medium' THEN 2
                        WHEN 'Low' THEN 3
                        ELSE 4
                    END ASC,
                    CASE 
                        WHEN deadline IS NULL THEN 1
                        ELSE 0
                    END,
                    deadline ASC
                """
            elif sort_by_priority == 'low_to_high':
                # Low priority first, then Medium, then High
                priority_order = """
                    CASE priority
                        WHEN 'Low' THEN 1
                        WHEN 'Medium' THEN 2
                        WHEN 'High' THEN 3
                        ELSE 4
                    END ASC,
                    CASE 
                        WHEN deadline IS NULL THEN 1
                        ELSE 0
                    END,
                    deadline ASC
                """
            else:
                # Default: by deadline urgency
                priority_order = """
                    CASE 
                        WHEN deadline IS NULL THEN 1
                        ELSE 0
                    END,
                    deadline ASC,
                    created_at DESC
                """
            
            if status:
                cursor.execute(f"""
                    SELECT * FROM commitments
                    WHERE user_id = ? AND status = ?
                    ORDER BY {priority_order}
                """, (user_id, status))
            else:
                cursor.execute(f"""
                    SELECT * FROM commitments
                    WHERE user_id = ?
                    ORDER BY {priority_order}
                """, (user_id,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def get_urgent_commitments(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get most urgent commitments (High priority only, nearest deadlines)."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM commitments
                WHERE user_id = ? 
                AND status = 'Pending'
                AND priority = 'High'
                AND deadline IS NOT NULL
                AND deadline >= datetime('now')
                ORDER BY deadline ASC
                LIMIT ?
            """, (user_id, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def update_commitment_status(self, commitment_id: int, user_id: int, status: str) -> bool:
        """Update commitment status."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE commitments 
                SET status = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
            """, (status, datetime.now().isoformat(), commitment_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def update_commitment(self, commitment_id: int, user_id: int, subject: str = None,
                         description: str = None, deadline: str = None, status: str = None,
                         priority: str = None) -> bool:
        """Update commitment details."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            updates = []
            params = []
            
            if subject is not None:
                updates.append("subject = ?")
                params.append(subject)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if deadline is not None:
                updates.append("deadline = ?")
                params.append(deadline)
            if status is not None:
                updates.append("status = ?")
                params.append(status)
            if priority is not None:
                updates.append("priority = ?")
                params.append(priority)
            
            if not updates:
                return False
            
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.extend([commitment_id, user_id])
            
            query = f"UPDATE commitments SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def delete_commitment(self, commitment_id: int, user_id: int) -> bool:
        """Delete a commitment."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM commitments WHERE id = ? AND user_id = ?", 
                         (commitment_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

