# backend/app/db.py

import sqlite3
from contextlib import contextmanager
import threading
import os

# Get the base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "chroma_db", "chroma.sqlite3")

# Ensure directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Thread-safe connection
_connection = None
_connection_lock = threading.Lock()

def get_connection():
    global _connection
    with _connection_lock:
        if _connection is None:
            _connection = sqlite3.connect(DB_PATH, check_same_thread=False)
            _connection.row_factory = sqlite3.Row  # Return dict-like rows
        return _connection

def get_db():
    """
    Returns a DB connection usable in routes/services.
    """
    return get_connection()

@contextmanager
def transaction():
    """
    Context manager for DB transactions.
    """
    db = get_db()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise

