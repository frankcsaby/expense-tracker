import sqlite3
from contextlib import contextmanager
from app.config import DATABASE_PATH

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize the database with required tables."""
    with get_db_connection() as conn:
        # Create expenses table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                recurring INTEGER DEFAULT 0,
                recurring_interval TEXT
            )
        ''')
        
        # Create budgets table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL UNIQUE,
                amount REAL NOT NULL,
                period TEXT NOT NULL
            )
        ''')
        
        # Create tags table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')
        
        # Create expense_tags table (for many-to-many relationship)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS expense_tags (
                expense_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (expense_id, tag_id),
                FOREIGN KEY (expense_id) REFERENCES expenses (id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()

def dict_factory(cursor, row):
    """Convert database row objects to dictionaries."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

def get_dict_connection():
    """Get a connection that returns results as dictionaries."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = dict_factory
    return conn 