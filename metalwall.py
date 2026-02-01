# =========================== 
# METAL MUSIC SOCIAL - STREAMLIT APP v3.3
# =========================== 
# NEW: Universal Metadata Extractor (Open Graph)
# Works with: Spotify, Bandcamp, Tidal, Apple Music, YouTube, SoundCloud, etc.
# Like pasting a link in WhatsApp - it ALWAYS works

import streamlit as st
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re

# =========================== 
# STREAMLIT CONFIGURATION
# =========================== 
st.set_page_config(
    page_title="Metal Music Social",
    page_icon="🤘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Elegant dark theme
st.markdown("""
    <style>
        body { background-color: #0a0e27; color: #e0e0e0; }
        .stButton>button { 
            background-color: #8b0000;
            color: #ffffff;
            font-weight: bold;
            border: 2px solid #ff4444;
        }
        .stButton>button:hover {
            background-color: #b30000;
            border: 2px solid #ff6666;
        }
        .tag-clickable {
            cursor: pointer;
            color: #ff6b6b;
            text-decoration: none;
            font-weight: bold;
            padding: 2px 6px;
        }
        .tag-clickable:hover {
            color: #ff9999;
            background-color: rgba(255, 107, 107, 0.1);
            border-radius: 4px;
        }
    </style>
""", unsafe_allow_html=True)

# =========================== 
# DATABASE - SQLITE
# =========================== 
DB_PATH = "metal_music.db"

def init_db():
    """Initialize the database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
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
    
    c.execute('''CREATE INDEX IF NOT EXISTS idx_albums_username ON albums(username)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_concerts_username ON concerts(username)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_concerts_date ON concerts(date)''')
    
    conn.commit()
    conn.close()

def load_albums():
    """Load all albums"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT * FROM albums ORDER BY timestamp DESC')
        rows = c.fetchall()
        conn.close()
        
        albums = []
        for row in rows:
            albums.append({
                'id': row[0],
                'username': row[1],
                'url': row[2],
                'artist': row[3],
                'album_name': row[4],
                'cover_url': row[5],
                'platform': row[6],
                'tags': eval(row[7]) if isinstance(row[7], str) else row[7],
                'likes': eval(row[8]) if isinstance(row[8], str) else [],
                'timestamp': datetime.fromisoformat(row[9])
            })
        return albums
    except Exception as e:
        st.error(f"Error loading albums: {e}")
        return []

def load_concerts():
    """Load all concerts"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT * FROM concerts ORDER BY date ASC')
        rows = c.fetchall()
        conn.close()
        
        concerts = []
        for row in rows:
            concerts.append({
                'id': row[0],
                'username': row[1],
                'bands': row[2],
                'date': row[3],
                'venue': row[4],
                'city': row[5],
                'tags': eval(row[6]) if isinstance(row[6], str) else row[6],
                'info': row[7],
                'likes': eval(row[8]) if isinstance(row[8], str) else [],
                'timestamp': datetime.fromisoformat(row[9])
            })
        return concerts
    except Exception as e:
        st.error(f"Error loading concerts: {e}")
        return []

def save_album(username, url, artist, album_name, cover_url, platform, tags):
    """Save a new album"""
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
        st.error(f"Error saving album: {e}")
        return False

def save_concert(username, bands, date, venue, city, tags, info):
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
        st.error(f"Error saving concert: {e}")
        return False

def update_album_likes(album_id, likes_list):
    """Update album likes"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE albums SET likes = ? WHERE id = ?', (str(likes_list), album_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error updating likes: {e}")
        return False

def update_concert_likes(concert_id, likes_list):
    """Update concert likes"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE concerts SET likes = ? WHERE id = ?', (str(likes_list), concert_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error updating likes: {e}")
        return False

def delete_album(album_id):
    """Delete an album"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM albums WHERE id = ?', (album_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error deleting album: {e}")
        return False

