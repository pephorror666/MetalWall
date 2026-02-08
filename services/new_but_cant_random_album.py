# File: metalwall_app/services/random_album.py
# ===========================
# RANDOM ALBUM DISCOVERY SERVICE
# ===========================

import streamlit as st
import random
import time
import difflib
import re
from typing import Optional, Dict, Tuple, List
from database.operations import load_albums, save_discovery
from services.spotify_service import get_spotify_client, get_related_artists_spotify, get_random_album_by_artist
from services.lastfm_service import get_lastfm_client, get_related_artists_lastfm
from services.bandcamp_service import bandcamp_search

# Strict metal validation keywords
METAL_KEYWORDS = ['metal', 'grind', 'metalcore', 'heavy', 'death', 'black', 'thrash', 
                  'doom', 'power', 'sludge', 'stoner', 'progressive metal', 'deathcore']

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

def is_metal_artist(lastfm_client, artist_name: str) -> Tuple[bool, List[str]]:
    """
    Strict check if an artist is a metal artist using Last.fm tags
    Returns: (is_metal, list_of_tags)
    """
    if not lastfm_client:
        return False, []
    
    try:
        # Get artist info from Last.fm
        artist = lastfm_client.get_artist(artist_name)
        
        # Get top tags for the artist
        tags = artist.get_top_tags(limit=15)
        
        # Convert tags to lowercase for comparison
        tag_names = [tag.item.get_name().lower() for tag in tags]
        
        # STRICT metal validation - check for specific metal keywords
        for tag in tag_names:
            for keyword in METAL_KEYWORDS:
                if keyword in tag:
                    return True, tag_names
        
        return False, tag_names
        
    except Exception as e:
        print(f"Error checking if {artist_name} is metal: {e}")
        return False, []

