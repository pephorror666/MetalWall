# File: metalwall_app/services/random_album.py
# ===========================
# RANDOM ALBUM DISCOVERY SERVICE
# ===========================

import streamlit as st
import random
import time
from typing import Optional, Dict, Tuple, List
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

def is_metal_artist(lastfm_client, artist_name: str) -> bool:
    """
    Check if an artist is a metal artist using Last.fm tags
    Returns True if artist has metal-related tags
    """
    if not lastfm_client:
        return False
    
    try:
        # Get artist info from Last.fm
        artist = lastfm_client.get_artist(artist_name)
        
        # Get top tags for the artist
        tags = artist.get_top_tags(limit=10)
        
        # Convert tags to lowercase for comparison
        tag_names = [tag.item.get_name().lower() for tag in tags]
        
        # Metal-related keywords to check for
        metal_keywords = [
            'metal', 'heavy metal', 'death metal', 'black metal', 'thrash metal',
            'power metal', 'folk metal', 'symphonic metal', 'doom metal',
            'progressive metal', 'melodic death metal', 'grindcore',
            'goregrind', 'deathcore', 'metalcore', 'hardcore', 'post-metal',
            'avant-garde metal', 'sludge metal', 'stoner metal', 'nu metal',
            'industrial metal', 'gothic metal', 'speed metal', 'hair metal',
            'glam metal', 'neoclassical metal', 'djent', 'math metal',
            'grunge', 'alternative metal', 'folk metal', 'viking metal',
            'pagan metal', 'war metal', 'brutal death metal', 'technical death metal'
        ]
        
        # Also check for partial matches (e.g., "death" in "death metal")
        partial_keywords = ['metal', 'grindcore', 'gore', 'death', 'thrash', 
                           'heavy', 'sludge', 'stoner']
        
        # Check if any metal keyword is in the tags
        for tag in tag_names:
            # Check for exact or partial matches
            for keyword in metal_keywords:
                if keyword in tag or tag in keyword:
                    return True
            
            # Check for partial keyword matches
            for keyword in partial_keywords:
                if keyword in tag:
                    return True
        
        return False
        
    except Exception as e:
        print(f"Error checking if {artist_name} is metal: {e}")
        return False

def search_lastfm_artist(lastfm_client, album_name: str, artist_name: str) -> Optional[Dict]:
    """
    Search for an album on Last.fm and get the correct artist info
    Returns: dict with artist name and tags if found
    """
    if not lastfm_client:
        return None
    
    try:
        # Search for the album
        search_results = lastfm_client.search_for_album(album_name, artist_name)
        
        if not search_results or len(search_results) == 0:
            # Try searching just by album name
            search_results = lastfm_client.search_for_album(album_name)
        
        if search_results and len(search_results) > 0:
            # Get the first result
            album = search_results[0]
            
            # Get the artist
            artist = album.get_artist()
            artist_name_corrected = artist.get_name()
            
            # Get artist tags
            tags = artist.get_top_tags(limit=10)
            tag_names = [tag.item.get_name().lower() for tag in tags]
            
            return {
                'artist': artist_name_corrected,
                'tags': tag_names,
                'album': album.get_name()
            }
    
    except Exception as e:
        print(f"Error searching Last.fm for {artist_name} - {album_name}: {e}")
    
    return None

def validate_and_correct_metal_album(lastfm_client, spotify_album_data: Dict) -> Tuple[Optional[Dict], bool]:
    """
    Validate if an album is metal and correct artist info using Last.fm
    Returns: (corrected_album_data, is_valid)
    """
    if not lastfm_client:
        # If no Last.fm client, we can't validate, so accept it
        return spotify_album_data, True
    
    artist_name = spotify_album_data.get('artist', '')
    album_name = spotify_album_data.get('album', '')
    
    # Step 1: Check if the artist is already metal
    if is_metal_artist(lastfm_client, artist_name):
        return spotify_album_data, True
    
    # Step 2: Search for the album on Last.fm to get correct artist info
    lastfm_info = search_lastfm_artist(lastfm_client, album_name, artist_name)
    
    if lastfm_info:
        corrected_artist = lastfm_info['artist']
        tags = lastfm_info['tags']
        
        # Check if the corrected artist is metal
        for tag in tags:
            if any(keyword in tag for keyword in ['metal', 'grindcore', 'gore', 'death', 'black', 'thrash', 'power', 'heavy']):
                # Update the album data with corrected artist
                spotify_album_data['artist'] = corrected_artist
                return spotify_album_data, True
    
    # Step 3: Try alternative approach - search for similar artists to check if any are metal
    try:
        artist = lastfm_client.get_artist(artist_name)
        similar = artist.get_similar(limit=5)
        
        for similar_artist in similar:
            similar_name = similar_artist.item.get_name()
            if is_metal_artist(lastfm_client, similar_name):
                # If similar artist is metal, this might be metal too
                return spotify_album_data, True
    
    except Exception:
        pass
    
    return None, False

