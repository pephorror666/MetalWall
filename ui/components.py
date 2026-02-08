# File: metalwall_app/ui/components.py
# ===========================
# UI COMPONENTS
# ===========================

import streamlit as st
from typing import List, Optional
from datetime import datetime

def render_header():
    """Render the app header with login/logout button"""
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("The Metal Wall")
    with col2:
        if st.session_state.current_user:
            if st.button("🚪 Logout"):
                from utils.session_handler import clear_session_storage
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

def render_sidebar():
    """Render the sidebar with login form and navigation"""
    with st.sidebar:
        st.header("👤 User")
        render_login_form()
        
        st.divider()
        page = render_navigation()
        
        st.sidebar.divider()
        st.sidebar.markdown("\\m/ MetalWall v0.5")
        if st.session_state.current_user:
            st.sidebar.caption("Session persistence enabled")
    
    return page

def render_login_form():
    """Render login form in sidebar"""
    if not st.session_state.current_user or 'show_login' in st.query_params:
        if 'show_login' in st.query_params:
            st.subheader("Login")
        else:
            st.markdown("### 👋 Welcome!")
            st.markdown("You're browsing as a guest. Login to post content.")
        
        # Remove show_login from query params if it exists
        if 'show_login' in st.query_params:
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
                from utils.helpers import verify_credentials
                ok, email = verify_credentials(username, password)
                if ok:
                    st.session_state.current_user = username
                    st.session_state.remember_me = remember_me
                    if remember_me:
                        from utils.session_handler import save_session_to_storage
                        save_session_to_storage()
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
    else:
        st.success(f"✅ Connected as @{st.session_state.current_user}")
        if st.session_state.current_user == "Admin":
            st.info("🔧 Admin privileges enabled")

def render_navigation():
    """Render navigation radio buttons"""
    from config import ADMIN_NAV_OPTIONS, USER_NAV_OPTIONS
    
    nav_options = ADMIN_NAV_OPTIONS if st.session_state.current_user == "Admin" else USER_NAV_OPTIONS
    
    page = st.sidebar.radio(
        "📱 Navigation",
        nav_options,
        label_visibility="collapsed"
    )
    
    return page

def render_album_post(album, show_rank: bool = False, rank: Optional[int] = None):
    """Display an album post like Twitter/Mastodon with edit functionality"""
    # Check if current user can edit this post
    can_edit = (st.session_state.current_user == "Admin" or 
                st.session_state.current_user == album.username)
    
    # Check if we're in edit mode for this album
    is_editing = st.session_state.get(f'editing_album_{album.id}', False)
    
    # If editing mode is active, show edit form
    if is_editing and can_edit:
        render_album_edit_form(album)
        return
    
    # Normal display (when not editing)
    col1, col2 = st.columns([1.3, 3.5])
    
    with col1:
        if album.cover_url:
            st.markdown(f'<a href="{album.url}" target="_blank" style="text-decoration: none;"><img src="{album.cover_url}" style="width:100%; border-radius:8px; object-fit:cover; height:180px;" class="clickable-image"></a>', 
                       unsafe_allow_html=True)
        else:
            st.markdown('<div style="width:100%; height:180px; background:#333; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#666;">No cover</div>', unsafe_allow_html=True)
    
    with col2:
        if show_rank and rank is not None:
            st.markdown(f"**#{rank}**")
        st.markdown(f'**{album.artist}**', unsafe_allow_html=True)
        st.markdown(f'{album.album_name}', unsafe_allow_html=True)
        st.caption(f'📱 {album.platform} • {get_time_ago(album.timestamp)} • @{album.username}')
    
    # Action buttons and tags
    bottom_container = st.container()
    
    with bottom_container:
        col_tags, col_actions = st.columns([3, 1])
        
        with col_tags:
            render_tag_buttons(album.tags, f"feed_tag_{album.id}")
        
        with col_actions:
            render_album_actions(album, can_edit)
    
    st.divider()

