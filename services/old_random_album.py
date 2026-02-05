# File: metalwall_app/services/random_album.py
# ===========================
# RANDOM ALBUM DISCOVERY SERVICE
# ===========================

import streamlit as st
import random
from typing import Optional, Dict, Tuple
from database.operations import load_albums, save_discovery
from services.spotify_service import get_spotify_client, get_related_artists_spotify, get_random_album_by_artist
from services.lastfm_service import get_lastfm_client, get_related_artists_lastfm
from services.bandcamp_service import bandcamp_search

def get_random_album_from_wall() -> Optional[Dict]:
    """Get a random album from the wall"""
    try:
        albums = load_albums()
        if albums:
            album = random.choice(albums)
            return {
                'id': album.id,
                'username': album.username,
                'url': album.url,
                'artist': album.artist,
                'album_name': album.album_name,
                'cover_url': album.cover_url,
                'platform': album.platform,
                'tags': album.tags,
                'likes': album.likes,
                'timestamp': album.timestamp
            }
        return None
    except Exception as e:
        st.error(f"Error getting random album: {e}")
        return None

def discover_random_album(base_artist: Optional[str] = None, base_album_obj: Optional[Dict] = None) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Main random discovery function:
    1. Pick random album from the wall (or use provided)
    2. Find related artists
    3. Pick random related artist
    4. Get random album from that artist
    """
    try:
        # Get Spotify and Last.fm clients
        spotify_client = get_spotify_client()
        lastfm_client = get_lastfm_client()
        
        # Step 1: Get random album from wall (or use provided)
        if base_album_obj is None:
            random_album = get_random_album_from_wall()
            if not random_album:
                return None, "No albums found in the wall"
        else:
            random_album = base_album_obj
        
        base_artist_name = random_album.get('artist', '')
        base_album_name = random_album.get('album_name', '')
        
        # Clean artist name
        from services.spotify_service import clean_artist_name
        base_artist_name = clean_artist_name(base_artist_name)
        
        if not base_artist_name:
            return None, "Could not extract artist from album"
        
        # Step 2: Find related artists
        related_artists = []
        
        # Try Spotify first
        if spotify_client:
            related_artists = get_related_artists_spotify(spotify_client, base_artist_name)
        
        # Try Last.fm if Spotify didn't find any or isn't available
        if not related_artists and lastfm_client:
            related_artists = get_related_artists_lastfm(lastfm_client, base_artist_name)
        
        if not related_artists:
            return None, f"No related artists found for {base_artist_name}"
        
        # Step 3: Pick random related artist
        random_artist = random.choice(related_artists)
        
        # Step 4: Get random album from Spotify
        random_album_data = None
        if spotify_client:
            random_album_data = get_random_album_by_artist(spotify_client, random_artist)
        
        # Step 5: Try to find the album on Bandcamp
        bandcamp_result = None
        try:
            if random_album_data:
                bc_search_result = bandcamp_search(random_artist, random_album_data["album"])
                if bc_search_result:
                    bandcamp_result = {
                        "url": bc_search_result["url"],
                        "artist": bc_search_result["artist"],
                        "album": bc_search_result["album"]
                    }
        except Exception:
            pass
        
        # If Spotify fails, create a basic discovery
        if not random_album_data:
            random_album_data = {
                "artist": random_artist,
                "album": f"Random album by {random_artist}",
                "image": None,
                "url": f"https://www.last.fm/music/{random_artist.replace(' ', '+')}",
                "release_date": "Unknown",
                "total_tracks": 0,
                "genres": []
            }
        
        # Prepare discovery data
        discovery_data = {
            "origin": {
                "album": random_album,
                "artist": base_artist_name,
                "album_name": base_album_name
            },
            "discovery": random_album_data,
            "bandcamp": bandcamp_result,
            "description": f"Based on '{base_album_name}' by {base_artist_name} → Related artist: {random_artist}"
        }
        
        # Save discovery to database if user is logged in
        if st.session_state.get('current_user'):
            save_discovery(
                username=st.session_state.current_user,
                base_artist=base_artist_name,
                base_album=base_album_name,
                discovered_artist=random_album_data["artist"],
                discovered_album=random_album_data["album"],
                discovered_url=random_album_data["url"],
                cover_url=random_album_data.get("image")
            )
        
        return discovery_data, None
    except Exception as e:
        return None, f"Error during discovery: {str(e)}"