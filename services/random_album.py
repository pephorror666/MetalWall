# File: metalwall_app/services/random_album.py
# ===========================
# RANDOM ALBUM DISCOVERY SERVICE (ULTRA-STRICT VERSION 2.0)
# ===========================

import streamlit as st
import random
import re
from typing import Optional, Dict, Tuple, List
from database.operations import load_albums, save_discovery
from services.spotify_service import get_spotify_client, get_related_artists_spotify, get_random_album_by_artist
from services.lastfm_service import get_lastfm_client, get_related_artists_lastfm
from services.bandcamp_service import bandcamp_search

def clean_strictly(text: str) -> str:
    """Limpia el texto para comparaciones de identidad exactas."""
    if not text: return ""
    # Convertir a minúsculas y eliminar todo lo que no sea letras o números
    return re.sub(r'[^a-z0-9]', '', text.lower())

def is_metal_artist(lastfm_client, artist_name: str) -> bool:
    """Verifica si un artista es metal con filtrado de etiquetas y protección de identidad."""
    if not lastfm_client:
        return False
    try:
        # Last.fm suele "autocorregir" nombres (ej. Taake -> Taaken). 
        # Obtenemos el objeto sin permitir redirecciones automáticas si es posible,
        # o verificamos el nombre final.
        artist = lastfm_client.get_artist(artist_name)
        
        # VALIDACIÓN DE IDENTIDAD EN LAST.FM
        if clean_strictly(artist.get_name()) != clean_strictly(artist_name):
            return False

        tags = artist.get_top_tags(limit=20)
        tag_names = [tag.item.get_name().lower() for tag in tags]
        
        metal_keywords = [
            'metal', 'grindcore', 'goregrind', 'deathcore', 'sludge', 
            'thrash', 'death metal', 'black metal', 'doom metal', 'stoner'
        ]
        
        # Bloqueo total de géneros que causan falsos positivos
        excluded_genres = ['pop', 'jazz', 'rnb', 'house', 'techno', 'musical', 'soundtrack', 'broadway', 'easy listening']
        
        has_metal_tag = any(any(k in tag for k in metal_keywords) for tag in tag_names)
        has_pop_tag = any(any(e == tag for e in excluded_genres) for tag in tag_names)
        
        # Un artista es válido si tiene tags de metal y no está "contaminado" por géneros excluidos
        # (a menos que el tag excluido forme parte de una etiqueta de metal, ej. "heavy metal pop" - poco común pero posible)
        return has_metal_tag and not (has_pop_tag and not 'metal' in "".join(tag_names))
    except:
        return False

def validate_identity_and_genre(lastfm_client, result_data: Dict, target_artist: str) -> bool:
    """
    Verifica que el resultado sea del artista buscado y pertenezca al género.
    """
    if not result_data:
        return False
    
    # 1. VERIFICACIÓN DE IDENTIDAD (CRÍTICO)
    # Comparamos el artista que Spotify DEVOLVIÓ con el que ESTÁBAMOS BUSCANDO.
    # Esto evita que "The Silver" devuelva "The Beatles" o "Narco" devuelva "Narcotic Thrust".
    name_found = clean_strictly(result_data.get('artist', ''))
    name_target = clean_strictly(target_artist)
    
    if name_found != name_target:
        return False

    # 2. VERIFICACIÓN DE ÁLBUM SOSPECHOSO
    # Si el álbum contiene palabras clave de musicales o bandas sonoras, lo rechazamos.
    album_name = result_data.get('album', '').lower()
    if any(k in album_name for k in ['musical', 'soundtrack', 'cast recording', 'broadway']):
        return False

    # 3. VERIFICACIÓN DE GÉNERO
    spotify_genres = [g.lower() for g in result_data.get('genres', [])]
    
    # Si Spotify tiene géneros, buscamos keywords de metal
    is_metal_on_spotify = any('metal' in g or 'grindcore' in g or 'death' in g or 'doom' in g for g in spotify_genres)
    
    # Si Spotify explícitamente dice que es un género no deseado
    is_non_metal = any(any(x in g for x in ['pop', 'hip hop', 'house', 'musical']) for g in spotify_genres)

    if is_metal_on_spotify and not is_non_metal:
        return True
        
    # En caso de duda (o falta de géneros en Spotify), recurrimos a Last.fm
    if lastfm_client:
        return is_metal_artist(lastfm_client, target_artist)
        
    return False

def discover_random_album(base_artist: Optional[str] = None, base_album_obj: Optional[Dict] = None, 
                         max_attempts: int = 15) -> Tuple[Optional[Dict], Optional[str]]:
    """Discovery con validación cruzada entre Spotify y Last.fm."""
    try:
        spotify_client = get_spotify_client()
        lastfm_client = get_lastfm_client()
        
        if base_album_obj is None:
            random_album = get_random_album_from_wall()
            if not random_album: return None, "No base albums found in database."
        else:
            random_album = base_album_obj
        
        base_artist_name = random_album.get('artist', '')
        base_album_name = random_album.get('album_name', '')
        
        from services.spotify_service import clean_artist_name
        base_artist_name = clean_artist_name(base_artist_name)
        
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
            
            # Evitamos recomendar al mismo artista del que partimos
            if clean_strictly(random_artist) == clean_strictly(base_artist_name):
                continue

            random_album_data = None
            if spotify_client:
                # Obtenemos un álbum aleatorio del artista seleccionado
                random_album_data = get_random_album_by_artist(spotify_client, random_artist)
            
            # --- VALIDACIÓN ESTRICTA ---
            if random_album_data and validate_identity_and_genre(lastfm_client, random_album_data, random_artist):
                
                # Procesamiento de Tags
                discovery_tags = []
                if random_album_data.get('genres'):
                    discovery_tags = [g.lower().replace(' ', '') for g in random_album_data['genres'][:3]]
                
                try:
                    lfm_artist = lastfm_client.get_artist(random_album_data["artist"])
                    tags = lfm_artist.get_top_tags(limit=5)
                    for t in tags:
                        t_name = t.item.get_name().lower().replace(' ', '')
                        if any(k in t_name for k in ['metal', 'death', 'thrash', 'doom', 'grind', 'sludge']):
                            if t_name not in discovery_tags: discovery_tags.append(t_name)
                except: pass
                
                discovery_tags.append('randomdiscovery')
                
                # Búsqueda en Bandcamp
                bandcamp_result = None
                try:
                    bc_res = bandcamp_search(random_album_data["artist"], random_album_data["album"])
                    if bc_res:
                        bandcamp_result = {"url": bc_res["url"], "artist": bc_res["artist"], "album": bc_res["album"]}
                except: pass

                discovery_data = {
                    "origin": {"album": random_album, "artist": base_artist_name, "album_name": base_album_name},
                    "discovery": random_album_data,
                    "bandcamp": bandcamp_result,
                    "description": f"Based on '{base_album_name}' by {base_artist_name} → Related: {random_album_data['artist']}",
                    "validation": "✅ Identity and Genre verified",
                    "tags": discovery_tags
                }
                
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
            
        return None, f"Could not find a valid metal album after {max_attempts} attempts."
        
    except Exception as e:
        return None, f"Discovery error: {str(e)}"

def get_random_album_from_wall() -> Optional[Dict]:
    """Carga un álbum aleatorio de la base de datos."""
    try:
        albums = load_albums()
        if not albums: return None
        album = random.choice(albums)
        return {
            'artist': album.artist,
            'album_name': album.album_name,
            'url': album.url,
            'cover_url': album.cover_url
        }
    except:
        return None