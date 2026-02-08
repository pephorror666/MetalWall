# File: metalwall_app/admin/backup_tools.py
# ===========================
# ADMIN BACKUP/RESTORE TOOLS
# ===========================

import streamlit as st
import sqlite3
import json
import os
import shutil
from datetime import datetime
from typing import Tuple
from config import DB_PATH
from database.operations import load_albums, load_concerts, get_database_stats

def admin_backup_page():
    """Admin database backup and restore page"""
    st.subheader("🔧 Admin Tools - Database Management")
    
    # Show database statistics
    stats = get_database_stats()
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Albums", stats['album_count'])
        with col2:
            st.metric("🎸 Concerts", stats['concert_count'])
        with col3:
            st.metric("🎲 Discoveries", stats['discovery_count'])
        with col4:
            # Calculate DB size
            db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
            st.metric("🗄️ DB Size", f"{db_size / (1024 * 1024):.2f} MB")
    
    st.markdown("---")
    
    # Create two columns for Export and Import
    col_export, col_import = st.columns(2)
    
    with col_export:
        st.markdown("### 📤 Export Database")
        st.markdown("<div class='admin-tools'>", unsafe_allow_html=True)
        
        # Export to JSON
        st.write("**Export to JSON**")
        st.write("Export all data as a JSON file for backup or migration.")
        
        if st.button("📄 Export to JSON", key="export_json", use_container_width=True):
            json_data = export_database_to_json()
            if json_data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"metalwall_backup_{timestamp}.json"
                
                st.download_button(
                    label="⬇️ Download JSON File",
                    data=json_data,
                    file_name=filename,
                    mime="application/json",
                    use_container_width=True
                )
                st.success("✅ JSON export ready for download")
            else:
                st.error("❌ Failed to export database")
        
        st.divider()
        
        # Export to SQLite DB
        st.write("**Export Database File**")
        st.write("Download the complete SQLite database file.")
        
        if st.button("🗃️ Export Database File", key="export_db", use_container_width=True):
            if os.path.exists(DB_PATH):
                with open(DB_PATH, "rb") as f:
                    db_data = f.read()
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"metal_music_backup_{timestamp}.db"
                
                st.download_button(
                    label="⬇️ Download Database File",
                    data=db_data,
                    file_name=filename,
                    mime="application/x-sqlite3",
                    use_container_width=True
                )
                st.success("✅ Database file ready for download")
            else:
                st.error("❌ Database file not found")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col_import:
        st.markdown("### 📥 Import Database")
        st.markdown("<div class='admin-tools'>", unsafe_allow_html=True)
        
        # Import from JSON
        st.write("**Import from JSON**")
        st.write("Import data from a JSON backup file.")
        st.warning("⚠️ This will replace all existing data!")
        
        json_file = st.file_uploader("Choose JSON file", type=['json'], key="json_upload")
        
        if json_file is not None:
            if st.button("🔄 Import from JSON", key="import_json", use_container_width=True):
                try:
                    json_data = json_file.getvalue().decode('utf-8')
                    success, message = import_database_from_json(json_data)
                    if success:
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                except Exception as e:
                    st.error(f"❌ Error reading JSON file: {e}")
        
        st.divider()
        
        # Import from SQLite DB
        st.write("**Import Database File**")
        st.write("Upload and replace the entire database file.")
        st.warning("⚠️ This will completely replace the current database!")
        
        db_file = st.file_uploader("Choose SQLite database file", type=['db', 'sqlite', 'sqlite3'], key="db_upload")
        
        if db_file is not None:
            if st.button("🔄 Import Database File", key="import_db", use_container_width=True):
                with st.spinner("Restoring database..."):
                    success, message = restore_database_from_file(db_file)
                    if success:
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Quick Backup Section
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Create Quick Backup", key="quick_backup", use_container_width=True):
            backup_filename = backup_database()
            if backup_filename:
                st.success(f"✅ Backup created: {backup_filename}")
            else:
                st.error("❌ Failed to create backup")
    
    with col2:
        if st.button("🔍 Verify Database", key="verify_db", use_container_width=True):
            stats = get_database_stats()
            if stats:
                st.info(f"""
                **Database Status:**
                - Albums: {stats['album_count']}
                - Concerts: {stats['concert_count']}
                - Discoveries: {stats['discovery_count']}
                - Size: {stats['db_size_mb']:.2f} MB
                - Latest album: {stats['latest_album'][:19] if stats['latest_album'] else 'N/A'}
                - Latest concert: {stats['latest_concert'][:19] if stats['latest_concert'] else 'N/A'}
                """)
            else:
                st.error("❌ Could not verify database")

