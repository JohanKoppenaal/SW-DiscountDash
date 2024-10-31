# backend/database.py
import sqlite3
from contextlib import contextmanager
import os
import json

DATABASE_PATH = 'shopware_settings.db'

@contextmanager
def get_db():
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Create database if it doesn't exist
    if not os.path.exists(DATABASE_PATH):
        with get_db() as db:
            # Credentials table
            db.execute("""
                CREATE TABLE IF NOT EXISTS credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shop_url TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    client_secret TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Discounts table
            db.execute("""
                CREATE TABLE IF NOT EXISTS discounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    percentage REAL NOT NULL,
                    conditions TEXT NOT NULL,  -- JSON string van conditions
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.commit()

# Credential functions
def save_credentials(shop_url: str, client_id: str, client_secret: str):
    with get_db() as db:
        # First delete any existing credentials
        db.execute("DELETE FROM credentials")
        # Then insert new credentials
        db.execute(
            "INSERT INTO credentials (shop_url, client_id, client_secret) VALUES (?, ?, ?)",
            (shop_url, client_id, client_secret)
        )
        db.commit()

def get_credentials():
    with get_db() as db:
        creds = db.execute("SELECT * FROM credentials ORDER BY id DESC LIMIT 1").fetchone()
        if creds:
            return {
                "shop_url": creds['shop_url'],
                "client_id": creds['client_id'],
                "client_secret": creds['client_secret']
            }
        return None

# Discount functions
def save_discount(name: str, percentage: float, conditions: list) -> int:
    """Save a new discount to the database"""
    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO discounts (name, percentage, conditions) VALUES (?, ?, ?)",
            (name, percentage, json.dumps(conditions))
        )
        db.commit()
        return cursor.lastrowid

def get_discounts() -> list:
    """Get all discounts from the database"""
    with get_db() as db:
        discounts = db.execute("SELECT * FROM discounts WHERE active = 1 ORDER BY created_at DESC").fetchall()
        return [{
            'id': d['id'],
            'name': d['name'],
            'percentage': d['percentage'],
            'conditions': json.loads(d['conditions']),
            'created_at': d['created_at']
        } for d in discounts]

def delete_discount(discount_id: int) -> bool:
    """Soft delete a discount by setting active to 0"""
    with get_db() as db:
        db.execute("UPDATE discounts SET active = 0 WHERE id = ?", (discount_id,))
        db.commit()
        return True

def update_discount(discount_id: int, name: str = None, percentage: float = None, conditions: list = None) -> bool:
    """Update an existing discount"""
    update_fields = []
    values = []

    if name is not None:
        update_fields.append("name = ?")
        values.append(name)
    if percentage is not None:
        update_fields.append("percentage = ?")
        values.append(percentage)
    if conditions is not None:
        update_fields.append("conditions = ?")
        values.append(json.dumps(conditions))

    if not update_fields:
        return False

    update_fields.append("updated_at = CURRENT_TIMESTAMP")

    with get_db() as db:
        query = f"UPDATE discounts SET {', '.join(update_fields)} WHERE id = ? AND active = 1"
        values.append(discount_id)
        db.execute(query, values)
        db.commit()
        return True

# Initialize database when module is imported
init_db()