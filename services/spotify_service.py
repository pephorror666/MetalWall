# File: metalwall_app/services/spotify_service.py
# ===========================
# SPOTIFY API SERVICE
# ===========================

import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Optional, Dict, List
import random

@st.cache_resource
def get_spotify_client():
    """Initialize Spotify client with credentials from secrets"""
    try:
        client_id = st.secrets.get("SPOTIFY_CLIENT_ID", "")
        client_secret = st.secrets.get("SPOTIFY_CLIENT_SECRET", "")
        
        if not client_id or not client_secret:
            st.warning("⚠️ Spotify API credentials not found. Random Album feature will use limited functionality.")
            return None
        
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        return spotipy.Spotify(auth_manager=auth_manager)
    except Exception as e:
        st.error(f"❌ Error initializing Spotify client: {e}")
        return None

def get_related_artists_spotify(spotify_client, artist_name: str) -> List[str]:
    """Find related artists using Spotify API"""
    artist_name = clean_artist_name(artist_name)
    
    try:
        if not spotify_client:
            return []
        
        results = spotify_client.search(q=f"artist:{artist_name}", type="artist", limit=1)
        artists = results.get("artists", {}).get("items", [])
        
        if not artists:
            return []
        
        artist_id = artists[0]["id"]
        related_artists = spotify_client.artist_related_artists(artist_id)
        
        return [artist["name"] for artist in related_artists.get("artists", [])[:10]]
    except Exception as e:
        print(f"Error getting related artists from Spotify: {e}")
        return []

def get_random_album_by_artist(spotify_client, artist_name: str) -> Optional[Dict]:
    """Get a random album by an artist from Spotify"""
    artist_name = clean_artist_name(artist_name)
    
    try:
        if not spotify_client:
            return None
        
        results = spotify_client.search(q=f"artist:{artist_name}", type="album", limit=20)
        albums = results.get("albums", {}).get("items", [])
        
        if not albums:
            return None
        
        # Pick random album
        random_album = random.choice(albums)
        
        # Get full album details
        album_id = random_album["id"]
        album_details = spotify_client.album(album_id)
        
        return {
            "artist": artist_name,
            "album": album_details["name"],
            "image": album_details["images"][0]["url"] if album_details.get("images") else None,
            "url": album_details["external_urls"]["spotify"],
            "release_date": album_details.get("release_date", "Unknown"),
            "total_tracks": album_details.get("total_tracks", 0),
            "genres": album_details.get("genres", [])
        }
    except Exception as e:
        print(f"Error getting random album from Spotify: {e}")
        return None

def clean_artist_name(artist_name: str) -> str:
    """Clean artist name by removing platform-specific suffixes"""
    suffixes = [" | Spotify", "Album by ", "EP by ", "Single by "]
    for suffix in suffixes:
        artist_name = artist_name.replace(suffix, "")
    return artist_name.strip()