def export_database_to_json() -> str:
    """Export entire database to JSON format"""
    try:
        albums = load_albums()
        concerts = load_concerts()
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'app_version': 'MetalWall v0.5',
            'albums_count': len(albums),
            'concerts_count': len(concerts),
            'albums': [album.to_dict() for album in albums],
            'concerts': [
                {
                    'id': concert.id,
                    'username': concert.username,
                    'bands': concert.bands,
                    'date': concert.date,
                    'venue': concert.venue,
                    'city': concert.city,
                    'tags': concert.tags,
                    'info': concert.info,
                    'likes': concert.likes,
                    'timestamp': concert.timestamp.isoformat(),
                    'created_at': concert.created_at.isoformat()
                }
                for concert in concerts
            ]
        }
        
        return json.dumps(export_data, indent=2, default=str)
    except Exception as e:
        st.error(f"Error exporting database: {e}")
        return ""

def import_database_from_json(json_data: str) -> Tuple[bool, str]:
    """Import database from JSON"""
    try:
        data = json.loads(json_data)
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Clear existing data
        c.execute('DELETE FROM albums')
        c.execute('DELETE FROM concerts')
        
        # Import albums
        for album in data.get('albums', []):
            c.execute('''
            INSERT INTO albums (id, username, url, artist, album_name, cover_url, 
                              platform, tags, likes, timestamp, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                album['id'],
                album['username'],
                album['url'],
                album['artist'],
                album['album_name'],
                album.get('cover_url', ''),
                album.get('platform', 'Other'),
                str(album.get('tags', [])),
                str(album.get('likes', [])),
                album['timestamp'],
                album.get('created_at', album['timestamp'])
            ))
        
        # Import concerts
        for concert in data.get('concerts', []):
            c.execute('''
            INSERT INTO concerts (id, username, bands, date, venue, city, 
                                tags, info, likes, timestamp, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                concert['id'],
                concert['username'],
                concert['bands'],
                concert['date'],
                concert['venue'],
                concert['city'],
                str(concert.get('tags', [])),
                concert.get('info', ''),
                str(concert.get('likes', [])),
                concert['timestamp'],
                concert.get('created_at', concert['timestamp'])
            ))
        
        conn.commit()
        conn.close()
        return True, f"Successfully imported {len(data.get('albums', []))} albums and {len(data.get('concerts', []))} concerts"
    except Exception as e:
        return False, f"Error importing database: {e}"

def backup_database() -> str:
    """Create a backup of the database file"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"metal_music_backup_{timestamp}.db"
        
        # Copy the database file
        shutil.copy2(DB_PATH, backup_filename)
        
        # Also create a backup directory for organization
        if not os.path.exists("backups"):
            os.makedirs("backups")
        shutil.copy2(DB_PATH, f"backups/{backup_filename}")
        
        return backup_filename
    except Exception as e:
        st.error(f"Error creating backup: {e}")
        return ""

def restore_database_from_file(uploaded_file) -> Tuple[bool, str]:
    """Restore database from uploaded .db file"""
    try:
        # Create a backup before restoring
        backup_filename = backup_database()
        
        # Write uploaded file to database location
        with open(DB_PATH, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        # Verify the restored database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if tables exist
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('albums', 'concerts')")
        tables = c.fetchall()
        
        conn.close()
        
        if len(tables) == 2:
            return True, f"Database restored successfully. Backup saved as {backup_filename}"
        else:
            # Restore from backup if tables don't exist
            if backup_filename and os.path.exists(backup_filename):
                shutil.copy2(backup_filename, DB_PATH)
            return False, "Invalid database file. Backup restored."
    except Exception as e:
        return False, f"Error restoring database: {e}"