def delete_concert(concert_id):
    """Delete a concert"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM concerts WHERE id = ?', (concert_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error deleting concert: {e}")
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
        st.error(f"Error cleaning concerts: {e}")

# =========================== 
# UNIVERSAL METADATA EXTRACTOR
# =========================== 

def detect_platform(url):
    """Detect platform based on domain"""
    platforms = {
        'spotify': 'Spotify',
        'bandcamp': 'Bandcamp',
        'tidal': 'Tidal',
        'music.apple': 'Apple Music',
        'deezer': 'Deezer',
        'youtube': 'YouTube Music',
        'soundcloud': 'SoundCloud',
        'genius': 'Genius',
        'last.fm': 'Last.fm',
        'pandora': 'Pandora',
        'amazon': 'Amazon Music',
        'jiosaavn': 'JioSaavn',
    }
    
    for key, value in platforms.items():
        if key in url.lower():
            return value
    return 'Music Service'

def extract_artist(metadata, platform):
    """Extract artist name from title"""
    title = metadata.get('og_title', '')
    description = metadata.get('og_description', '')
    
    if ' - ' in title:
        parts = title.split(' - ')
        if len(parts) >= 2:
            return parts[-1].strip()
    
    if 'by' in description:
        match = re.search(r'by (.+?)$|by (.+?) on', description, re.IGNORECASE)
        if match:
            return match.group(1) or match.group(2)
    
    if ' by ' in title:
        return title.split(' by ')[-1].strip()
    
    return 'Unknown Artist'

def extract_album(metadata, platform):
    """Extract album name"""
    title = metadata.get('og_title', '')
    
    if ' - ' in title:
        parts = title.split(' - ')
        return parts[0].strip()
    
    if ' by ' in title:
        return title.split(' by ')[0].strip()
    
    return title or 'Unknown Album'

def extract_og_metadata(url):
    """
    Universal extractor using Open Graph metadata
    Works with ANY platform (Spotify, Bandcamp, Tidal, Apple Music, etc.)
    Similar to how WhatsApp/Discord/Twitter do it
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=8, headers=headers)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        metadata = {}
        
        # Search for Open Graph meta tags
        for meta in soup.find_all('meta', property=True):
            prop = meta.get('property', '')
            content = meta.get('content', '')
            
            if prop == 'og:title':
                metadata['og_title'] = content
            elif prop == 'og:description':
                metadata['og_description'] = content
            elif prop == 'og:image':
                metadata['og_image'] = content
        
        # Fallback: search for meta name
        if not metadata.get('og_title'):
            for meta in soup.find_all('meta'):
                name = meta.get('name', '')
                content = meta.get('content', '')
                if name.lower() == 'description':
                    metadata['og_description'] = content
        
        if not metadata.get('og_image'):
            img = soup.find('img')
            if img:
                img_src = img.get('src', '')
                if img_src.startswith('http'):
                    metadata['og_image'] = img_src
        
        return metadata if metadata else None
        
    except Exception as e:
        st.warning(f"Could not fetch metadata: {e}")
        return None

# =========================== 
# SESSION STATE INITIALIZATION
# =========================== 

if 'username' not in st.session_state:
    st.session_state.username = None
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'filter_tag' not in st.session_state:
    st.session_state.filter_tag = None

# Initialize database
init_db()

# =========================== 
# SIDEBAR - MAIN NAVIGATION
# =========================== 

with st.sidebar:
    st.title("🤘 Metal Wall")
    
    if st.session_state.username:
        st.write(f"**User:** {st.session_state.username}")
        if st.button("Logout"):
            st.session_state.username = None
            st.session_state.page = 'home'
            st.rerun()
    else:
        st.write("*Not logged in*")
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏠 Home"):
            st.session_state.page = 'home'
            st.session_state.filter_tag = None
            st.rerun()
    
    with col2:
        if st.button("🎵 Feed"):
            st.session_state.page = 'feed'
            st.session_state.filter_tag = None
            st.rerun()
    
    with col3:
        if st.button("🎤 Concerts"):
            st.session_state.page = 'concerts'
            st.session_state.filter_tag = None
            st.rerun()
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🏆 Ranking"):
            st.session_state.page = 'ranking'
            st.session_state.filter_tag = None
            st.rerun()
    
    with col2:
        if st.button("➕ Add Album"):
            st.session_state.page = 'add_album'
            st.rerun()
    
    st.divider()

# =========================== 
# HOME PAGE
# =========================== 

def display_home():
    st.title("🤘 Metal Wall - Music Social Network")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not st.session_state.username:
            st.subheader("Login")
            username = st.text_input("Enter your username", key="login_username")
            if st.button("Login", key="btn_login"):
                if username.strip():
                    st.session_state.username = username
                    st.success(f"Welcome, {username}!")
                    st.rerun()
                else:
                    st.error("Please enter a username")
    
    with col2:
        st.subheader("About Metal Wall")
        st.write("""
        Share your favorite metal albums, discover new bands, and connect with other metalheads.
        
        - 🎵 Share albums from any music platform
        - 🏆 Check out rankings by genre
        - 🎤 Find upcoming metal concerts
        - 👥 Connect with other fans
        """)
    
    st.divider()
    
    st.subheader("Recent Albums")
    albums = load_albums()
    
    if albums:
        for album in albums[:5]:
            with st.container(border=True):
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    if album['cover_url']:
                        st.image(album['cover_url'], width=100)
                with col2:
                    st.write(f"**{album['album_name']}**")
                    st.write(f"*{album['artist']}*")
                    st.write(f"📱 {album['platform']}")
                    
                    # Display tags as clickable hashtags
                    tag_string = " ".join([f"#{tag}" for tag in album['tags']])
                    col_tag, _ = st.columns([2, 1])
                    with col_tag:
                        for tag in album['tags']:
                            if st.button(f"#{tag}", key=f"tag_home_{album['id']}_{tag}", use_container_width=False):
                                st.session_state.filter_tag = tag
                                st.session_state.page = 'feed'
                                st.rerun()
                    
                    st.write(f"👤 Added by {album['username']}")
    else:
        st.info("No albums yet. Be the first to add one!")