def search_lastfm_artist(lastfm_client, album_name: str, artist_name: str) -> Optional[Dict]:
    """
    Search for an album on Last.fm and get the correct artist info
    Returns: dict with artist name, tags, and album info if found
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
            tags = artist.get_top_tags(limit=15)
            tag_names = [tag.item.get_name().lower() for tag in tags]
            
            return {
                'artist': artist_name_corrected,
                'tags': tag_names,
                'album': album.get_name(),
                'mbid': album.get_mbid() if hasattr(album, 'get_mbid') else None
            }
    
    except Exception as e:
        print(f"Error searching Last.fm for {artist_name} - {album_name}: {e}")
    
    return None

def format_tags_for_posting(tags: List[str]) -> str:
    """
    Format Last.fm tags for posting to the wall
    Returns: string of tags (e.g., "#deathmetal #blackmetal #thrash")
    """
    if not tags:
        return "#randomdiscovery"
    
    # Clean and format tags
    cleaned_tags = []
    for tag in tags[:3]:  # Limit to 3 tags
        # Remove special characters and spaces, convert to lowercase
        cleaned = re.sub(r'[^\w\s]', '', tag)
        cleaned = cleaned.lower().replace(' ', '')
        
        # Ensure it's a valid tag (at least 2 characters)
        if len(cleaned) >= 2:
            # Capitalize first letter for better readability
            cleaned = cleaned.capitalize() if cleaned.islower() else cleaned
            cleaned_tags.append(f"#{cleaned}")
    
    # If no valid tags found, use default
    if not cleaned_tags:
        return "#randomdiscovery"
    
    # Return as space-separated string
    return ' '.join(cleaned_tags)

def validate_and_correct_metal_album(lastfm_client, spotify_album_data: Dict, original_artist: str = None) -> Tuple[Optional[Dict], bool, str, List[str]]:
    """
    STRICT validation if an album is metal with double checking
    Returns: (corrected_album_data, is_valid, validation_message, lastfm_tags)
    """
    if not lastfm_client:
        # If no Last.fm client, we can't validate properly
        return spotify_album_data, True, "Warning: No Last.fm validation available", []
    
    artist_name = spotify_album_data.get('artist', '')
    album_name = spotify_album_data.get('album', '')
    
    # Step 1: STRICT check if the Spotify artist is metal on Last.fm
    is_metal, spotify_artist_tags = is_metal_artist(lastfm_client, artist_name)
    
    if is_metal:
        # DOUBLE CHECK: Verify artist name match is close enough
        if original_artist:
            similarity = difflib.SequenceMatcher(None, artist_name.lower(), original_artist.lower()).ratio()
            if similarity < 0.7:  # 70% similarity threshold
                return None, False, f"Artist name mismatch: '{artist_name}' vs '{original_artist}'", []
        
        # Additional verification: check if metal tags are prominent
        metal_tag_count = sum(1 for tag in spotify_artist_tags 
                            if any(keyword in tag for keyword in METAL_KEYWORDS))
        
        if metal_tag_count >= 1:  # At least one strong metal tag
            # Extract metal tags for tagging
            metal_tags = [tag for tag in spotify_artist_tags 
                         if any(keyword in tag for keyword in METAL_KEYWORDS)]
            
            # Add tags to album data
            spotify_album_data['lastfm_tags'] = spotify_artist_tags
            spotify_album_data['metal_tags'] = metal_tags
            # Add formatted tags for easy access
            spotify_album_data['formatted_tags'] = format_tags_for_posting(metal_tags)
            
            return spotify_album_data, True, f"✅ Validated as metal ({metal_tag_count} metal tags found)", spotify_artist_tags
        else:
            return None, False, "Not enough metal tags found", []
    
    # Step 2: Search for the album on Last.fm to get correct artist info
    lastfm_info = search_lastfm_artist(lastfm_client, album_name, artist_name)
    
    if lastfm_info:
        corrected_artist = lastfm_info['artist']
        tags = lastfm_info['tags']
        
        # Step 3: DOUBLE CHECK the corrected artist
        is_corrected_metal, corrected_tags = is_metal_artist(lastfm_client, corrected_artist)
        
        if is_corrected_metal:
            # Verify artist name similarity
            if original_artist:
                similarity = difflib.SequenceMatcher(None, corrected_artist.lower(), original_artist.lower()).ratio()
                if similarity < 0.7:
                    return None, False, f"Corrected artist name mismatch: '{corrected_artist}' vs '{original_artist}'", []
            
            # Update the album data with corrected artist and tags
            spotify_album_data['artist'] = corrected_artist
            spotify_album_data['lastfm_tags'] = corrected_tags
            
            # Extract metal tags
            metal_tags = [tag for tag in corrected_tags 
                         if any(keyword in tag for keyword in METAL_KEYWORDS)]
            spotify_album_data['metal_tags'] = metal_tags
            spotify_album_data['formatted_tags'] = format_tags_for_posting(metal_tags)
            
            metal_tag_count = sum(1 for tag in corrected_tags 
                                if any(keyword in tag for keyword in METAL_KEYWORDS))
            
            return spotify_album_data, True, f"✅ Corrected and validated as metal ({metal_tag_count} metal tags)", corrected_tags
    
    # Step 4: Check for similar artists that are metal
    try:
        artist = lastfm_client.get_artist(artist_name)
        similar = artist.get_similar(limit=5)
        
        for similar_artist in similar:
            similar_name = similar_artist.item.get_name()
            is_similar_metal, similar_tags = is_metal_artist(lastfm_client, similar_name)
            
            if is_similar_metal:
                # Check if original artist name matches similar metal artist
                similarity = difflib.SequenceMatcher(None, artist_name.lower(), similar_name.lower()).ratio()
                if similarity > 0.8:  # 80% similarity
                    # Add tags to album data
                    spotify_album_data['lastfm_tags'] = similar_tags
                    
                    # Extract metal tags
                    metal_tags = [tag for tag in similar_tags 
                                 if any(keyword in tag for keyword in METAL_KEYWORDS)]
                    spotify_album_data['metal_tags'] = metal_tags
                    spotify_album_data['formatted_tags'] = format_tags_for_posting(metal_tags)
                    
                    metal_tag_count = sum(1 for tag in similar_tags 
                                        if any(keyword in tag for keyword in METAL_KEYWORDS))
                    return spotify_album_data, True, f"✅ Validated via similar artist ({metal_tag_count} metal tags)", similar_tags
    
    except Exception:
        pass
    
    return None, False, "Not a validated metal artist", []

def get_metal_related_artists(lastfm_client, base_artist: str, max_results: int = 10) -> List[str]:
    """
    Get related artists and filter to only metal ones
    """
    if not lastfm_client:
        return []
    
    try:
        # Get all related artists
        artist = lastfm_client.get_artist(base_artist)
        similar = artist.get_similar(limit=20)
        
        # Filter to only metal artists
        metal_related = []
        for similar_artist in similar:
            artist_name = similar_artist.item.get_name()
            is_metal, tags = is_metal_artist(lastfm_client, artist_name)
            
            if is_metal:
                metal_related.append(artist_name)
                
                if len(metal_related) >= max_results:
                    break
        
        return metal_related
        
    except Exception as e:
        print(f"Error getting metal related artists: {e}")
        return []

def discover_random_album(base_artist: Optional[str] = None, base_album_obj: Optional[Dict] = None, 
                         max_attempts: int = 10) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Main random discovery function with STRICT metal validation and double checking
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
        base_artist_name_clean = clean_artist_name(base_artist_name)
        
        if not base_artist_name_clean:
            return None, "Could not extract artist from album"
        
        # Step 2: DOUBLE VALIDATION - Check if base artist itself is metal
        if lastfm_client:
            is_base_metal, base_tags = is_metal_artist(lastfm_client, base_artist_name_clean)
            if not is_base_metal:
                st.warning(f"Warning: Base artist '{base_artist_name_clean}' may not be metal. Continuing anyway.")
        
        # Step 3: Find metal-related artists only
        metal_related_artists = []
        
        # Try to get metal-only related artists from Last.fm
        if lastfm_client:
            metal_related_artists = get_metal_related_artists(lastfm_client, base_artist_name_clean)
        
        # Fallback to Spotify if no metal artists found
        if not metal_related_artists and spotify_client:
            all_related = get_related_artists_spotify(spotify_client, base_artist_name_clean)
            # Filter Spotify results through Last.fm validation
            for artist in all_related[:10]:  # Check first 10
                if lastfm_client:
                    is_metal, _ = is_metal_artist(lastfm_client, artist)
                    if is_metal:
                        metal_related_artists.append(artist)
        
        if not metal_related_artists:
            return None, f"No metal-related artists found for {base_artist_name_clean}"
        
        # Try multiple attempts to find a valid metal album
        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            
            # Step 4: Pick random metal-related artist
            random_metal_artist = random.choice(metal_related_artists)
            
            # Step 5: Get random album from Spotify
            random_album_data = None
            if spotify_client:
                random_album_data = get_random_album_by_artist(spotify_client, random_metal_artist)
            
            # If Spotify fails, skip this attempt
            if not random_album_data:
                continue
            
            # Step 6: STRICT validation with double checking
            if lastfm_client:
                validated_album, is_valid, validation_msg, lastfm_tags = validate_and_correct_metal_album(
                    lastfm_client, random_album_data, random_metal_artist
                )
                
                if is_valid and validated_album:
                    # Step 7: FINAL VERIFICATION - Double check artist name match
                    final_artist = validated_album.get("artist", "")
                    similarity = difflib.SequenceMatcher(None, 
                                                        final_artist.lower(), 
                                                        random_metal_artist.lower()).ratio()
                    
                    if similarity < 0.6:  # Strict final check
                        continue  # Try another attempt
                    
                    # Step 8: Try to find the album on Bandcamp
                    bandcamp_result = None
                    try:
                        bc_search_result = bandcamp_search(
                            validated_album["artist"], 
                            validated_album["album"]
                        )
                        if bc_search_result:
                            bandcamp_result = {
                                "url": bc_search_result["url"],
                                "artist": bc_search_result["artist"],
                                "album": bc_search_result["album"]
                            }
                    except Exception:
                        pass
                    
                    # Get formatted tags for posting
                    formatted_tags = validated_album.get('formatted_tags', '#randomdiscovery')
                    
                    # Prepare discovery data with validation info
                    discovery_data = {
                        "origin": {
                            "album": random_album,
                            "artist": base_artist_name,
                            "album_name": base_album_name
                        },
                        "discovery": {
                            **validated_album,
                            "validated_artist": final_artist,
                            "original_searched_artist": random_metal_artist,
                            # Ensure tags are included
                            "lastfm_tags": validated_album.get('lastfm_tags', []),
                            "metal_tags": validated_album.get('metal_tags', []),
                            "formatted_tags": formatted_tags
                        },
                        "bandcamp": bandcamp_result,
                        "description": f"Based on '{base_album_name}' by {base_artist_name} → Metal-related artist: {random_metal_artist}",
                        "validation": validation_msg,
                        "similarity_score": f"{similarity:.1%} artist match",
                        # Also include tags at the top level for easy access
                        "lastfm_tags": lastfm_tags,
                        "formatted_tags": formatted_tags
                    }
                    
                    # Save discovery to database if user is logged in
                    if st.session_state.get('current_user'):
                        # Try to save with tags, fallback to without tags if function doesn't support it
                        try:
                            save_discovery(
                                username=st.session_state.current_user,
                                base_artist=base_artist_name,
                                base_album=base_album_name,
                                discovered_artist=validated_album["artist"],
                                discovered_album=validated_album["album"],
                                discovered_url=validated_album["url"],
                                cover_url=validated_album.get("image"),
                                tags=formatted_tags
                            )
                        except TypeError:
                            # If save_discovery doesn't accept tags parameter, call without it
                            save_discovery(
                                username=st.session_state.current_user,
                                base_artist=base_artist_name,
                                base_album=base_album_name,
                                discovered_artist=validated_album["artist"],
                                discovered_album=validated_album["album"],
                                discovered_url=validated_album["url"],
                                cover_url=validated_album.get("image")
                            )
                    
                    return discovery_data, None
                else:
                    # Not a valid metal album, try again
                    continue
            else:
                # No Last.fm client, can't validate - create basic discovery with warning
                bandcamp_result = None
                try:
                    if random_album_data:
                        bc_search_result = bandcamp_search(random_metal_artist, random_album_data["album"])
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
                    "discovery": {
                        **random_album_data,
                        "lastfm_tags": [],  # Empty because no Last.fm
                        "metal_tags": [],
                        "formatted_tags": "#randomdiscovery"
                    },
                    "bandcamp": bandcamp_result,
                    "description": f"Based on '{base_album_name}' by {base_artist_name} → Related artist: {random_metal_artist}",
                    "validation": "⚠️ No Last.fm validation available",
                    "similarity_score": "Unknown",
                    "lastfm_tags": [],  # Empty tags for consistency
                    "formatted_tags": "#randomdiscovery"
                }
                
                return discovery_data, None
        
        # If we get here, we couldn't find a valid metal album after max attempts
        return None, f"Could not find a validated metal album after {max_attempts} attempts. Try again!"
        
    except Exception as e:
        return None, f"Error during discovery: {str(e)}"