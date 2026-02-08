# File: metalwall_app/services/random_album.py
# ===========================
# RANDOM ALBUM DISCOVERY SERVICE
# ===========================

import streamlit as st
import random
import re
from typing import Optional, Dict, Tuple, List
from database.operations import load_albums, save_discovery
from services.spotify_service import get_spotify_client, get_related_artists_spotify, get_random_album_by_artist, search_artist_spotify
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

def normalize_artist_name(name: str) -> str:
    """
    Normalize artist name for comparison:
    - Lowercase
    - Remove special characters
    - Remove common prefixes/suffixes
    """
    if not name:
        return ""
    
    # Lowercase
    normalized = name.lower().strip()
    
    # Remove common prefixes that cause confusion
    prefixes_to_remove = ['the ', 'los ', 'las ', 'el ', 'la ', 'die ', 'der ', 'das ']
    for prefix in prefixes_to_remove:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
    
    # Remove special characters and extra spaces
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized

def is_similar_artist(artist1: str, artist2: str, threshold: float = 0.7) -> bool:
    """
    Check if two artist names are similar using fuzzy matching
    """
    from difflib import SequenceMatcher
    
    norm1 = normalize_artist_name(artist1)
    norm2 = normalize_artist_name(artist2)
    
    # Exact match after normalization
    if norm1 == norm2:
        return True
    
    # Check if one contains the other (for cases like "Sabbat" vs "Black Sabbath")
    if norm1 in norm2 or norm2 in norm1:
        # But be careful - "sabat" in "sabbath" might be too loose
        # Only accept if the shorter name is at least 4 chars
        min_len = min(len(norm1), len(norm2))
        if min_len >= 4:
            return True
    
    # Use sequence matcher for fuzzy matching
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    return similarity >= threshold

def get_artist_exact_match(spotify_client, artist_name: str) -> Optional[Dict]:
    """
    Search for an artist on Spotify and try to find the exact match
    Returns artist info if found, None otherwise
    """
    try:
        if not spotify_client:
            return None
            
        # Clean artist name for search
        search_name = artist_name.strip()
        
        # Try exact search
        results = spotify_client.search(q=f'artist:"{search_name}"', type='artist', limit=5)
        
        if not results or not results['artists']['items']:
            # Try without quotes for partial match
            results = spotify_client.search(q=search_name, type='artist', limit=10)
        
        artists = results['artists']['items']
        
        if not artists:
            return None
        
        # Try to find the best match
        normalized_target = normalize_artist_name(artist_name)
        
        for artist in artists:
            spotify_name = artist['name']
            normalized_spotify = normalize_artist_name(spotify_name)
            
            # Check for exact match after normalization
            if normalized_target == normalized_spotify:
                return {
                    'id': artist['id'],
                    'name': artist['name'],
                    'genres': artist.get('genres', []),
                    'popularity': artist.get('popularity', 0)
                }
        
        # If no exact match, check for similarity
        best_match = None
        best_similarity = 0
        
        for artist in artists:
            spotify_name = artist['name']
            similarity = SequenceMatcher(None, normalized_target, normalize_artist_name(spotify_name)).ratio()
            
            if similarity > best_similarity and similarity > 0.6:
                best_similarity = similarity
                best_match = {
                    'id': artist['id'],
                    'name': artist['name'],
                    'genres': artist.get('genres', []),
                    'popularity': artist.get('popularity', 0)
                }
        
        return best_match
        
    except Exception as e:
        print(f"Error getting exact artist match for {artist_name}: {e}")
        return None

def is_metal_album(lastfm_client, artist_name: str, album_name: str) -> Tuple[bool, List[str]]:
    """
    Check if an album is metal using Last.fm album tags
    Returns: (is_metal, tags_list)
    """
    if not lastfm_client:
        return False, []
    
    try:
        # First try to get album info
        album_info = search_lastfm_artist(lastfm_client, album_name, artist_name)
        
        if album_info and album_info.get('tags'):
            album_tags = album_info['tags']
            
            # Check album tags for metal keywords
            metal_keywords = [
                'metal', 'heavy metal', 'death metal', 'black metal', 'thrash metal',
                'power metal', 'folk metal', 'symphonic metal', 'doom metal',
                'progressive metal', 'melodic death metal', 'grindcore',
                'goregrind', 'deathcore', 'metalcore', 'hardcore', 'post-metal',
                'avant-garde metal', 'sludge metal', 'stoner metal', 'nu metal',
                'industrial metal', 'gothic metal', 'speed metal', 'hair metal',
                'glam metal', 'neoclassical metal', 'djent', 'math metal',
                'grunge', 'alternative metal', 'viking metal', 'pagan metal',
                'war metal', 'brutal death metal', 'technical death metal',
                'deathgrind', 'blackened death', 'blackdeath', 'doomdeath',
                'stoner rock', 'sludge', 'crossover thrash', 'black thrash',
                'thrash', 'death', 'black', 'doom', 'grind', 'core'
            ]
            
            # Check if any metal keyword is in the album tags
            for tag in album_tags:
                tag_lower = tag.lower()
                for keyword in metal_keywords:
                    if keyword in tag_lower or tag_lower in keyword:
                        return True, album_tags
            
        # If album not found or no tags, fall back to artist check
        return is_metal_artist(lastfm_client, artist_name), album_info.get('tags', []) if album_info else []
        
    except Exception as e:
        print(f"Error checking if album is metal: {e}")
        return False, []

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
                           'heavy', 'sludge', 'stoner', 'doom', 'black', 'power']
        
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
            
            # Try to get album tags too
            album_tags = []
            try:
                album_obj = lastfm_client.get_album(artist_name_corrected, album.get_name())
                album_top_tags = album_obj.get_top_tags(limit=5)
                album_tags = [tag.item.get_name().lower() for tag in album_top_tags]
            except:
                pass
            
            return {
                'artist': artist_name_corrected,
                'tags': tag_names,
                'album_tags': album_tags,
                'album': album.get_name()
            }
    
    except Exception as e:
        print(f"Error searching Last.fm for {artist_name} - {album_name}: {e}")
    
    return None