# =========================== 
# FEED PAGE (ALBUMS WALL)
# =========================== 

def display_feed():
    st.title("🎵 Albums Feed")
    
    albums = load_albums()
    
    # Get all unique tags for filtering
    all_tags = set()
    for album in albums:
        all_tags.update(album['tags'])
    all_tags = sorted(list(all_tags))
    
    # Filter display
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.session_state.filter_tag:
            st.info(f"Filtered by: #{st.session_state.filter_tag}")
    with col2:
        if st.button("Clear filter", key="btn_clear_feed"):
            st.session_state.filter_tag = None
            st.rerun()
    
    st.divider()
    
    # Filter albums if needed
    if st.session_state.filter_tag:
        albums = [a for a in albums if st.session_state.filter_tag in a['tags']]
    
    if albums:
        for album in albums:
            with st.container(border=True):
                col1, col2, col3 = st.columns([1, 4, 1])
                
                with col1:
                    if album['cover_url']:
                        st.image(album['cover_url'], width=120)
                
                with col2:
                    st.write(f"### {album['album_name']}")
                    st.write(f"**{album['artist']}** • {album['platform']}")
                    
                    # Clickable tags only (no separate buttons)
                    tag_html = " ".join([f'<span class="tag-clickable" onclick="window.location.href=\'?tag={tag}\'">#​{tag}</span>' for tag in album['tags']])
                    st.markdown(tag_html, unsafe_allow_html=True)
                    
                    st.write(f"👤 {album['username']} • {album['timestamp'].strftime('%d/%m/%Y')}")
                    st.write(f"[🔗 Listen on {album['platform']}]({album['url']})")
                
                with col3:
                    likes = album['likes']
                    num_likes = len(likes)
                    
                    if st.session_state.username:
                        if st.session_state.username in likes:
                            if st.button("❤️", key=f"like_{album['id']}", help="Unlike"):
                                likes.remove(st.session_state.username)
                                update_album_likes(album['id'], likes)
                                st.rerun()
                        else:
                            if st.button("🤍", key=f"like_{album['id']}", help="Like"):
                                likes.append(st.session_state.username)
                                update_album_likes(album['id'], likes)
                                st.rerun()
                    
                    st.write(f"**{num_likes}** likes")
                    
                    if st.session_state.username == album['username']:
                        if st.button("🗑️ Delete", key=f"delete_{album['id']}"):
                            delete_album(album['id'])
                            st.success("Album deleted!")
                            st.rerun()
    else:
        st.info("No albums found. Try a different filter or add one!")

# =========================== 
# RANKING PAGE
# =========================== 

def display_ranking():
    st.title("🏆 Ranking by Genre")
    
    albums = load_albums()
    
    # Get all unique tags
    all_tags = set()
    for album in albums:
        all_tags.update(album['tags'])
    all_tags = sorted(list(all_tags))
    
    if not all_tags:
        st.info("No genres available yet")
        return
    
    # Create ranking for each genre
    for genre in all_tags:
        st.subheader(f"🎸 #{genre}")
        
        # Get albums with this genre and sort by likes
        genre_albums = [a for a in albums if genre in a['tags']]
        genre_albums.sort(key=lambda x: len(x['likes']), reverse=True)
        
        # Display top 10
        for idx, album in enumerate(genre_albums[:10], 1):
            col1, col2, col3, col4 = st.columns([0.5, 1, 3, 1])
            
            with col1:
                st.write(f"**#{idx}**")
            
            with col2:
                if album['cover_url']:
                    st.image(album['cover_url'], width=80)
            
            with col3:
                st.write(f"**{album['album_name']}** - {album['artist']}")
                
                # Clickable tags only
                for tag in album['tags']:
                    if st.button(f"#{tag}", key=f"tag_ranking_{album['id']}_{tag}", use_container_width=False):
                        st.session_state.filter_tag = tag
                        st.session_state.page = 'feed'
                        st.rerun()
            
            with col4:
                st.write(f"❤️ **{len(album['likes'])}**")
        
        st.divider()

# =========================== 
# ADD ALBUM PAGE
# =========================== 