def render_album_edit_form(album):
    """Render album edit form"""
    with st.container():
        st.markdown("### ✏️ Edit Album")
        with st.form(f"edit_album_form_{album.id}"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_artist = st.text_input("Artist", value=album.artist, key=f"edit_artist_{album.id}")
                new_album_name = st.text_input("Album Name", value=album.album_name, key=f"edit_album_name_{album.id}")
                new_url = st.text_input("Album URL", value=album.url, key=f"edit_url_{album.id}")
            
            with col2:
                new_cover_url = st.text_input("Cover URL", value=album.cover_url if album.cover_url else "", 
                                             key=f"edit_cover_{album.id}")
                new_platform = st.text_input("Platform", value=album.platform, key=f"edit_platform_{album.id}")
                tags_str = " ".join([f"#{tag}" for tag in album.tags])
                new_tags_input = st.text_input("Tags", value=tags_str, 
                                              placeholder="#tag1 #tag2 #tag3",
                                              key=f"edit_tags_{album.id}")
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                    from database.operations import update_album
                    from utils.helpers import process_tags
                    new_tags = process_tags(new_tags_input)
                    if update_album(album.id, new_url, new_artist, new_album_name, 
                                   new_cover_url, new_platform, new_tags):
                        st.session_state[f'editing_album_{album.id}'] = False
                        st.success("✅ Album updated successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Error updating album")
            
            with col_cancel:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
                    st.session_state[f'editing_album_{album.id}'] = False
                    st.rerun()
        
        st.divider()

def render_album_actions(album, can_edit: bool):
    """Render action buttons for an album post"""
    from database.operations import update_album_likes, delete_album
    
    is_liked = st.session_state.current_user in album.likes if st.session_state.current_user else False
    current_likes = len(album.likes)
    
    if can_edit:
        edit_col, like_col, delete_col = st.columns([1, 2, 1])
        
        with edit_col:
            if st.button("✏️", key=f"edit_{album.id}", help="Edit", use_container_width=True):
                st.session_state[f'editing_album_{album.id}'] = True
                st.rerun()
        
        with like_col:
            render_like_button(album, is_liked, current_likes, f"like_{album.id}")
        
        with delete_col:
            if st.button("🗑️", key=f"delete_{album.id}", help="Delete", use_container_width=True):
                if delete_album(album.id):
                    st.success("✅ Album deleted successfully!")
                    st.rerun()
    else:
        like_col, delete_col = st.columns([2, 1])
        
        with like_col:
            render_like_button(album, is_liked, current_likes, f"like_{album.id}")
        
        with delete_col:
            # Admin can delete any post
            if st.session_state.current_user == "Admin":
                if st.button("🗑️", key=f"delete_{album.id}", help="Delete", use_container_width=True):
                    if delete_album(album.id):
                        st.success("✅ Album deleted successfully!")
                        st.rerun()

def render_like_button(album, is_liked: bool, current_likes: int, key: str):
    """Render like button with count"""
    from database.operations import update_album_likes
    
    if st.session_state.current_user:
        like_text = f"{'❤️' if is_liked else '🤍'} {current_likes}"
        if st.button(like_text, key=key, help="Like", use_container_width=True):
            if is_liked:
                album.likes.remove(st.session_state.current_user)
            else:
                album.likes.append(st.session_state.current_user)
            update_album_likes(album.id, album.likes)
            st.rerun()
    else:
        # For guest, just show the likes count
        st.markdown(f"❤️ {current_likes}")

def render_tag_buttons(tags: List[str], key_prefix: str):
    """Render tag buttons in a horizontal layout"""
    if tags:
        tag_cols = st.columns(len(tags))
        for idx, tag in enumerate(tags):
            with tag_cols[idx]:
                if st.button(f"#{tag}", key=f"{key_prefix}_{tag}", 
                            help=f"Filter by {tag}", use_container_width=True):
                    st.session_state.active_filter_feed = tag
                    st.rerun()

def render_concert_post(concert):
    """Display a concert post with edit functionality"""
    # Check if current user can edit this concert
    can_edit = (st.session_state.current_user == "Admin" or 
                st.session_state.current_user == concert.username)
    
    # Check if we're in edit mode for this concert
    is_editing = st.session_state.get(f'editing_concert_{concert.id}', False)
    
    # If editing mode is active, show edit form
    if is_editing and can_edit:
        render_concert_edit_form(concert)
        return
    
    # Normal display (when not editing)
    from utils.helpers import format_date_display, get_days_until, get_time_ago
    days_until = get_days_until(concert.date)
    date_display = format_date_display(concert.date)
    
    if days_until < 0:
        emoji = "📆"
    elif days_until == 0:
        emoji = "🔴"
    elif days_until <= 7:
        emoji = "🟠"
    else:
        emoji = "🟢"
    
    st.markdown(f'**{concert.bands}**', unsafe_allow_html=True)
    st.markdown(f'{emoji} {date_display} • {concert.venue} • {concert.city}', unsafe_allow_html=True)
    
    if concert.info:
        st.caption(f"ℹ️ {concert.info}")
    
    st.caption(f'{get_time_ago(concert.timestamp)} • @{concert.username}')
    
    # Action buttons
    col_actions = st.columns([1, 1])[0]
    
    with col_actions:
        if can_edit:
            edit_col, delete_col = st.columns(2)
            
            with edit_col:
                if st.button("✏️ Edit", key=f"edit_concert_{concert.id}", 
                           help="Edit concert", use_container_width=True):
                    st.session_state[f'editing_concert_{concert.id}'] = True
                    st.rerun()
            
            with delete_col:
                from database.operations import delete_concert
                if st.button("🗑️ Delete", key=f"delete_concert_{concert.id}", 
                           help="Delete concert", use_container_width=True):
                    if delete_concert(concert.id):
                        st.success("✅ Concert deleted successfully!")
                        st.rerun()
        else:
            # Admin can delete any concert
            if st.session_state.current_user == "Admin":
                from database.operations import delete_concert
                if st.button("🗑️ Delete", key=f"delete_concert_{concert.id}", 
                           help="Delete concert", use_container_width=True):
                    if delete_concert(concert.id):
                        st.success("✅ Concert deleted successfully!")
                        st.rerun()
    
    st.divider()

def render_concert_edit_form(concert):
    """Render concert edit form"""
    from datetime import datetime
    from utils.helpers import process_tags
    from database.operations import update_concert
    
    with st.container():
        st.markdown("### ✏️ Edit Concert")
        with st.form(f"edit_concert_form_{concert.id}"):
            new_bands = st.text_input("Bands", value=concert.bands, 
                                     key=f"edit_bands_{concert.id}")
            new_date = st.date_input("Date", value=datetime.strptime(concert.date, '%Y-%m-%d').date(), 
                                    key=f"edit_date_{concert.id}")
            new_venue = st.text_input("Venue", value=concert.venue, 
                                     key=f"edit_venue_{concert.id}")
            new_city = st.text_input("City", value=concert.city, 
                                    key=f"edit_city_{concert.id}")
            
            tags_str = " ".join([f"#{tag}" for tag in concert.tags])
            new_tags_input = st.text_input("Tags", value=tags_str, 
                                          placeholder="#tag1 #tag2 #tag3",
                                          key=f"edit_tags_concert_{concert.id}")
            
            new_info = st.text_area("Additional info", value=concert.info, 
                                   key=f"edit_info_{concert.id}")
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                    new_tags = process_tags(new_tags_input)
                    if update_concert(concert.id, new_bands, new_date, new_venue, 
                                    new_city, new_tags, new_info):
                        st.session_state[f'editing_concert_{concert.id}'] = False
                        st.success("✅ Concert updated successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Error updating concert")
            
            with col_cancel:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
                    st.session_state[f'editing_concert_{concert.id}'] = False
                    st.rerun()
        
        st.divider()

def get_time_ago(timestamp):
    """Calculate relative time"""
    from datetime import datetime
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