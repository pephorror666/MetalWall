# File: metalwall_app/services/random_album.py
# ===========================
# RANDOM ALBUM DISCOVERY SERVICE (OPTIMIZED)
# ===========================

import streamlit as st
import random
import time
from typing import Optional, Dict, Tuple, List
from database.operations import load_albums, save_discovery
from services.spotify_service import get_spotify_client, get_related_artists_spotify, get_random_album_by_artist
from services.lastfm_service import get_lastfm_client, get_related_artists_lastfm
from services.bandcamp_service import bandcamp_search

def normalize_name(name: str) -> str:
    """Normaliza nombres para comparaciones precisas"""
    if not name: return ""
    import re
    # Convertir a minúsculas, quitar "The " al inicio y eliminar caracteres no alfanuméricos
    name = name.lower().strip()
    if name.startswith("the "):
        name = name[4:]
    return re.sub(r'[^a-z0-9]', '', name)

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
    Verifica si un artista es metal usando tags de Last.fm.
    He mejorado la lista de keywords para ser más selectiva.
    """
    if not lastfm_client:
        return False
    
    try:
        artist = lastfm_client.get_artist(artist_name)
        tags = artist.get_top_tags(limit=15) # Aumentado a 15 para mayor precisión
        tag_names = [tag.item.get_name().lower() for tag in tags]
        
        metal_keywords = [
            'metal', 'grindcore', 'goregrind', 'deathcore', 'metalcore', 
            'djent', 'sludge', 'thrash', 'death metal', 'black metal'
        ]
        
        # Si tiene alguno de estos tags, es metal
        for tag in tag_names:
            if any(keyword in tag for keyword in metal_keywords):
                return True
        return False
    except Exception:
        return False

def validate_and_correct_metal_album(lastfm_client, spotify_album_data: Dict, target_artist_name: str) -> Tuple[Optional[Dict], bool]:
    """
    VALIDACIÓN MEJORADA:
    1. Verifica que el artista de Spotify coincida con el buscado (evita confusión Sabbat/Black Sabbath).
    2. Verifica que el artista resultante sea Metal.
    """
    if not spotify_album_data:
        return None, False

    result_artist_name = spotify_album_data.get('artist', '')
    
    # --- CAPA 1: Validación de Identidad Estricta ---
    # Comparamos el nombre buscado con el obtenido de la URL de Spotify
    if normalize_name(result_artist_name) != normalize_name(target_artist_name):
        # Si Spotify nos dio un artista diferente (ej. Black Sabbath cuando buscamos Sabbat)
        return None, False

    # --- CAPA 2: Validación de Género ---
    if not lastfm_client:
        return spotify_album_data, True # No podemos validar, confiamos
    
    # Verificamos si el artista que Spotify ha devuelto es realmente metal
    if is_metal_artist(lastfm_client, result_artist_name):
        return spotify_album_data, True
    
    # --- CAPA 3: Re-validación por Album ---
    # A veces el artista no tiene tags, pero el album sí
    try:
        album_name = spotify_album_data.get('album', '')
        search_results = lastfm_client.search_for_album(album_name, result_artist_name)
        if search_results:
            album = search_results[0]
            tags = album.get_top_tags(limit=5)
            if any('metal' in tag.item.get_name().lower() for tag in tags):
                return spotify_album_data, True
    except:
        pass

    return None, False

def discover_random_album(base_artist: Optional[str] = None, base_album_obj: Optional[Dict] = None, 
                         max_attempts: int = 8) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Función principal mejorada para evitar confusiones de artistas.
    """
    try:
        spotify_client = get_spotify_client()
        lastfm_client = get_lastfm_client()
        
        if base_album_obj is None:
            random_album = get_random_album_from_wall()
            if not random_album:
                return None, "No albums found in the wall"
        else:
            random_album = base_album_obj
        
        base_artist_name = random_album.get('artist', '')
        base_album_name = random_album.get('album_name', '')
        
        from services.spotify_service import clean_artist_name
        base_artist_name = clean_artist_name(base_artist_name)
        
        # Obtener artistas relacionados
        related_artists = []
        if spotify_client:
            related_artists = get_related_artists_spotify(spotify_client, base_artist_name)
        if not related_artists and lastfm_client:
            related_artists = get_related_artists_lastfm(lastfm_client, base_artist_name)
        
        if not related_artists:
            return None, f"No related artists found for {base_artist_name}"
        
        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            random_artist = random.choice(related_artists)
            
            # Obtener album del artista seleccionado
            random_album_data = None
            if spotify_client:
                random_album_data = get_random_album_by_artist(spotify_client, random_artist)
            
            if not random_album_data:
                continue

            # --- VALIDACIÓN CRÍTICA ---
            # Pasamos 'random_artist' para asegurar que el resultado de Spotify sea de ESE artista
            validated_album, is_valid = validate_and_correct_metal_album(
                lastfm_client, random_album_data, random_artist
            )
            
            if is_valid and validated_album:
                # Si pasa la validación, procedemos a extraer tags y buscar en Bandcamp
                discovery_tags = []
                # (Mantengo tu lógica original de extracción de tags...)
                if validated_album.get('genres'):
                    for genre in validated_album['genres'][:3]:
                        tag = genre.lower().replace(' ', '')
                        if tag not in discovery_tags: discovery_tags.append(tag)
                
                try:
                    artist_info = lastfm_client.get_artist(validated_album["artist"])
                    lfm_tags = artist_info.get_top_tags(limit=5)
                    for t in lfm_tags:
                        t_name = t.item.get_name().lower().replace(' ', '')
                        if any(k in t_name for k in ['metal', 'death', 'thrash', 'doom', 'grind']):
                            if t_name not in discovery_tags and len(discovery_tags) < 5:
                                discovery_tags.append(t_name)
                except: pass
                
                discovery_tags.append('randomdiscovery')

                # Búsqueda en Bandcamp
                bandcamp_result = None
                try:
                    bc_search_result = bandcamp_search(validated_album["artist"], validated_album["album"])
                    if bc_search_result:
                        bandcamp_result = {
                            "url": bc_search_result["url"],
                            "artist": bc_search_result["artist"],
                            "album": bc_search_result["album"]
                        }
                except: pass

                discovery_data = {
                    "origin": {"album": random_album, "artist": base_artist_name, "album_name": base_album_name},
                    "discovery": validated_album,
                    "bandcamp": bandcamp_result,
                    "description": f"Based on '{base_album_name}' by {base_artist_name} → Related: {validated_album['artist']}",
                    "validation": "✅ Validated Metal Artist & Identity",
                    "tags": discovery_tags
                }
                
                if st.session_state.get('current_user'):
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
            
        return None, f"Could not find a confirmed metal album after {max_attempts} attempts."
        
    except Exception as e:
        return None, f"Error during discovery: {str(e)}"