def validate_and_correct_metal_album(lastfm_client, spotify_album_data: Dict) -> Tuple[Optional[Dict], bool, List[str]]:
    """
    Validate if an album is metal and correct artist info using Last.fm
    Returns: (corrected_album_data, is_valid, tags)
    """
    if not lastfm_client:
        # If no Last.fm client, we can't validate, so accept it
        return spotify_album_data, True, []
    
    artist_name = spotify_album_data.get('artist', '')
    album_name = spotify_album_data.get('album', '')
    
    # Step 1: Check if the album itself is metal
    is_metal, album_tags = is_metal_album(lastfm_client, artist_name, album_name)
    if is_metal:
        return spotify_album_data, True, album_tags
    
    # Step 2: Search for the album on Last.fm to get correct artist info
    lastfm_info = search_lastfm_artist(lastfm_client, album_name, artist_name)
    
    if lastfm_info:
        corrected_artist = lastfm_info['artist']
        artist_tags = lastfm_info['tags']
        album_specific_tags = lastfm_info.get('album_tags', [])
        
        # Check if the corrected artist is metal
        for tag in artist_tags:
            if any(keyword in tag for keyword in ['metal', 'grindcore', 'gore', 'death', 'black', 'thrash', 'power', 'heavy', 'doom']):
                # Update the album data with corrected artist
                spotify_album_data['artist'] = corrected_artist
                # Combine artist and album tags
                all_tags = list(set(artist_tags + album_specific_tags))
                return spotify_album_data, True, all_tags
        
        # Also check album-specific tags
        for tag in album_specific_tags:
            if any(keyword in tag for keyword in ['metal', 'grindcore', 'gore', 'death', 'black', 'thrash', 'power', 'heavy', 'doom']):
                spotify_album_data['artist'] = corrected_artist
                all_tags = list(set(artist_tags + album_specific_tags))
                return spotify_album_data, True, all_tags
    
    # Step 3: Try alternative approach - search for similar artists to check if any are metal
    try:
        artist = lastfm_client.get_artist(artist_name)
        similar = artist.get_similar(limit=5)
        
        for similar_artist in similar:
            similar_name = similar_artist.item.get_name()
            if is_metal_artist(lastfm_client, similar_name):
                # If similar artist is metal, this might be metal too
                return spotify_album_data, True, []
    
    except Exception:
        pass
    
    return None, False, []

def verify_artist_identity(spotify_client, artist_name: str, spotify_artist_data: Dict) -> bool:
    """
    Verify that the Spotify artist data matches the intended artist
    """
    if not spotify_client or not spotify_artist_data:
        return False
    
    spotify_artist_name = spotify_artist_data.get('artist', '')
    
    # Check if names are similar
    if is_similar_artist(artist_name, spotify_artist_name):
        return True
    
    # Additional check: if the Spotify data has genres, check if they're metal-related
    genres = spotify_artist_data.get('genres', [])
    metal_genres = ['metal', 'heavy metal', 'death metal', 'black metal', 'thrash metal',
                   'power metal', 'doom metal', 'folk metal', 'progressive metal',
                   'grindcore', 'metalcore', 'deathcore', 'hardcore']
    
    for genre in genres:
        if any(metal_genre in genre.lower() for metal_genre in metal_genres):
            # The genre suggests it's metal, so it's likely the right artist
            return True
    
    return False

