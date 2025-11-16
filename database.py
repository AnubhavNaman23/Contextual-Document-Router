"""
Database Integration Module for Contextual Document Router
Provides database connectivity and ORM support for data persistence
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from pathlib import Path


class Database:
    """SQLite database manager for the system"""
    
    def __init__(self, db_path: str = "data/system.db"):
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Get database connection as context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Documents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    format TEXT NOT NULL,
                    content_hash TEXT,
                    size_bytes INTEGER,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT 0,
                    processing_time REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Classifications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS classifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    intent TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    agent TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id)
                )
            ''')
            
            # Actions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    classification_id INTEGER,
                    action_type TEXT NOT NULL,
                    action_data TEXT,
                    status TEXT DEFAULT 'pending',
                    executed_at TIMESTAMP,
                    result TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (classification_id) REFERENCES classifications(id)
                )
            ''')
            
            # Processing logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processing_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    stage TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id)
                )
            ''')
            
            # System metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metadata TEXT,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Users table (for future authentication)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    api_key TEXT,
                    role TEXT DEFAULT 'user',
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_format ON documents(format)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_processed ON documents(processed)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_classifications_intent ON classifications(intent)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_actions_status ON actions(status)')
    
    def insert_document(self, filename: str, format: str, size_bytes: int, content_hash: str = None) -> int:
        """Insert a new document record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO documents (filename, format, size_bytes, content_hash)
                VALUES (?, ?, ?, ?)
            ''', (filename, format, size_bytes, content_hash))
            return cursor.lastrowid
    
    def update_document_processing(self, document_id: int, processed: bool, processing_time: float = None):
        """Update document processing status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE documents
                SET processed = ?, processing_time = ?
                WHERE id = ?
            ''', (processed, processing_time, document_id))
    
    def insert_classification(self, document_id: int, intent: str, confidence: float, 
                            agent: str, metadata: Dict[str, Any] = None) -> int:
        """Insert a classification result"""
        metadata_json = json.dumps(metadata) if metadata else None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO classifications (document_id, intent, confidence, agent, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (document_id, intent, confidence, agent, metadata_json))
            return cursor.lastrowid
    
    def insert_action(self, classification_id: int, action_type: str, 
                     action_data: Dict[str, Any] = None) -> int:
        """Insert an action record"""
        action_data_json = json.dumps(action_data) if action_data else None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO actions (classification_id, action_type, action_data)
                VALUES (?, ?, ?)
            ''', (classification_id, action_type, action_data_json))
            return cursor.lastrowid
    
    def update_action_status(self, action_id: int, status: str, result: str = None):
        """Update action status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE actions
                SET status = ?, result = ?, executed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, result, action_id))
    
    def log_processing(self, document_id: int, stage: str, status: str, 
                      message: str = None, error: str = None):
        """Log a processing event"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO processing_logs (document_id, stage, status, message, error)
                VALUES (?, ?, ?, ?, ?)
            ''', (document_id, stage, status, message, error))
    
    def record_metric(self, metric_type: str, metric_value: float, metadata: Dict[str, Any] = None):
        """Record a system metric"""
        metadata_json = json.dumps(metadata) if metadata else None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_metrics (metric_type, metric_value, metadata)
                VALUES (?, ?, ?)
            ''', (metric_type, metric_value, metadata_json))
    
    def get_document_by_id(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM documents WHERE id = ?', (document_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_document_classifications(self, document_id: int) -> List[Dict[str, Any]]:
        """Get all classifications for a document"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM classifications
                WHERE document_id = ?
                ORDER BY created_at DESC
            ''', (document_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_classification_actions(self, classification_id: int) -> List[Dict[str, Any]]:
        """Get all actions for a classification"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM actions
                WHERE classification_id = ?
                ORDER BY created_at DESC
            ''', (classification_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_documents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent documents"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM documents
                ORDER BY uploaded_at DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total documents
            cursor.execute('SELECT COUNT(*) as count FROM documents')
            total_docs = cursor.fetchone()['count']
            
            # Processed documents
            cursor.execute('SELECT COUNT(*) as count FROM documents WHERE processed = 1')
            processed_docs = cursor.fetchone()['count']
            
            # Documents by format
            cursor.execute('''
                SELECT format, COUNT(*) as count
                FROM documents
                GROUP BY format
            ''')
            by_format = {row['format']: row['count'] for row in cursor.fetchall()}
            
            # Classifications by intent
            cursor.execute('''
                SELECT intent, COUNT(*) as count
                FROM classifications
                GROUP BY intent
            ''')
            by_intent = {row['intent']: row['count'] for row in cursor.fetchall()}
            
            # Average confidence
            cursor.execute('SELECT AVG(confidence) as avg_conf FROM classifications')
            avg_confidence = cursor.fetchone()['avg_conf'] or 0
            
            # Pending actions
            cursor.execute("SELECT COUNT(*) as count FROM actions WHERE status = 'pending'")
            pending_actions = cursor.fetchone()['count']
            
            return {
                'total_documents': total_docs,
                'processed_documents': processed_docs,
                'by_format': by_format,
                'by_intent': by_intent,
                'average_confidence': avg_confidence,
                'pending_actions': pending_actions
            }
    
    def search_documents(self, query: str = None, format: str = None, 
                        processed: bool = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Search documents with filters"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            sql = 'SELECT * FROM documents WHERE 1=1'
            params = []
            
            if query:
                sql += ' AND filename LIKE ?'
                params.append(f'%{query}%')
            
            if format:
                sql += ' AND format = ?'
                params.append(format)
            
            if processed is not None:
                sql += ' AND processed = ?'
                params.append(1 if processed else 0)
            
            sql += ' ORDER BY uploaded_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_old_records(self, days: int = 30):
        """Delete records older than specified days"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM documents
                WHERE created_at < datetime('now', '-' || ? || ' days')
            ''', (days,))
            deleted = cursor.rowcount
            return deleted
    
    def vacuum(self):
        """Vacuum the database to reclaim space"""
        with self.get_connection() as conn:
            conn.execute('VACUUM')


class DocumentRepository:
    """High-level repository for document operations"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def create_document(self, filename: str, format: str, size_bytes: int) -> int:
        """Create a new document and return its ID"""
        return self.db.insert_document(filename, format, size_bytes)
    
    def process_document(self, document_id: int, intent: str, confidence: float, 
                        agent: str, actions: List[str], processing_time: float = None) -> int:
        """Process a document with classification and actions"""
        # Update document processing status
        self.db.update_document_processing(document_id, True, processing_time)
        
        # Insert classification
        classification_id = self.db.insert_classification(
            document_id, intent, confidence, agent
        )
        
        # Insert actions
        for action in actions:
            self.db.insert_action(classification_id, action)
        
        return classification_id
    
    def get_document_history(self, document_id: int) -> Dict[str, Any]:
        """Get complete history of a document"""
        document = self.db.get_document_by_id(document_id)
        if not document:
            return None
        
        classifications = self.db.get_document_classifications(document_id)
        
        for classification in classifications:
            classification['actions'] = self.db.get_classification_actions(
                classification['id']
            )
        
        document['classifications'] = classifications
        return document


if __name__ == "__main__":
    # Test database
    print("=== Testing Database System ===\n")
    
    db = Database("data/test_system.db")
    repo = DocumentRepository(db)
    
    # Create a test document
    doc_id = repo.create_document("test_email.txt", "Email", 1024)
    print(f"Created document ID: {doc_id}")
    
    # Process the document
    classification_id = repo.process_document(
        doc_id,
        intent="Complaint",
        confidence=0.95,
        agent="EmailAgent",
        actions=["escalate_complaint", "send_acknowledgment"],
        processing_time=0.523
    )
    print(f"Created classification ID: {classification_id}")
    
    # Get statistics
    stats = db.get_statistics()
    print("\nDatabase Statistics:")
    print(json.dumps(stats, indent=2))
    
    # Get document history
    history = repo.get_document_history(doc_id)
    print("\nDocument History:")
    print(json.dumps(history, indent=2, default=str))
