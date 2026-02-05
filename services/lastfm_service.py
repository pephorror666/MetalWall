# File: metalwall_app/services/lastfm_service.py
# ===========================
# LAST.FM API SERVICE
# ===========================

import streamlit as st
import pylast
from typing import Optional, List

@st.cache_resource
def get_lastfm_client():
    """Initialize Last.fm client with credentials from secrets"""
    try:
        api_key = st.secrets.get("LASTFM_API_KEY", "")
        api_secret = st.secrets.get("LASTFM_API_SECRET", "")
        
        if not api_key or not api_secret:
            st.warning("⚠️ Last.fm API credentials not found. Some features may be limited.")
            return None
        
        return pylast.LastFMNetwork(api_key=api_key, api_secret=api_secret)
    except Exception as e:
        st.error(f"❌ Error initializing Last.fm client: {e}")
        return None

def get_related_artists_lastfm(lastfm_client, artist_name: str) -> List[str]:
    """Find related artists using Last.fm API"""
    from services.spotify_service import clean_artist_name
    artist_name = clean_artist_name(artist_name)
    
    try:
        if not lastfm_client:
            return []
        
        artist = lastfm_client.get_artist(artist_name)
        similar = artist.get_similar(limit=15)
        return [a.item.get_name() for a in similar]
    except Exception as e:
        print(f"Error getting related artists from Last.fm: {e}")
        return []