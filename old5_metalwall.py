# ===========================
# THE METAL WALL - STREAMLIT APP v0.2
# ===========================
# NEW: Session persistence with browser localStorage
# NEW: Confirmation pop-ups and form reset
# NEW: Guest browsing without login

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
    page_title="The Metal Wall",
    page_icon="🤘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Elegant dark theme
st.markdown("""
<style>
    body {
        background-color: #0a0e27;
        color: #e0e0e0;
    }
    .clickable-image {
        cursor: pointer;
        transition: transform 0.2s;
    }
    .clickable-image:hover {
        transform: scale(1.02);
    }
    .tag-button {
        margin-right: 5px;
        margin-bottom: 2px;
    }
    /* Success notification styling */
    .stSuccess {
        background-color: #1a472a !important;
        border-color: #2e7d32 !important;
        color: #e0e0e0 !important;
    }
    .guest-notice {
        background-color: #2d3748;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        border-left: 4px solid #4299e1;
    }
</style>
""", unsafe_allow_html=True)

# ===========================
# DATABASE - SQLITE
# ===========================

DB_PATH = "metal_music.db"

def init_db():
    """Initialize database"""
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
    """Update likes"""
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
    return 'Other'

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
    UNIVERSAL extractor using Open Graph metadata
    Works with ANY platform (Spotify, Bandcamp, Tidal, Apple Music, etc.)
    Similar to how WhatsApp/Discord/Twitter does it
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
        
        # Look for Open Graph meta tags
        for meta in soup.find_all('meta', property=True):
            prop = meta.get('property', '')
            content = meta.get('content', '')
            if prop == 'og:title':
                metadata['og_title'] = content
            elif prop == 'og:description':
                metadata['og_description'] = content
            elif prop == 'og:image':
                metadata['og_image'] = content
        
        # Fallback: look for meta name
        if not metadata.get('og_title'):
            for meta in soup.find_all('meta'):
                name = meta.get('name', '')
                content = meta.get('content', '')
                if name.lower() == 'description':
                    metadata['og_description'] = content
                elif name.lower() == 'twitter:title':
                    metadata['og_title'] = content
                elif name.lower() == 'twitter:image':
                    metadata['og_image'] = content
        
        if not metadata.get('og_title'):
            return None
        
        platform = detect_platform(url)
        return {
            'artist': extract_artist(metadata, platform),
            'album_name': extract_album(metadata, platform),
            'cover_url': metadata.get('og_image', ''),
            'platform': platform
        }
    except Exception as e:
        return None

# ===========================
# SESSION PERSISTENCE WITH QUERY PARAMS
# ===========================

def save_session_to_storage():
    """Save current session state to browser's localStorage using query params"""
    if st.session_state.get('remember_me', False) and st.session_state.get('current_user'):
        session_data = {
            'username': st.session_state.current_user,
            'remember_me': True,
            'timestamp': datetime.now().isoformat()
        }
        # Encode the session data and set it as a query parameter
        import base64
        encoded_data = base64.urlsafe_b64encode(json.dumps(session_data).encode()).decode()
        st.query_params['session'] = encoded_data

def load_session_from_storage():
    """Load session from query parameters"""
    try:
        if 'session' in st.query_params:
            import base64
            encoded_data = st.query_params['session']
            session_data = json.loads(base64.urlsafe_b64decode(encoded_data).decode())
            
            # Check if session is not too old (7 days max)
            session_time = datetime.fromisoformat(session_data['timestamp'])
            if (datetime.now() - session_time).days < 7:
                st.session_state.current_user = session_data['username']
                st.session_state.remember_me = session_data['remember_me']
                return True
    except:
        pass
    return False

def clear_session_storage():
    """Clear the session from query params"""
    # Clear only the session parameter
    params = dict(st.query_params)
    if 'session' in params:
        del params['session']
        st.query_params.clear()
        for key, value in params.items():
            st.query_params[key] = value

# ===========================
# INITIALIZE SESSION STATE
# ===========================

# Initialize session state variables
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'show_album_form' not in st.session_state:
    st.session_state.show_album_form = False
if 'show_concert_form' not in st.session_state:
    st.session_state.show_concert_form = False
if 'active_filter_feed' not in st.session_state:
    st.session_state.active_filter_feed = None
if 'active_filter_ranking' not in st.session_state:
    st.session_state.active_filter_ranking = None
if 'active_filter_concerts' not in st.session_state:
    st.session_state.active_filter_concerts = None
if 'show_manual_input' not in st.session_state:
    st.session_state.show_manual_input = False
