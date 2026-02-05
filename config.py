# File: metalwall_app/config.py
# ===========================
# CONFIGURATION AND CONSTANTS
# ===========================

import streamlit as st

# Streamlit configuration
PAGE_CONFIG = {
    "page_title": "The Metal Wall",
    "page_icon": "🤘",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Database configuration
DB_PATH = "metal_music.db"

# API service names
SPOTIFY = "spotify"
LASTFM = "lastfm"
BANDCAMP = "bandcamp"

# Platform mappings
PLATFORMS = {
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

# Default values
DEFAULT_SORT_OPTION = "Timeline"
SORT_OPTIONS = ["Timeline", "Votes"]

# Navigation options
ADMIN_NAV_OPTIONS = ["💿 Records", "🎸 Gigs", "🎲 Random Album", "👤 Profile", "🔧 Admin Tools"]
USER_NAV_OPTIONS = ["💿 Records", "🎸 Gigs", "🎲 Random Album", "👤 Profile"]

def init_session_state():
    """Initialize all session state variables"""
    default_state = {
        'current_user': None,
        'show_album_form': False,
        'show_concert_form': False,
        'active_filter_feed': None,
        'active_filter_concerts': None,
        'show_manual_input': False,
        'remember_me': False,
        'username_input': "",
        'password_input': "",
        'form_submitted': False,
        'success_message': "",
        'sort_option': DEFAULT_SORT_OPTION,
        'random_discovery_data': None,
        'show_discovery_history': False,
    }
    
    for key, value in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = value