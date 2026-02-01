# ===========================
# METAL MUSIC SOCIAL - STREAMLIT APP v3.3
# ===========================
# NEW: Universal Metadata Extractor (Open Graph)
# Works with: Spotify, Bandcamp, Tidal, Apple Music, YouTube, SoundCloud, etc.
# Like when you paste a link in WhatsApp - works ALWAYS

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
# INITIALIZE SESSION STATE
# ===========================

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
    is_liked = st.session_state.current_user in likes
    
    col1, col2 = st.columns([1.3, 3.5])
    with col1:
        st.markdown(cover_html, unsafe_allow_html=True)
    with col2:
        st.markdown(f'**{artist}**', unsafe_allow_html=True)
        st.markdown(f'{album_name}', unsafe_allow_html=True)
        st.caption(f'📱 {platform} • {get_time_ago(timestamp)} • @{username}')
    
    col_tags, col_like, col_delete = st.columns([3, 0.5, 0.5])
    
    with col_tags:
        # Show tags in one line
        if tags:
            tags_html = ' '.join([f'#{tag}' for tag in tags])
            st.markdown(tags_html, unsafe_allow_html=True)
        
        # Filter buttons in one line using horizontal container
        tag_cols = st.columns(len(tags)) if tags else []
        for idx, tag in enumerate(tags):
            with tag_cols[idx]:
                if st.button(f"🔍 {tag}", key=f"feed_tag_{album['id']}_{tag}", help=f"Filter by {tag}"):
                    st.session_state.active_filter_feed = tag
                    st.rerun()
    
    with col_like:
        if st.button("❤️" if is_liked else "🤍", key=f"like_{album['id']}", help="Like"):
            if is_liked:
                likes.remove(st.session_state.current_user)
            else:
                likes.append(st.session_state.current_user)
            update_album_likes(album['id'], likes)
            st.rerun()
        st.caption(f"{current_likes}")
    
    with col_delete:
        if st.session_state.current_user == username:
            if st.button("🗑️", key=f"delete_{album['id']}", help="Delete"):
                delete_album(album['id'])
                st.rerun()
    
    st.divider()

def display_concert_post(concert):
    """Display a concert post without tags or like button"""
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
    
    # Only delete button, no tags or like
    if st.session_state.current_user == concert['username']:
        if st.button("🗑️", key=f"delete_concert_{concert['id']}", help="Delete"):
            delete_concert(concert['id'])
            st.rerun()
    
    st.divider()

# ===========================
# MAIN PAGE
# ===========================