if 'remember_me' not in st.session_state:
    st.session_state.remember_me = False
if 'username_input' not in st.session_state:
    st.session_state.username_input = ""
if 'password_input' not in st.session_state:
    st.session_state.password_input = ""
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False
if 'success_message' not in st.session_state:
    st.session_state.success_message = ""

# Try to load session from storage
if st.session_state.current_user is None:
    load_session_from_storage()

init_db()

# ===========================
# AUTHENTICATION FUNCTIONS
# ===========================

def verify_credentials(username, password):
    """Verify credentials"""
    try:
        if username in st.secrets:
            if st.secrets[username]["password"] == password:
                return True, st.secrets[username].get("email", username)
        return False, None
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return False, None

# ===========================
# UTILITY FUNCTIONS
# ===========================

def get_time_ago(timestamp):
    """Calculate relative time"""
    now = datetime.now()
    diff = now - timestamp
    minutes = int(diff.total_seconds() / 60)
    hours = int(diff.total_seconds() / 3600)
    days = int(diff.total_seconds() / 86400)
    
    if minutes < 1:
        return "just now"
    elif minutes < 60:
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif hours < 24:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        return f"{days} day{'s' if days > 1 else ''} ago"

def format_date_display(date_str):
    """Convert YYYY-MM-DD to DD/MM/YYYY"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%d/%m/%Y')
    except:
        return date_str

def get_days_until(date_str):
    """Calculate days until concert"""
    try:
        concert_date = datetime.strptime(date_str, '%Y-%m-%d')
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        concert_date = concert_date.replace(hour=0, minute=0, second=0, microsecond=0)
        return (concert_date - today).days
    except:
        return 0

def process_tags(tags_str):
    """Process tags"""
    tags = []
    for tag in tags_str.split():
        tag = tag.strip()
        if tag:
            if tag.startswith('#'):
                tag = tag[1:]
            if tag.replace('_', '').isalnum():
                tags.append(tag)
    return tags[:5]

def show_success_message(message):
    """Show a success message"""
    st.session_state.success_message = message
    st.session_state.form_submitted = True
    st.success(message)

# ===========================
# UI COMPONENTS
# ===========================

def display_album_post(album):
    """Display an album post like Twitter/Mastodon"""
    cover_url = album.get('cover_url', '')
    username = album.get('username', 'Unknown')
    url = album.get('url', '#')
    artist = album.get('artist', 'Unknown')
    album_name = album.get('album_name', 'Unknown')
    platform = album.get('platform', '')
    timestamp = album.get('timestamp', '')
    tags = album.get('tags', [])
    
    if cover_url:
        cover_html = f'<a href="{url}" target="_blank" style="text-decoration: none;"><img src="{cover_url}" class="clickable-image" style="width:100%; border-radius:8px; object-fit:cover; height:180px;"></a>'
    else:
        cover_html = '<div style="width:100%; height:180px; background:#333; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#666;">No cover</div>'
    
    likes = album.get('likes', [])
    current_likes = len(likes)
    is_liked = st.session_state.current_user in likes if st.session_state.current_user else False
    
    col1, col2 = st.columns([1.3, 3.5])
    with col1:
        st.markdown(cover_html, unsafe_allow_html=True)
    with col2:
        st.markdown(f'**{artist}**', unsafe_allow_html=True)
        st.markdown(f'{album_name}', unsafe_allow_html=True)
        st.caption(f'📱 {platform} • {get_time_ago(timestamp)} • @{username}')
    
    # Create a container for the bottom row with tags, like, and delete
    bottom_container = st.container()
    
    with bottom_container:
        # Create columns for the bottom row
        col_tags, col_like_delete = st.columns([3, 1])
        
        with col_tags:
            # Only show tag buttons, not the text tags
            if tags:
                # Create a horizontal container for tag buttons
                tag_cols = st.columns(len(tags))
                for idx, tag in enumerate(tags):
                    with tag_cols[idx]:
                        if st.button(f"#{tag}", key=f"feed_tag_{album['id']}_{tag}", 
                                    help=f"Filter by {tag}", use_container_width=True):
                            st.session_state.active_filter_feed = tag
                            st.rerun()
        
        with col_like_delete:
            # Create sub-columns for like and delete within this column
            like_col, delete_col = st.columns([2, 1])
            
            with like_col:
                # Only show like button if user is logged in
                if st.session_state.current_user:
                    # Like button with count displayed next to it
                    like_text = f"{'❤️' if is_liked else '🤍'} {current_likes}"
                    if st.button(like_text, key=f"like_{album['id']}", 
                               help="Like", use_container_width=True):
                        if is_liked:
                            likes.remove(st.session_state.current_user)
                        else:
                            likes.append(st.session_state.current_user)
                        update_album_likes(album['id'], likes)
                        st.rerun()
                else:
                    # For guest, just show the likes count
                    st.markdown(f"❤️ {current_likes}")
            
            with delete_col:
                # Show delete button only for logged in users
                if st.session_state.current_user:
                    # Admin can delete any post, users can delete their own posts
                    if st.session_state.current_user == "Admin" or st.session_state.current_user == username:
                        if st.button("🗑️", key=f"delete_{album['id']}", 
                                   help="Delete", use_container_width=True):
                            delete_album(album['id'])
                            show_success_message("✅ Album deleted successfully!")
                            st.rerun()
    
    st.divider()

def display_concert_post(concert):
    """Display a concert post"""
    bands = concert.get('bands', 'Unknown')
    date = concert.get('date', '')
    venue = concert.get('venue', 'Unknown')
    city = concert.get('city', 'Unknown')
    info = concert.get('info', '')
    username = concert.get('username', 'Unknown')
    timestamp = concert.get('timestamp', '')
    
    days_until = get_days_until(date)
    date_display = format_date_display(date)
    
    if days_until < 0:
        emoji = "📆"
    elif days_until == 0:
        emoji = "🔴"
    elif days_until <= 7:
        emoji = "🟠"
    else:
        emoji = "🟢"
    
    st.markdown(f'**{bands}**', unsafe_allow_html=True)
    st.markdown(f'{emoji} {date_display} • {venue} • {city}', unsafe_allow_html=True)
    
    if info:
        st.caption(f"ℹ️ {info}")
    
    st.caption(f'{get_time_ago(timestamp)} • @{username}')
    
    # Show delete button only for logged in users
    if st.session_state.current_user:
        # Admin can delete any post, users can delete their own posts
        if st.session_state.current_user == "Admin" or st.session_state.current_user == concert['username']:
            if st.button("🗑️", key=f"delete_concert_{concert['id']}", help="Delete"):
                delete_concert(concert['id'])
                show_success_message("✅ Concert deleted successfully!")
                st.rerun()
    
    st.divider()

# ===========================
# FORM HANDLING
# ===========================

def handle_album_submission(url, tags_input, is_manual=False, artist="", album_name="", cover_url=""):
    """Handle album form submission"""
    if is_manual:
        if artist and album_name and url:
            tags = process_tags(tags_input)
            if save_album(
                st.session_state.current_user,
                url,
                artist,
                album_name,
                cover_url,
                "Other",
                tags
            ):
                show_success_message("✅ Album shared successfully!")
                return True
            else:
                st.error("❌ Error saving")
                return False
        else:
            st.warning("⚠️ Artist, Album Name, and Album URL are required")
            return False
    else:
        if url:
            with st.spinner("⏳ Extracting metadata..."):
                metadata = extract_og_metadata(url)
                if metadata:
                    tags = process_tags(tags_input)
                    if save_album(
                        st.session_state.current_user,
                        url,
                        metadata['artist'],
                        metadata['album_name'],
                        metadata['cover_url'],
                        metadata['platform'],
                        tags
                    ):
                        show_success_message("✅ Album shared successfully!")
                        return True
                    else:
                        st.error("❌ Error saving")
                        return False
                else:
                    st.error("❌ Could not extract metadata. Verify the URL or use Manual Input")
                    return False
        else:
            st.warning("⚠️ Please paste a valid URL")
            return False

# ===========================
# MAIN PAGE
# ===========================

def main():
    """Main app function"""
    
    # ============ Header ============
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("🤘 The Metal Wall")
    with col2:
        if st.session_state.current_user:
            if st.button("🚪 Logout"):
                clear_session_storage()
                st.session_state.current_user = None
                st.session_state.remember_me = False
                st.session_state.username_input = ""
                st.session_state.password_input = ""
                st.rerun()
        else:
            if st.button("👤 Login", key="header_login"):
                st.query_params['show_login'] = "true"
                st.rerun()
    
    # ============ Sidebar ============
    with st.sidebar:
        st.header("👤 User")
        
        # Show login form if user is not logged in or if show_login is in query params
        if not st.session_state.current_user or 'show_login' in st.query_params:
            if 'show_login' in st.query_params:
                st.subheader("Login")
            else:
                st.markdown("### 👋 Welcome!")
                st.markdown("You're browsing as a guest. Login to post content.")
            
            # Remove show_login from query params if it exists
            if 'show_login' in st.query_params:
                # Create a copy of query params and remove show_login
                params = dict(st.query_params)
                del params['show_login']
                st.query_params.clear()
                for key, value in params.items():
                    st.query_params[key] = value
            
            # Login form
            with st.form("login_form"):
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                remember_me = st.checkbox("Remember me", key="login_remember")
                
                submitted = st.form_submit_button("Login", use_container_width=True)
                
                if submitted:
                    ok, email = verify_credentials(username, password)
                    if ok:
                        st.session_state.current_user = username
                        st.session_state.remember_me = remember_me
                        if remember_me:
                            save_session_to_storage()
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
        else:
            st.success(f"✅ Connected as @{st.session_state.current_user}")
        
        st.divider()
        
        # ============ Navigation ============
        page = st.sidebar.radio(
            "📱 Navigation",
            ["💿 Records", "🎵 New Post", "🎸 Gigs", "🏆 Ranking", "👤 Profile"],
            label_visibility="collapsed"
        )
        
        st.sidebar.divider()
        st.sidebar.markdown("\\m/ MetalWall v0.2")
        if st.session_state.current_user:
            st.sidebar.caption("Session persistence enabled")
    
    # ============ PAGE: RECORDS ============
    if page == "💿 Records":
        st.subheader("💿 Records Wall")
        
        # Show guest notice if not logged in
        if not st.session_state.current_user:
            st.markdown("""
            <div class="guest-notice">
            👀 You're browsing as a guest. You can view all content but need to 
            <strong><a href="#" onclick="window.location.href='?show_login=true'">login</a></strong> 
            to like, post, or delete content.
            </div>
            """, unsafe_allow_html=True)
        
        albums = load_albums()
        
        if st.session_state.active_filter_feed:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"🔍 Filtered by: **#{st.session_state.active_filter_feed}**")
            with col2:
                if st.button("✖️ Clear filter", key="clear_feed_filter", use_container_width=True):
                    st.session_state.active_filter_feed = None
                    st.rerun()
        
        if st.session_state.active_filter_feed:
            albums = [a for a in albums if st.session_state.active_filter_feed.lower() in [t.lower() for t in a.get('tags', [])]]
        
        if not albums:
            st.info("📭 No albums with this tag")
        else:
            for album in albums:
                display_album_post(album)
    
    # ============ PAGE: NEW POST ============
    elif page == "🎵 New Post":
        st.subheader("🎵 New Post")
        
        # Check if user is logged in
        if not st.session_state.current_user:
            st.warning("""
            🔒 **Login Required**
            
            You need to login to share albums. 
            
            Please use the login form in the sidebar or click the Login button in the header.
            """)
        else:
            # Show success message if form was just submitted
            if st.session_state.get('form_submitted'):
                st.success(st.session_state.success_message)
                st.session_state.form_submitted = False
            
            # Create two columns for the two input methods
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### Automatic (from URL)")
                st.write("Paste a URL of your favorite album")
                
                with st.form("album_form_auto", clear_on_submit=True):
                    url = st.text_input("Album URL", placeholder="https://open.spotify.com/album/...")
                    tags_input = st.text_input("Tags", placeholder="Example: #deathmetal #classicmetal", 
                                             help="Maximum 5 tags")
                    submitted_auto = st.form_submit_button("🚀 Share from URL", use_container_width=True)
                    
                    if submitted_auto:
                        handle_album_submission(url, tags_input)
            
            with col2:
                st.write("### Manual Input")
                st.write("For platforms without automatic metadata")
                
                with st.form("album_form_manual", clear_on_submit=True):
                    artist = st.text_input("Artist", placeholder="Artist name")
                    album_name = st.text_input("Album Name", placeholder="Album title")
                    url = st.text_input("Album URL", placeholder="https://...")
                    cover_url = st.text_input("Cover URL (optional)", placeholder="https://...")
                    tags_input = st.text_input("Tags", placeholder="Example: #deathmetal #classicmetal", 
                                             help="Maximum 5 tags")
                    submitted_manual = st.form_submit_button("📝 Share Manually", use_container_width=True)
                    
                    if submitted_manual:
                        handle_album_submission(url, tags_input, True, artist, album_name, cover_url)
    
    # ============ PAGE: GIGS ============
    elif page == "🎸 Gigs":
        st.subheader("🎸 Gigs")
        delete_past_concerts()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Upcoming metal events")
        with col2:
            # Only show New Concert button if user is logged in
            if st.session_state.current_user:
                if st.button("➕ New Concert", use_container_width=True):
                    st.session_state.show_concert_form = not st.session_state.show_concert_form
            else:
                st.button("➕ New Concert", disabled=True, use_container_width=True,
                         help="Login to add concerts")
        
        if st.session_state.show_concert_form and st.session_state.current_user:
            with st.form("concert_form", clear_on_submit=True):
                bands = st.text_input("Bands", placeholder="Separate with commas")
                date = st.date_input("Date")
                venue = st.text_input("Venue")
                city = st.text_input("City")
                tags_input = st.text_input("Tags", placeholder="Example: #deathmetal #liveshow")
                info = st.text_area("Additional info", placeholder="Tickets, prices, etc.")
                submitted = st.form_submit_button("✅ Save Concert", use_container_width=True)
                
                if submitted:
                    if bands and venue and city:
                        tags = process_tags(tags_input)
                        if save_concert(st.session_state.current_user, bands, date, venue, city, tags, info):
                            show_success_message("✅ Concert added successfully!")
                            st.session_state.show_concert_form = False
                            st.rerun()
                        else:
                            st.error("❌ Error saving")
                    else:
                        st.warning("⚠️ Please complete all required fields")
        
        st.divider()
        concerts = load_concerts()
        
        if not concerts:
            st.info("📭 No upcoming concerts")
        else:
            for concert in concerts:
                display_concert_post(concert)
    
    # ============ PAGE: RANKING ============
    elif page == "🏆 Ranking":
        st.subheader("🏆 Album Ranking")
        
        # Show guest notice if not logged in
        if not st.session_state.current_user:
            st.markdown("""
            <div class="guest-notice">
            👀 You're browsing as a guest. You can view rankings but need to 
            <strong><a href="#" onclick="window.location.href='?show_login=true'">login</a></strong> 
            to like albums.
            </div>
            """, unsafe_allow_html=True)
        
        albums = load_albums()
        albums_sorted = sorted(albums, key=lambda x: len(x.get('likes', [])), reverse=True)
        
        if st.session_state.active_filter_ranking:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"🔍 Filtered by: **#{st.session_state.active_filter_ranking}**")
            with col2:
                if st.button("✖️ Clear filter", key="clear_ranking_filter", use_container_width=True):
                    st.session_state.active_filter_ranking = None
                    st.rerun()
        
        if st.session_state.active_filter_ranking:
            albums_sorted = [a for a in albums_sorted if st.session_state.active_filter_ranking.lower() in [t.lower() for t in a.get('tags', [])]]
        
        if not albums_sorted:
            st.info("📭 No albums with this tag")
        else:
            for idx, album in enumerate(albums_sorted, 1):
                st.write(f"**#{idx}**")
                display_album_post(album)
    
    # ============ PAGE: PROFILE ============
    elif page == "👤 Profile":
        st.subheader("👤 Profile")
        
        if not st.session_state.current_user:
            st.info("""
            👤 **Your Profile**
            
            Login to see your profile, including:
            - Albums you've shared
            - Concerts you've added
            - Albums you've liked
            - Your activity stats
            
            Use the login form in the sidebar to get started.
            """)
        else:
            albums = load_albums()
            concerts = load_concerts()
            my_albums = [a for a in albums if a['username'] == st.session_state.current_user]
            my_concerts = [c for c in concerts if c['username'] == st.session_state.current_user]
            
            # Get liked albums and concerts
            liked_albums = [a for a in albums if st.session_state.current_user in a.get('likes', [])]
            liked_concerts = [c for c in concerts if st.session_state.current_user in c.get('likes', [])]
            
            # Show counts
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🎵 My Albums", len(my_albums))
            with col2:
                st.metric("🎸 My Gigs", len(my_concerts))
            with col3:
                st.metric("❤️ Liked Albums", len(liked_albums))
            with col4:
                st.metric("🤘 Liked Gigs", len(liked_concerts))
            
            st.divider()
            
            if my_albums:
                st.write("### 🎵 My Albums")
                for album in my_albums:
                    display_album_post(album)
            
            if liked_albums:
                st.write("### ❤️ Liked Albums")
                for album in liked_albums:
                    display_album_post(album)
            
            if my_concerts:
                st.write("### 🎸 My Gigs")
                for concert in my_concerts:
                    display_concert_post(concert)
            
            if liked_concerts:
                st.write("### 🤘 Liked Gigs")
                for concert in liked_concerts:
                    display_concert_post(concert)
            
            if not my_albums and not my_concerts and not liked_albums and not liked_concerts:
                st.info("📭 You haven't shared or liked anything yet")

# ===========================
# RUN APP
# ===========================

if __name__ == "__main__":
    main()