# File: metalwall_app/services/metadata_extractor.py
# ===========================
# METADATA EXTRACTION SERVICE
# ===========================

import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
from config import PLATFORMS

def get_headers_for_url(url: str) -> Dict[str, str]:
    """Get appropriate headers based on the platform"""
    url_lower = url.lower()
    
    if 'bandcamp' in url_lower:
        # Bandcamp-specific headers
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://bandcamp.com/',  # Add this!
        }
    elif 'spotify' in url_lower:
        # Spotify-specific headers
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    else:
        # Generic headers for other platforms
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

def detect_platform(url: str) -> str:
    """Detect platform based on domain"""
    url_lower = url.lower()
    for key, value in PLATFORMS.items():
        if key in url_lower:
            return value
    return 'Other'

def extract_artist(metadata: Dict, platform: str) -> str:
    """Extract artist name from metadata"""
    title = metadata.get('og_title', '')
    description = metadata.get('og_description', '')
    
    if ' - ' in title:
        parts = title.split(' - ')
        if len(parts) >= 2:
            return parts[-1].strip()
    
    if 'by' in description:
        match = re.search(r'by (.+?)$|by (.+?) on', description, re.IGNORECASE)
        if match:
            return match.group(1) or match.group(2)
    
    if ' by ' in title:
        return title.split(' by ')[-1].strip()
    
    return 'Unknown Artist'

def extract_album(metadata: Dict, platform: str) -> str:
    """Extract album name from metadata"""
    title = metadata.get('og_title', '')
    
    if ' - ' in title:
        parts = title.split(' - ')
        return parts[0].strip()
    
    if ' by ' in title:
        return title.split(' by ')[0].strip()
    
    return title or 'Unknown Album'

def extract_og_metadata(url: str) -> Optional[Dict]:
    """
    UNIVERSAL extractor using Open Graph metadata
    Works with ANY platform (Spotify, Bandcamp, Tidal, Apple Music, etc.)
    Similar to how WhatsApp/Discord/Twitter does it
    """
    try:
        headers = get_headers_for_url(url)
        
        # For Bandcamp, we might need to follow redirects
        session = requests.Session()
        session.headers.update(headers)
        
        # Increase timeout for Bandcamp
        timeout = 15 if 'bandcamp' in url.lower() else 8
        
        response = session.get(url, timeout=timeout, allow_redirects=True)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            # Try with a different approach for Bandcamp
            if 'bandcamp' in url.lower():
                return try_bandcamp_fallback(url, session)
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        metadata = {}
        
        # Look for Open Graph meta tags
        for meta in soup.find_all('meta', property=True):
            prop = meta.get('property', '')
            content = meta.get('content', '')
            if prop == 'og:title':
                metadata['og_title'] = content
            elif prop == 'og:description':
                metadata['og_description'] = content
            elif prop == 'og:image':
                metadata['og_image'] = content
        
        # Fallback: look for meta name
        if not metadata.get('og_title'):
            for meta in soup.find_all('meta'):
                name = meta.get('name', '')
                content = meta.get('content', '')
                if name.lower() == 'description':
                    metadata['og_description'] = content
                elif name.lower() == 'twitter:title':
                    metadata['og_title'] = content
                elif name.lower() == 'twitter:image':
                    metadata['og_image'] = content
        
        # Special handling for Bandcamp if OG tags not found
        if not metadata.get('og_title') and 'bandcamp' in url.lower():
            return extract_bandcamp_metadata(soup, url)
        
        if not metadata.get('og_title'):
            return None
        
        platform = detect_platform(url)
        return {
            'artist': extract_artist(metadata, platform),
            'album_name': extract_album(metadata, platform),
            'cover_url': metadata.get('og_image', ''),
            'platform': platform
        }
    except Exception as e:
        print(f"Error extracting metadata from {url}: {e}")
        return None

def extract_bandcamp_metadata(soup: BeautifulSoup, url: str) -> Optional[Dict]:
    """Extract metadata specifically from Bandcamp pages"""
    try:
        # Try to get title from <title> tag
        title_tag = soup.find('title')
        title = title_tag.text.strip() if title_tag else ''
        
        # Try to get artist and album from title
        artist = 'Unknown Artist'
        album_name = 'Unknown Album'
        
        if ' | ' in title:
            parts = title.split(' | ')
            if len(parts) >= 2:
                # Format is usually "Album Name | Artist Name | Bandcamp"
                album_name = parts[0].strip()
                artist = parts[1].strip()
        elif ' by ' in title.lower():
            parts = title.lower().split(' by ')
            if len(parts) >= 2:
                album_name = parts[0].strip()
                artist = parts[1].replace('| bandcamp', '').strip().title()
        
        # Try to get cover image
        cover_url = ''
        
        # Look for track art
        track_art = soup.find('a', class_='popupImage')
        if track_art and track_art.get('href'):
            cover_url = track_art['href']
        else:
            # Look for album art
            album_art = soup.find('img', id='tralbumArt')
            if album_art and album_art.get('src'):
                cover_url = album_art['src']
            else:
                # Look for any image with class containing 'art'
                for img in soup.find_all('img', class_=lambda x: x and 'art' in x.lower()):
                    if img.get('src'):
                        cover_url = img['src']
                        break
        
        # Clean up artist name
        if artist.lower().endswith('| bandcamp'):
            artist = artist[:-10].strip()
        
        return {
            'artist': artist,
            'album_name': album_name,
            'cover_url': cover_url,
            'platform': 'Bandcamp'
        }
    except Exception as e:
        print(f"Error extracting Bandcamp metadata: {e}")
        return None

def try_bandcamp_fallback(url: str, session: requests.Session) -> Optional[Dict]:
    """Try alternative methods for Bandcamp"""
    try:
        # Try with mobile user agent
        mobile_headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        session.headers.update(mobile_headers)
        response = session.get(url, timeout=15, allow_redirects=True)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return extract_bandcamp_metadata(soup, url)
    
    except Exception as e:
        print(f"Bandcamp fallback failed: {e}")
    
    return None