def discover_random_album(base_artist: Optional[str] = None, base_album_obj: Optional[Dict] = None, 
                         max_attempts: int = 5) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Main random discovery function with metal validation:
    1. Pick random album from the wall (or use provided)
    2. Find related artists
    3. Pick random related artist
    4. Get random album from that artist
    5. Validate it's a metal album
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
        
        # Try multiple attempts to find a valid metal album
        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            
            # Step 3: Pick random related artist
            random_artist = random.choice(related_artists)
            
            # Step 4: Get random album from Spotify
            random_album_data = None
            if spotify_client:
                random_album_data = get_random_album_by_artist(spotify_client, random_artist)
            
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
            
            # Step 5: Validate it's a metal album
            if lastfm_client:
                validated_album, is_valid = validate_and_correct_metal_album(
                    lastfm_client, random_album_data
                )
                
                if is_valid and validated_album:
                    random_album_data = validated_album
                    
                    # NEW: Extract tags from the discovered album
                    discovery_tags = []
                    
                    # Get genres from Spotify and convert to tags
                    if random_album_data.get('genres'):
                        for genre in random_album_data['genres'][:3]:  # Limit to 3 genres
                            # Clean genre and convert to tag format
                            tag = genre.lower().replace(' ', '')
                            if tag not in discovery_tags:
                                discovery_tags.append(tag)
                    
                    # Also try to get tags from Last.fm
                    try:
                        if lastfm_client:
                            # Get artist info from Last.fm for more specific metal tags
                            artist = lastfm_client.get_artist(random_album_data["artist"])
                            tags = artist.get_top_tags(limit=5)
                            
                            for tag in tags:
                                tag_name = tag.item.get_name().lower().replace(' ', '')
                                # Filter for metal-related tags
                                if any(metal_keyword in tag_name for metal_keyword in 
                                      ['metal', 'death', 'thrash', 'doom', 'grind']):
                                    if tag_name not in discovery_tags and len(discovery_tags) < 5:
                                        discovery_tags.append(tag_name)
                    except Exception:
                        pass
                    
                    # Add random discovery tag
                    discovery_tags.append('randomdiscovery')
                    
                    # Step 6: Try to find the album on Bandcamp
                    bandcamp_result = None
                    try:
                        bc_search_result = bandcamp_search(
                            random_album_data["artist"], 
                            random_album_data["album"]
                        )
                        if bc_search_result:
                            bandcamp_result = {
                                "url": bc_search_result["url"],
                                "artist": bc_search_result["artist"],
                                "album": bc_search_result["album"]
                            }
                    except Exception:
                        pass
                    
                    # Prepare discovery data with tags
                    discovery_data = {
                        "origin": {
                            "album": random_album,
                            "artist": base_artist_name,
                            "album_name": base_album_name
                        },
                        "discovery": random_album_data,
                        "bandcamp": bandcamp_result,
                        "description": f"Based on '{base_album_name}' by {base_artist_name} → Related artist: {random_artist}",
                        "validation": "✅ Validated as metal",
                        "tags": discovery_tags  # NEW: Store tags for the discovered album
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
                else:
                    # Not a metal album, try again
                    continue
            else:
                # No Last.fm client, can't validate - just return what we have
                # NEW: Still try to extract tags from Spotify genres
                discovery_tags = []
                if random_album_data.get('genres'):
                    for genre in random_album_data['genres'][:3]:
                        tag = genre.lower().replace(' ', '')
                        if tag not in discovery_tags:
                            discovery_tags.append(tag)
                discovery_tags.append('randomdiscovery')
                
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
                
                discovery_data = {
                    "origin": {
                        "album": random_album,
                        "artist": base_artist_name,
                        "album_name": base_album_name
                    },
                    "discovery": random_album_data,
                    "bandcamp": bandcamp_result,
                    "description": f"Based on '{base_album_name}' by {base_artist_name} → Related artist: {random_artist}",
                    "validation": "⚠️ Could not validate (Last.fm not available)",
                    "tags": discovery_tags  # NEW: Store tags
                }
                
                return discovery_data, None
        
        # If we get here, we couldn't find a valid metal album after max attempts
        return None, f"Could not find a valid metal album after {max_attempts} attempts. Try again!"
        
    except Exception as e:
        return None, f"Error during discovery: {str(e)}"