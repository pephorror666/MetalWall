# File: metalwall_app/database/init_db.py
# ===========================
# DATABASE INITIALIZATION
# ===========================

import sqlite3
from config import DB_PATH

def init_db():
    """Initialize database with all tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Albums table
    c.execute('''
    CREATE TABLE IF NOT EXISTS albums (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        url TEXT NOT NULL,
        artist TEXT NOT NULL,
        album_name TEXT NOT NULL,
        cover_url TEXT,
        platform TEXT,
        tags TEXT NOT NULL,
        likes TEXT DEFAULT '[]',
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Concerts table
    c.execute('''
    CREATE TABLE IF NOT EXISTS concerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        bands TEXT NOT NULL,
        date DATE NOT NULL,
        venue TEXT NOT NULL,
        city TEXT NOT NULL,
        tags TEXT NOT NULL,
        info TEXT DEFAULT '',
        likes TEXT DEFAULT '[]',
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Album discoveries table
    c.execute('''
    CREATE TABLE IF NOT EXISTS album_discoveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        base_artist TEXT NOT NULL,
        base_album TEXT NOT NULL,
        discovered_artist TEXT NOT NULL,
        discovered_album TEXT NOT NULL,
        discovered_url TEXT,
        cover_url TEXT,
        discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create indexes
    c.execute('''CREATE INDEX IF NOT EXISTS idx_albums_username ON albums(username)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_concerts_username ON concerts(username)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_concerts_date ON concerts(date)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_discoveries_username ON album_discoveries(username)''')
    
    conn.commit()
    conn.close()