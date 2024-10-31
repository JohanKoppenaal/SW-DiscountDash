# backend/database.py
import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db():
    db = sqlite3.connect('credentials.db')
    try:
        yield db
    finally:
        db.close()

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY,
                shop_url TEXT NOT NULL,
                client_id TEXT NOT NULL,
                client_secret TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()