def display_add_album():
    if not st.session_state.username:
        st.warning("Please login first to add an album")
        return
    
    st.title("➕ Add New Album")
    
    url = st.text_input("Paste the link to the album (Spotify, Bandcamp, etc.)")
    
    if url:
        if st.button("Get album info", key="btn_extract"):
            metadata = extract_og_metadata(url)
            
            if metadata:
                st.session_state.metadata = metadata
            else:
                st.error("Could not fetch album information. Please check the URL.")
    
    if 'metadata' in st.session_state:
        metadata = st.session_state.metadata
        
        st.divider()
        st.subheader("Album details")
        
        platform = detect_platform(url)
        artist = st.text_input("Artist", value=extract_artist(metadata, platform))
        album_name = st.text_input("Album name", value=extract_album(metadata, platform))
        
        tags_input = st.text_input("Tags (separated by spaces, e.g., deathmetal blackmetal thrash)")
        tags = [tag.lower().strip() for tag in tags_input.split() if tag.strip()]
        
        if metadata.get('og_image'):
            st.image(metadata['og_image'], width=200)
        
        if st.button("Add Album", key="btn_add_album"):
            if artist and album_name and tags:
                if save_album(st.session_state.username, url, artist, album_name, 
                             metadata.get('og_image'), platform, tags):
                    st.success("Album added successfully! 🤘")
                    del st.session_state.metadata
                    st.rerun()
                else:
                    st.error("Error saving album")
            else:
                st.error("Please fill in all fields")

# =========================== 
# CONCERTS PAGE
# =========================== 

def display_concerts():
    st.title("🎤 Metal Concerts")
    
    if st.session_state.username:
        with st.expander("➕ Add New Concert"):
            bands = st.text_input("Bands (separated by commas)")
            concert_date = st.date_input("Date")
            venue = st.text_input("Venue")
            city = st.text_input("City")
            tags_input = st.text_input("Tags (separated by spaces)")
            info = st.text_area("Additional info")
            
            tags = [tag.lower().strip() for tag in tags_input.split() if tag.strip()]
            
            if st.button("Add Concert"):
                if bands and venue and city and tags:
                    if save_concert(st.session_state.username, bands, concert_date, 
                                   venue, city, tags, info):
                        st.success("Concert added!")
                        st.rerun()
                    else:
                        st.error("Error saving concert")
                else:
                    st.error("Please fill in all required fields")
    
    st.divider()
    
    concerts = load_concerts()
    
    # Get all unique tags for filtering
    all_tags = set()
    for concert in concerts:
        all_tags.update(concert['tags'])
    all_tags = sorted(list(all_tags))
    
    # Filter display
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.session_state.filter_tag:
            st.info(f"Filtered by: #{st.session_state.filter_tag}")
    with col2:
        if st.button("Clear filter", key="btn_clear_concerts"):
            st.session_state.filter_tag = None
            st.rerun()
    
    st.divider()
    
    # Filter concerts if needed
    if st.session_state.filter_tag:
        concerts = [c for c in concerts if st.session_state.filter_tag in c['tags']]
    
    if concerts:
        for concert in concerts:
            with st.container(border=True):
                st.write(f"### 🎸 {concert['bands']}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"📅 **{concert['date']}**")
                with col2:
                    st.write(f"📍 **{concert['venue']}**")
                with col3:
                    st.write(f"🏙️ **{concert['city']}**")
                
                # Clickable tags only
                tag_cols = st.columns(len(concert['tags']) if concert['tags'] else 1)
                for idx, tag in enumerate(concert['tags']):
                    with tag_cols[idx]:
                        if st.button(f"#{tag}", key=f"tag_concert_{concert['id']}_{tag}", use_container_width=False):
                            st.session_state.filter_tag = tag
                            st.session_state.page = 'concerts'
                            st.rerun()
                
                if concert['info']:
                    st.write(f"**Info:** {concert['info']}")
                
                st.write(f"👤 {concert['username']}")
                
                col1, col2 = st.columns([4, 1])
                with col2:
                    if st.session_state.username == concert['username']:
                        if st.button("🗑️ Delete", key=f"delete_concert_{concert['id']}"):
                            delete_concert(concert['id'])
                            st.success("Concert deleted!")
                            st.rerun()
    else:
        st.info("No concerts found")
    
    # Auto-cleanup of past concerts (weekly)
    if 'last_cleanup' not in st.session_state:
        st.session_state.last_cleanup = datetime.now()
    
    if (datetime.now() - st.session_state.last_cleanup).days >= 7:
        delete_past_concerts()
        st.session_state.last_cleanup = datetime.now()

# =========================== 
# MAIN APP ROUTER
# =========================== 

if st.session_state.page == 'home':
    display_home()
elif st.session_state.page == 'feed':
    display_feed()
elif st.session_state.page == 'ranking':
    display_ranking()
elif st.session_state.page == 'add_album':
    display_add_album()
elif st.session_state.page == 'concerts':
    display_concerts()
else:
    display_home()