def discover_random_album(base_artist: Optional[str] = None, base_album_obj: Optional[Dict] = None, 
                         max_attempts: int = 10) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Main random discovery function with robust metal validation:
    1. Pick random album from the wall (or use provided)
    2. Find related artists
    3. Pick random related artist
    4. Get exact artist match from Spotify
    5. Get random album from that artist
    6. Validate it's a metal album with multiple checks
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
        related_artists_info = []
        
        # Try Spotify first
        if spotify_client:
            related_artists = get_related_artists_spotify(spotify_client, base_artist_name)
            # Get full artist info for each related artist
            for artist_name in related_artists:
                artist_info = get_artist_exact_match(spotify_client, artist_name)
                if artist_info:
                    related_artists_info.append(artist_info)
        
        # Try Last.fm if Spotify didn't find any or isn't available
        if not related_artists_info and lastfm_client:
            related_artists = get_related_artists_lastfm(lastfm_client, base_artist_name)
            for artist_name in related_artists:
                related_artists_info.append({
                    'name': artist_name,
                    'genres': [],
                    'popularity': 0
                })
        
        if not related_artists_info:
            return None, f"No related artists found for {base_artist_name}"
        
        # Try multiple attempts to find a valid metal album
        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            
            # Step 3: Pick random related artist
            random_artist_info = random.choice(related_artists_info)
            random_artist_name = random_artist_info['name']
            
            # Step 4: Get exact artist match from Spotify
            exact_artist = None
            if spotify_client:
                exact_artist = get_artist_exact_match(spotify_client, random_artist_name)
            
            if not exact_artist:
                # Skip if we can't find the exact artist
                continue
            
            # Step 5: Get random album from that artist
            random_album_data = None
            if spotify_client:
                random_album_data = get_random_album_by_artist(spotify_client, exact_artist['name'], exact_artist['id'])
            
            # If Spotify fails, create a basic discovery
            if not random_album_data:
                continue  # Skip and try another artist
            
            # Step 6: Verify artist identity
            if not verify_artist_identity(spotify_client, random_artist_name, random_album_data):
                # Artist doesn't match, try another
                continue
            
            # Step 7: Validate it's a metal album
            if lastfm_client:
                validated_album, is_valid, album_tags = validate_and_correct_metal_album(
                    lastfm_client, random_album_data
                )
                
                if is_valid and validated_album:
                    random_album_data = validated_album
                    
                    # Extract tags from the discovered album
                    discovery_tags = []
                    
                    # Use the album tags from Last.fm validation
                    if album_tags:
                        for tag in album_tags[:5]:  # Limit to 5 tags
                            # Clean tag and convert to tag format
                            clean_tag = tag.lower().replace(' ', '')
                            if clean_tag not in discovery_tags:
                                discovery_tags.append(clean_tag)
                    
                    # Also get genres from Spotify and convert to tags
                    if random_album_data.get('genres'):
                        for genre in random_album_data['genres'][:3]:  # Limit to 3 genres
                            tag = genre.lower().replace(' ', '')
                            if tag not in discovery_tags and len(discovery_tags) < 5:
                                discovery_tags.append(tag)
                    
                    # Also try to get tags from the artist's Last.fm page
                    try:
                        if lastfm_client:
                            artist = lastfm_client.get_artist(random_album_data["artist"])
                            tags = artist.get_top_tags(limit=5)
                            
                            for tag in tags:
                                tag_name = tag.item.get_name().lower().replace(' ', '')
                                # Filter for metal-related tags
                                if any(metal_keyword in tag_name for metal_keyword in 
                                      ['metal', 'death', 'thrash', 'doom', 'grind', 'black', 'core']):
                                    if tag_name not in discovery_tags and len(discovery_tags) < 5:
                                        discovery_tags.append(tag_name)
                    except Exception:
                        pass
                    
                    # Add random discovery tag
                    if 'randomdiscovery' not in discovery_tags:
                        discovery_tags.append('randomdiscovery')
                    
                    # Step 8: Try to find the album on Bandcamp
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
                        "description": f"Based on '{base_album_name}' by {base_artist_name} → Related artist: {random_artist_name}",
                        "validation": "✅ Validated as metal",
                        "tags": discovery_tags
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
                # No Last.fm client, can't validate - use Spotify genres as fallback
                discovery_tags = []
                if random_album_data.get('genres'):
                    for genre in random_album_data['genres'][:3]:
                        tag = genre.lower().replace(' ', '')
                        if tag not in discovery_tags:
                            discovery_tags.append(tag)
                
                # Check if any genre suggests metal
                metal_genres = ['metal', 'heavy', 'death', 'black', 'thrash', 'doom', 'grind', 'core']
                is_metal_by_genre = any(
                    any(metal_genre in genre.lower() for metal_genre in metal_genres)
                    for genre in random_album_data.get('genres', [])
                )
                
                if not is_metal_by_genre:
                    continue  # Skip non-metal albums
                
                discovery_tags.append('randomdiscovery')
                
                bandcamp_result = None
                try:
                    if random_album_data:
                        bc_search_result = bandcamp_search(random_artist_name, random_album_data["album"])
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
                    "description": f"Based on '{base_album_name}' by {base_artist_name} → Related artist: {random_artist_name}",
                    "validation": "⚠️ Could not validate (Last.fm not available)",
                    "tags": discovery_tags
                }
                
                return discovery_data, None
        
        # If we get here, we couldn't find a valid metal album after max attempts
        return None, f"Could not find a valid metal album after {max_attempts} attempts. Try again!"
        
    except Exception as e:
        return None, f"Error during discovery: {str(e)}"