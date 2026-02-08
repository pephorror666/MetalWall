# File: metalwall_app/database/operations.py
# ===========================
# DATABASE CRUD OPERATIONS
# ===========================

import sqlite3
from datetime import datetime
from typing import List, Optional
from .models import Album, Concert, AlbumDiscovery
from config import DB_PATH

# ============ ALBUM OPERATIONS ============

def save_album(username: str, url: str, artist: str, album_name: str, 
               cover_url: str, platform: str, tags: List[str]) -> bool:
    """Save a new album to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
        INSERT INTO albums (username, url, artist, album_name, cover_url, platform, tags, likes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, url, artist, album_name, cover_url, platform, str(tags), str([])))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving album: {e}")
        return False

def load_albums() -> List[Album]:
    """Load all albums from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT * FROM albums ORDER BY timestamp DESC')
        rows = c.fetchall()
        conn.close()
        
        return [Album.from_db_row(row) for row in rows]
    except Exception as e:
        print(f"Error loading albums: {e}")
        return []

def update_album(album_id: int, url: str, artist: str, album_name: str, 
                 cover_url: str, platform: str, tags: List[str]) -> bool:
    """Update an existing album"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
        UPDATE albums 
        SET url = ?, artist = ?, album_name = ?, cover_url = ?, platform = ?, tags = ?
        WHERE id = ?
        ''', (url, artist, album_name, cover_url, platform, str(tags), album_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating album: {e}")
        return False

def update_album_likes(album_id: int, likes_list: List[str]) -> bool:
    """Update album likes"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE albums SET likes = ? WHERE id = ?', (str(likes_list), album_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating album likes: {e}")
        return False

def delete_album(album_id: int) -> bool:
    """Delete an album"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM albums WHERE id = ?', (album_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting album: {e}")
        return False

def check_duplicate_url(url: str) -> bool:
    """Check if URL already exists in database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM albums WHERE url = ?', (url,))
        count = c.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        print(f"Error checking duplicate: {e}")
        return False

# ============ CONCERT OPERATIONS ============

def save_concert(username: str, bands: str, date: str, venue: str, 
                 city: str, tags: List[str], info: str) -> bool:
    """Save a new concert"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
        INSERT INTO concerts (username, bands, date, venue, city, tags, info, likes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, bands, date, venue, city, str(tags), info, str([])))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving concert: {e}")
        return False

def load_concerts() -> List[Concert]:
    """Load all concerts"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT * FROM concerts ORDER BY date ASC')
        rows = c.fetchall()
        conn.close()
        
        return [Concert.from_db_row(row) for row in rows]
    except Exception as e:
        print(f"Error loading concerts: {e}")
        return []

def update_concert(concert_id: int, bands: str, date: str, venue: str, 
                   city: str, tags: List[str], info: str) -> bool:
    """Update an existing concert"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
        UPDATE concerts 
        SET bands = ?, date = ?, venue = ?, city = ?, tags = ?, info = ?
        WHERE id = ?
        ''', (bands, date, venue, city, str(tags), info, concert_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating concert: {e}")
        return False

def update_concert_likes(concert_id: int, likes_list: List[str]) -> bool:
    """Update concert likes"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE concerts SET likes = ? WHERE id = ?', (str(likes_list), concert_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating concert likes: {e}")
        return False

def delete_concert(concert_id: int) -> bool:
    """Delete a concert"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM concerts WHERE id = ?', (concert_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting concert: {e}")
        return False

def delete_past_concerts():
    """Delete past concerts"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('DELETE FROM concerts WHERE date < ?', (today,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error cleaning concerts: {e}")

# ============ DISCOVERY OPERATIONS ============

def save_discovery(username: str, base_artist: str, base_album: str,
                   discovered_artist: str, discovered_album: str,
                   discovered_url: str, cover_url: str) -> bool:
    """Save an album discovery"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
        INSERT INTO album_discoveries 
        (username, base_artist, base_album, discovered_artist, discovered_album, discovered_url, cover_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, base_artist, base_album, discovered_artist, discovered_album, discovered_url, cover_url))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving discovery: {e}")
        return False

def load_discoveries(username: Optional[str] = None) -> List[AlbumDiscovery]:
    """Load album discoveries, optionally filtered by username"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        if username:
            c.execute('SELECT * FROM album_discoveries WHERE username = ? ORDER BY discovered_at DESC', (username,))
        else:
            c.execute('SELECT * FROM album_discoveries ORDER BY discovered_at DESC')
        
        rows = c.fetchall()
        conn.close()
        
        return [AlbumDiscovery.from_db_row(row) for row in rows]
    except Exception as e:
        print(f"Error loading discoveries: {e}")
        return []

# ============ DATABASE STATISTICS ============

# In database/operations.py, update the get_database_stats function:
def get_database_stats():
    """Get database statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Count albums
        c.execute('SELECT COUNT(*) FROM albums')
        album_count = c.fetchone()[0]
        
        # Count concerts
        c.execute('SELECT COUNT(*) FROM concerts')
        concert_count = c.fetchone()[0]
        
        # Count discoveries
        c.execute('SELECT COUNT(*) FROM album_discoveries')
        discovery_count = c.fetchone()[0]
        
        # Get latest entries
        c.execute('SELECT MAX(timestamp) FROM albums')
        latest_album = c.fetchone()[0]
        
        c.execute('SELECT MAX(timestamp) FROM concerts')
        latest_concert = c.fetchone()[0]
        
        conn.close()
        
        # Calculate DB size
        import os
        db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
        
        return {
            'album_count': album_count,
            'concert_count': concert_count,
            'discovery_count': discovery_count,
            'latest_album': latest_album,
            'latest_concert': latest_concert,
            'db_size_mb': db_size / (1024 * 1024)
        }
    except Exception as e:
        print(f"Error getting database stats: {e}")
        return None