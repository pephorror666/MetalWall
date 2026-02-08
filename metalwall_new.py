# ===========================
# NEW FEATURES
# ===========================

# 1. Add duplicate URL check function
def check_duplicate_url(url):
    """Check if URL already exists in database to avoid duplicates"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM albums WHERE url = ?', (url,))
        count = c.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        st.error(f"Error checking duplicate: {e}")
        return False

# 2. Update album function
def update_album(album_id, url, artist, album_name, cover_url, platform, tags):
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
        st.error(f"Error updating album: {e}")
        return False

# 3. Update concert function
def update_concert(concert_id, bands, date, venue, city, tags, info):
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
        st.error(f"Error updating concert: {e}")
        return False

# ===========================
# MODIFIED ALBUM DISPLAY FUNCTION WITH EDIT
# ===========================

def display_album_post(album):
    """Display an album post like Twitter/Mastodon with edit functionality"""
    cover_url = album.get('cover_url', '')
    username = album.get('username', 'Unknown')
    url = album.get('url', '#')
    artist = album.get('artist', 'Unknown')
    album_name = album.get('album_name', 'Unknown')
    platform = album.get('platform', '')
    timestamp = album.get('timestamp', '')
    tags = album.get('tags', [])
    
    # Check if current user can edit this post
    can_edit = (st.session_state.current_user == "Admin" or 
                st.session_state.current_user == username)
    
    # Check if we're in edit mode for this album
    is_editing = st.session_state.get(f'editing_album_{album["id"]}', False)
    
    # If editing mode is active, show edit form
    if is_editing and can_edit:
        with st.container():
            st.markdown("### ✏️ Edit Album")
            with st.form(f"edit_album_form_{album['id']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_artist = st.text_input("Artist", value=artist, key=f"edit_artist_{album['id']}")
                    new_album_name = st.text_input("Album Name", value=album_name, key=f"edit_album_name_{album['id']}")
                    new_url = st.text_input("Album URL", value=url, key=f"edit_url_{album['id']}")
                
                with col2:
                    new_cover_url = st.text_input("Cover URL", value=cover_url if cover_url else "", 
                                                 key=f"edit_cover_{album['id']}")
                    new_platform = st.text_input("Platform", value=platform, key=f"edit_platform_{album['id']}")
                    tags_str = " ".join([f"#{tag}" for tag in tags])
                    new_tags_input = st.text_input("Tags", value=tags_str, 
                                                  placeholder="#tag1 #tag2 #tag3",
                                                  key=f"edit_tags_{album['id']}")
                
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.form_submit_button("💾 Save Changes", use_container_width=True):
                        new_tags = process_tags(new_tags_input)
                        if update_album(album['id'], new_url, new_artist, new_album_name, 
                                       new_cover_url, new_platform, new_tags):
                            st.session_state[f'editing_album_{album["id"]}'] = False
                            show_success_message("✅ Album updated successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Error updating album")
                
                with col_cancel:
                    if st.form_submit_button("❌ Cancel", use_container_width=True):
                        st.session_state[f'editing_album_{album["id"]}'] = False
                        st.rerun()
            
            st.divider()
            return  # Skip normal display when editing
    
    # Normal display (when not editing)
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
    
    # Create a container for the bottom row with tags, like, edit, and delete
    bottom_container = st.container()
    
    with bottom_container:
        # Create columns for the bottom row
        col_tags, col_actions = st.columns([3, 1])
        
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
        
        with col_actions:
            # Create sub-columns for actions within this column
            if can_edit:
                # Show both edit and delete for users who can edit
                edit_col, like_col, delete_col = st.columns([1, 2, 1])
                
                with edit_col:
                    if st.button("✏️", key=f"edit_{album['id']}", 
                               help="Edit", use_container_width=True):
                        st.session_state[f'editing_album_{album["id"]}'] = True
                        st.rerun()
                
                with like_col:
                    # Like button with count displayed next to it
                    if st.session_state.current_user:
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
                    if st.button("🗑️", key=f"delete_{album['id']}", 
                               help="Delete", use_container_width=True):
                        delete_album(album['id'])
                        show_success_message("✅ Album deleted successfully!")
                        st.rerun()
            else:
                # For users who cannot edit, show like and delete (for admin only)
                like_col, delete_col = st.columns([2, 1])
                
                with like_col:
                    if st.session_state.current_user:
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
                    # Admin can delete any post
                    if st.session_state.current_user == "Admin":
                        if st.button("🗑️", key=f"delete_{album['id']}", 
                                   help="Delete", use_container_width=True):
                            delete_album(album['id'])
                            show_success_message("✅ Album deleted successfully!")
                            st.rerun()
    
    st.divider()

# ===========================
# MODIFIED CONCERT DISPLAY FUNCTION WITH EDIT
# ===========================

def display_concert_post(concert):
    """Display a concert post with edit functionality"""
    bands = concert.get('bands', 'Unknown')
    date = concert.get('date', '')
    venue = concert.get('venue', 'Unknown')
    city = concert.get('city', 'Unknown')
    info = concert.get('info', '')
    username = concert.get('username', 'Unknown')
    timestamp = concert.get('timestamp', '')
    
    # Check if current user can edit this concert
    can_edit = (st.session_state.current_user == "Admin" or 
                st.session_state.current_user == username)
    
    # Check if we're in edit mode for this concert
    is_editing = st.session_state.get(f'editing_concert_{concert["id"]}', False)
    
    # If editing mode is active, show edit form
    if is_editing and can_edit:
        with st.container():
            st.markdown("### ✏️ Edit Concert")
            with st.form(f"edit_concert_form_{concert['id']}"):
                new_bands = st.text_input("Bands", value=bands, 
                                         key=f"edit_bands_{concert['id']}")
                new_date = st.date_input("Date", value=datetime.strptime(date, '%Y-%m-%d').date(), 
                                        key=f"edit_date_{concert['id']}")
                new_venue = st.text_input("Venue", value=venue, 
                                         key=f"edit_venue_{concert['id']}")
                new_city = st.text_input("City", value=city, 
                                        key=f"edit_city_{concert['id']}")
                
                current_tags = concert.get('tags', [])
                tags_str = " ".join([f"#{tag}" for tag in current_tags])
                new_tags_input = st.text_input("Tags", value=tags_str, 
                                              placeholder="#tag1 #tag2 #tag3",
                                              key=f"edit_tags_concert_{concert['id']}")
                
                new_info = st.text_area("Additional info", value=info, 
                                       key=f"edit_info_{concert['id']}")
                
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.form_submit_button("💾 Save Changes", use_container_width=True):
                        new_tags = process_tags(new_tags_input)
                        if update_concert(concert['id'], new_bands, new_date, new_venue, 
                                        new_city, new_tags, new_info):
                            st.session_state[f'editing_concert_{concert["id"]}'] = False
                            show_success_message("✅ Concert updated successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Error updating concert")
                
                with col_cancel:
                    if st.form_submit_button("❌ Cancel", use_container_width=True):
                        st.session_state[f'editing_concert_{concert["id"]}'] = False
                        st.rerun()
            
            st.divider()
            return  # Skip normal display when editing
    
    # Normal display (when not editing)
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
    
    # Action buttons container
    col_actions = st.columns([1, 1])[0]  # Single column for actions
    
    with col_actions:
        if can_edit:
            # Show edit and delete buttons
            edit_col, delete_col = st.columns(2)
            
            with edit_col:
                if st.button("✏️ Edit", key=f"edit_concert_{concert['id']}", 
                           help="Edit concert", use_container_width=True):
                    st.session_state[f'editing_concert_{concert["id"]}'] = True
                    st.rerun()
            
            with delete_col:
                if st.button("🗑️ Delete", key=f"delete_concert_{concert['id']}", 
                           help="Delete concert", use_container_width=True):
                    delete_concert(concert['id'])
                    show_success_message("✅ Concert deleted successfully!")
                    st.rerun()
        else:
            # Admin can delete any concert
            if st.session_state.current_user == "Admin":
                if st.button("🗑️ Delete", key=f"delete_concert_{concert['id']}", 
                           help="Delete concert", use_container_width=True):
                    delete_concert(concert['id'])
                    show_success_message("✅ Concert deleted successfully!")
                    st.rerun()
    
    st.divider()

# ===========================
# MODIFIED ALBUM SUBMISSION HANDLER WITH DUPLICATE CHECK
# ===========================

def handle_album_submission(url, tags_input, is_manual=False, artist="", album_name="", cover_url=""):
    """Handle album form submission with duplicate check"""
    # Check for duplicate URL
    if check_duplicate_url(url):
        st.error("❌ This URL has already been posted. Please share a different album.")
        return False
    
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
# MODIFIED PROFILE PAGE SECTION
# ===========================

# In the main() function, locate the Profile page section (around line 1600)
# Replace the column structure for metrics to remove "Liked Gigs" counter:

# Change this part in the Profile page section:
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
    
    # Get liked albums
    liked_albums = [a for a in albums if st.session_state.current_user in a.get('likes', [])]
    
    # REMOVED: liked_concerts counter
    # liked_concerts = [c for c in concerts if st.session_state.current_user in c.get('likes', [])]
    
    # Show counts - MODIFIED: Only show 3 metrics now
    col1, col2, col3 = st.columns(3)  # Changed from 4 to 3 columns
    with col1:
        st.metric("🎵 My Albums", len(my_albums))
    with col2:
        st.metric("🎸 My Gigs", len(my_concerts))
    with col3:
        st.metric("❤️ Liked Albums", len(liked_albums))
    # REMOVED: "Liked Gigs" counter
    
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
    
    # REMOVED: "Liked Gigs" section
    # if liked_concerts:
    #     st.write("### 🤘 Liked Gigs")
    #     for concert in liked_concerts:
    #         display_concert_post(concert)
    
    if not my_albums and not my_concerts and not liked_albums:  # Removed: and not liked_concerts
        st.info("📭 You haven't shared or liked anything yet")