def main():
    """Main app function"""
    
    # ============ Header ============
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("🤘 Metal Music Social")
    with col2:
        if st.session_state.current_user:
            if st.button("🚪 Logout"):
                st.session_state.current_user = None
                st.rerun()
    
    # ============ Sidebar - Authentication ============
    with st.sidebar:
        st.header("👤 User")
        if not st.session_state.current_user:
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                ok, email = verify_credentials(username, password)
                if ok:
                    st.session_state.current_user = username
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        else:
            st.success(f"✅ Connected as @{st.session_state.current_user}")
        
        st.divider()
        
        # ============ Navigation ============
        page = st.sidebar.radio(
            "📱 Navigation",
            ["📜 Feed", "🎵 New Post", "🎸 Concerts", "🏆 Ranking", "👤 Profile"],
            label_visibility="collapsed"
        )
        
        st.sidebar.divider()
        st.sidebar.markdown("🤘 Metal Music Social v3.3")
    
    # ============ ONLY IF AUTHENTICATED ============
    if not st.session_state.current_user:
        st.warning("⚠️ Please login first")
        return
    
    # ============ PAGE: FEED ============
    if page == "📜 Feed":
        st.subheader("📜 Global Feed")
        albums = load_albums()
        
        if st.session_state.active_filter_feed:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"🔍 Filtered by: **#{st.session_state.active_filter_feed}**")
            with col2:
                if st.button("✖️ Clear filter", key="clear_feed_filter"):
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
        
        # Create two columns for the two input methods
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Automatic (from URL)")
            st.write("Paste a URL of your favorite album")
            
            with st.form("album_form_auto"):
                url = st.text_input("Album URL", placeholder="https://open.spotify.com/album/...", key="auto_url")
                tags_input = st.text_input("Tags", placeholder="Example: #deathmetal #classicmetal", help="Maximum 5 tags", key="auto_tags")
                submitted_auto = st.form_submit_button("🚀 Share from URL", use_container_width=True)
                
                if submitted_auto:
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
                                    st.success("✅ Album shared!")
                                    st.rerun()
                                else:
                                    st.error("❌ Error saving")
                            else:
                                st.error("❌ Could not extract metadata. Verify the URL or use Manual Input")
                    else:
                        st.warning("⚠️ Please paste a valid URL")
        
        with col2:
            st.write("### Manual Input")
            st.write("For platforms without automatic metadata")
            
            with st.form("album_form_manual"):
                artist = st.text_input("Artist", placeholder="Artist name", key="manual_artist")
                album_name = st.text_input("Album Name", placeholder="Album title", key="manual_album")
                url = st.text_input("Album URL (optional)", placeholder="https://...", key="manual_url")
                cover_url = st.text_input("Cover URL (optional)", placeholder="https://...", key="manual_cover")
                platform = st.selectbox(
                    "Platform",
                    ["Spotify", "Bandcamp", "YouTube", "SoundCloud", "Apple Music", "Tidal", "Deezer", "Other"],
                    key="manual_platform"
                )
                tags_input = st.text_input("Tags", placeholder="Example: #deathmetal #classicmetal", help="Maximum 5 tags", key="manual_tags")
                submitted_manual = st.form_submit_button("📝 Share Manually", use_container_width=True)
                
                if submitted_manual:
                    if artist and album_name:
                        # If no URL provided, use a placeholder
                        if not url:
                            url = "#"
                        
                        tags = process_tags(tags_input)
                        if save_album(
                            st.session_state.current_user,
                            url,
                            artist,
                            album_name,
                            cover_url,
                            platform,
                            tags
                        ):
                            st.success("✅ Album shared!")
                            st.rerun()
                        else:
                            st.error("❌ Error saving")
                    else:
                        st.warning("⚠️ Artist and Album Name are required")
    
    # ============ PAGE: CONCERTS ============
    elif page == "🎸 Concerts":
        st.subheader("🎸 Concerts")
        delete_past_concerts()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Upcoming metal events")
        with col2:
            if st.button("➕ New Concert"):
                st.session_state.show_concert_form = not st.session_state.show_concert_form
        
        if st.session_state.show_concert_form:
            with st.form("concert_form"):
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
                            st.success("✅ Concert added!")
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
        albums = load_albums()
        albums_sorted = sorted(albums, key=lambda x: len(x.get('likes', [])), reverse=True)
        
        if st.session_state.active_filter_ranking:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"🔍 Filtered by: **#{st.session_state.active_filter_ranking}**")
            with col2:
                if st.button("✖️ Clear filter", key="clear_ranking_filter"):
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
        st.subheader("👤 My Profile")
        albums = load_albums()
        concerts = load_concerts()
        my_albums = [a for a in albums if a['username'] == st.session_state.current_user]
        my_concerts = [c for c in concerts if c['username'] == st.session_state.current_user]
        
        # Removed the user stats section (the three columns with metrics)
        
        st.divider()
        
        if my_albums or my_concerts:
            if my_albums:
                st.write("### 🎵 My Albums")
                for album in my_albums:
                    display_album_post(album)
            
            if my_concerts:
                st.write("### 🎸 My Concerts")
                for concert in my_concerts:
                    display_concert_post(concert)
        else:
            st.info("📭 You haven't shared anything yet")

# ===========================
# RUN APP
# ===========================

if __name__ == "__main__":
    main()