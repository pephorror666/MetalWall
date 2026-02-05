# File: metalwall_app/services/metadata_extractor.py
# ===========================
# METADATA EXTRACTION SERVICE
# ===========================

import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Tuple
from config import PLATFORMS
import json

def get_headers_for_url(url: str) -> Dict[str, str]:
    """Get appropriate headers based on the platform"""
    url_lower = url.lower()
    
    if 'bandcamp' in url_lower:
        # Bandcamp-specific headers with multiple User-Agents
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://bandcamp.com/',
            'Cache-Control': 'no-cache',
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

# ===========================
# BANDCAMP-SPECIFIC EXTRACTION
# ===========================

def extract_bandcamp_metadata_robust(soup: BeautifulSoup, url: str) -> Optional[Dict]:
    """Robust Bandcamp metadata extraction with multiple fallback methods"""
    metadata = {}
    
    # METHOD 1: Try to extract from JavaScript data
    metadata = _extract_bandcamp_from_js(soup)
    if metadata.get('artist') and metadata.get('album_name') and metadata.get('artist') != 'Unknown Artist':
        metadata['platform'] = 'Bandcamp'
        return metadata
    
    # METHOD 2: Try to extract from Open Graph tags
    metadata = _extract_bandcamp_og_tags(soup)
    if metadata.get('artist') and metadata.get('album_name') and metadata.get('artist') != 'Unknown Artist':
        metadata['platform'] = 'Bandcamp'
        return metadata
    
    # METHOD 3: Try to extract from structured data (JSON-LD)
    metadata = _extract_bandcamp_json_ld(soup)
    if metadata.get('artist') and metadata.get('album_name'):
        metadata['platform'] = 'Bandcamp'
        return metadata
    
    # METHOD 4: Try to extract from HTML structure
    metadata = _extract_bandcamp_html_structure(soup)
    if metadata.get('artist') and metadata.get('album_name'):
        metadata['platform'] = 'Bandcamp'
        return metadata
    
    # METHOD 5: Try to extract from title tag patterns
    metadata = _extract_bandcamp_from_title(soup)
    if metadata.get('artist') and metadata.get('album_name'):
        metadata['platform'] = 'Bandcamp'
        return metadata
    
    # Fallback: Return whatever we have
    if metadata:
        metadata['platform'] = 'Bandcamp'
        return metadata
    
    return None

def _extract_bandcamp_from_js(soup: BeautifulSoup) -> Dict:
    """Extract metadata from embedded JavaScript data"""
    metadata = {'artist': 'Unknown Artist', 'album_name': 'Unknown Album', 'cover_url': ''}
    
    try:
        # Look for TralbumData (common Bandcamp pattern)
        for script in soup.find_all('script'):
            if script.string and 'TralbumData' in script.string:
                # Extract the JSON object
                match = re.search(r'TralbumData\s*=\s*({.*?});', script.string, re.DOTALL)
                if match:
                    try:
                        data_str = match.group(1)
                        # Clean up the string
                        data_str = re.sub(r'//.*?\n', '', data_str)  # Remove single-line comments
                        data = json.loads(data_str)
                        
                        if data.get('artist'):
                            metadata['artist'] = data['artist']
                        if data.get('current') and data['current'].get('title'):
                            metadata['album_name'] = data['current']['title']
                        elif data.get('album_title'):
                            metadata['album_name'] = data['album_title']
                        if data.get('art_id'):
                            # Construct cover URL from art_id
                            metadata['cover_url'] = f"https://f4.bcbits.com/img/a{data['art_id']}_16.jpg"
                    except (json.JSONDecodeError, KeyError):
                        pass
        
        # Look for other common Bandcamp data patterns
        for script in soup.find_all('script'):
            script_text = script.string
            if not script_text:
                continue
                
            # Look for artist in various patterns
            artist_patterns = [
                r'"artist":"([^"]+)"',
                r"artist:\s*'([^']+)'",
                r'artist:\s*"([^"]+)"',
                r'data-artist="([^"]+)"',
            ]
            
            for pattern in artist_patterns:
                match = re.search(pattern, script_text)
                if match and match.group(1) and match.group(1) != 'null':
                    metadata['artist'] = match.group(1).strip()
                    break
            
            # Look for album/track title
            title_patterns = [
                r'"title":"([^"]+)"',
                r"title:\s*'([^']+)'",
                r'title:\s*"([^"]+)"',
                r'data-item-title="([^"]+)"',
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, script_text)
                if match and match.group(1) and match.group(1) != 'null':
                    metadata['album_name'] = match.group(1).strip()
                    break
            
            # Look for cover art
            cover_patterns = [
                r'"art_id":\s*(\d+)',
                r'art_id:\s*(\d+)',
                r'"artUrl":"([^"]+)"',
                r'artUrl:\s*"([^"]+)"',
            ]
            
            for pattern in cover_patterns:
                match = re.search(pattern, script_text)
                if match:
                    if match.group(1).isdigit():
                        metadata['cover_url'] = f"https://f4.bcbits.com/img/a{match.group(1)}_16.jpg"
                    else:
                        metadata['cover_url'] = match.group(1)
                    break
    
    except Exception as e:
        print(f"Error extracting from JS: {e}")
    
    return metadata

def _extract_bandcamp_og_tags(soup: BeautifulSoup) -> Dict:
    """Extract metadata from Open Graph tags"""
    metadata = {'artist': 'Unknown Artist', 'album_name': 'Unknown Album', 'cover_url': ''}
    
    try:
        og_title = soup.find('meta', property='og:title')
        og_description = soup.find('meta', property='og:description')
        og_image = soup.find('meta', property='og:image')
        
        if og_title and og_title.get('content'):
            title = og_title['content']
            # Try to parse "Artist - Album" format
            if ' - ' in title:
                parts = title.split(' - ')
                if len(parts) >= 2:
                    metadata['artist'] = parts[0].strip()
                    metadata['album_name'] = parts[1].strip()
        
        if og_description and og_description.get('content'):
            desc = og_description['content']
            # Try to extract artist from description
            artist_match = re.search(r'by\s+([^,.]+)', desc, re.IGNORECASE)
            if artist_match:
                metadata['artist'] = artist_match.group(1).strip()
        
        if og_image and og_image.get('content'):
            metadata['cover_url'] = og_image['content']
    
    except Exception as e:
        print(f"Error extracting OG tags: {e}")
    
    return metadata

def _extract_bandcamp_json_ld(soup: BeautifulSoup) -> Dict:
    """Extract metadata from JSON-LD structured data"""
    metadata = {'artist': 'Unknown Artist', 'album_name': 'Unknown Album', 'cover_url': ''}
    
    try:
        for script in soup.find_all('script', type='application/ld+json'):
            if script.string:
                try:
                    data = json.loads(script.string)
                    
                    # Check for MusicAlbum schema
                    if data.get('@type') in ['MusicAlbum', 'MusicRecording', 'MusicGroup']:
                        if data.get('byArtist') and data['byArtist'].get('name'):
                            metadata['artist'] = data['byArtist']['name']
                        elif data.get('author') and data['author'].get('name'):
                            metadata['artist'] = data['author']['name']
                        elif data.get('performer') and data['performer'].get('name'):
                            metadata['artist'] = data['performer']['name']
                        
                        if data.get('name'):
                            metadata['album_name'] = data['name']
                        
                        if data.get('image'):
                            if isinstance(data['image'], str):
                                metadata['cover_url'] = data['image']
                            elif isinstance(data['image'], dict) and data['image'].get('url'):
                                metadata['cover_url'] = data['image']['url']
                            elif isinstance(data['image'], list) and len(data['image']) > 0:
                                metadata['cover_url'] = data['image'][0] if isinstance(data['image'][0], str) else data['image'][0].get('url', '')
                
                except json.JSONDecodeError:
                    continue
    
    except Exception as e:
        print(f"Error extracting JSON-LD: {e}")
    
    return metadata

def _extract_bandcamp_html_structure(soup: BeautifulSoup) -> Dict:
    """Extract metadata from HTML structure"""
    metadata = {'artist': 'Unknown Artist', 'album_name': 'Unknown Album', 'cover_url': ''}
    
    try:
        # Try to get artist from various selectors
        artist_selectors = [
            '.artist span', '.artist a', '.artist',
            'span[itemprop="byArtist"]', 'a[itemprop="byArtist"]',
            '.band-name', '.artist-name', '#band-name',
            'h3 span a', '.trackTitle span a', '.title-artist a'
        ]
        
        for selector in artist_selectors:
            element = soup.select_one(selector)
            if element and element.text.strip():
                metadata['artist'] = element.text.strip()
                break
        
        # Try to get album/track title
        title_selectors = [
            '.trackTitle', '.track-title', '.title',
            'h2.trackTitle', '.trackTitle span',
            '[itemprop="name"]', '.album-title',
            '#name-section h2', '.track-album'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.text.strip():
                metadata['album_name'] = element.text.strip()
                break
        
        # Try to get cover image
        cover_selectors = [
            'a.popupImage', '#tralbumArt', '.album-art',
            '.art img', '.track-art img', '[itemprop="image"]',
            'img.album-cover', '.cover-image img'
        ]
        
        for selector in cover_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'a' and element.get('href'):
                    metadata['cover_url'] = element['href']
                    break
                elif element.name == 'img' and element.get('src'):
                    metadata['cover_url'] = element['src']
                    break
        
        # Fallback: Look for any image with art in class
        if not metadata['cover_url']:
            for img in soup.find_all('img', class_=lambda x: x and 'art' in x.lower()):
                if img.get('src'):
                    metadata['cover_url'] = img['src']
                    break
    
    except Exception as e:
        print(f"Error extracting from HTML structure: {e}")
    
    return metadata

def _extract_bandcamp_from_title(soup: BeautifulSoup) -> Dict:
    """Extract metadata from title tag patterns"""
    metadata = {'artist': 'Unknown Artist', 'album_name': 'Unknown Album', 'cover_url': ''}
    
    try:
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.text.strip()
            
            # Pattern 1: "Album Name | Artist Name | Bandcamp"
            if ' | ' in title:
                parts = title.split(' | ')
                if len(parts) >= 2:
                    metadata['album_name'] = parts[0].strip()
                    metadata['artist'] = parts[1].strip()
            
            # Pattern 2: "Artist Name - Album Name"
            elif ' - ' in title:
                parts = title.split(' - ')
                if len(parts) >= 2:
                    metadata['artist'] = parts[0].strip()
                    metadata['album_name'] = parts[1].replace('| Bandcamp', '').strip()
            
            # Pattern 3: "Album Name by Artist Name"
            elif ' by ' in title.lower():
                parts = re.split(r' by ', title, flags=re.IGNORECASE)
                if len(parts) >= 2:
                    metadata['album_name'] = parts[0].strip()
                    metadata['artist'] = parts[1].replace('| Bandcamp', '').strip()
    
    except Exception as e:
        print(f"Error extracting from title: {e}")
    
    return metadata

def extract_og_metadata(url: str) -> Optional[Dict]:
    """
    UNIVERSAL extractor using Open Graph metadata
    Works with ANY platform (Spotify, Bandcamp, Tidal, Apple Music, etc.)
    Similar to how WhatsApp/Discord/Twitter does it
    """
    try:
        headers = get_headers_for_url(url)
        
        # For Bandcamp, we need more robust handling
        session = requests.Session()
        session.headers.update(headers)
        
        # Increase timeout and allow redirects
        timeout = 20 if 'bandcamp' in url.lower() else 10
        
        try:
            response = session.get(
                url, 
                timeout=timeout, 
                allow_redirects=True,
                verify=True  # SSL verification
            )
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"HTTP {response.status_code} for {url}")
                # For Bandcamp, try multiple approaches
                if 'bandcamp' in url.lower():
                    return try_multiple_bandcamp_approaches(url)
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # FOR BANDCAMP: Always use robust extraction
            if 'bandcamp' in url.lower():
                metadata = extract_bandcamp_metadata_robust(soup, url)
                if metadata:
                    return metadata
                # Fallback to OG extraction if robust method fails
                return extract_bandcamp_fallback(soup)
            
            # FOR OTHER PLATFORMS: Use OG extraction
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
            
            if not metadata.get('og_title'):
                # Try to get from title tag as last resort
                title_tag = soup.find('title')
                if title_tag:
                    metadata['og_title'] = title_tag.text.strip()
                else:
                    return None
            
            platform = detect_platform(url)
            return {
                'artist': extract_artist(metadata, platform),
                'album_name': extract_album(metadata, platform),
                'cover_url': metadata.get('og_image', ''),
                'platform': platform
            }
            
        except requests.exceptions.Timeout:
            print(f"Timeout for {url}")
            if 'bandcamp' in url.lower():
                return try_multiple_bandcamp_approaches(url)
            return None
        except requests.exceptions.RequestException as e:
            print(f"Request error for {url}: {e}")
            if 'bandcamp' in url.lower():
                return try_multiple_bandcamp_approaches(url)
            return None
            
    except Exception as e:
        print(f"Error extracting metadata from {url}: {e}")
        return None

def try_multiple_bandcamp_approaches(url: str) -> Optional[Dict]:
    """Try multiple approaches to get Bandcamp metadata"""
    approaches = [
        try_bandcamp_with_mobile_headers,
        try_bandcamp_with_desktop_headers,
        try_bandcamp_with_minimal_headers,
    ]
    
    for approach in approaches:
        try:
            metadata = approach(url)
            if metadata:
                return metadata
        except Exception as e:
            print(f"Approach failed: {e}")
            continue
    
    return None

def try_bandcamp_with_mobile_headers(url: str) -> Optional[Dict]:
    """Try with mobile user agent"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    response = session.get(url, timeout=20, allow_redirects=True)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        return extract_bandcamp_metadata_robust(soup, url)
    
    return None

def try_bandcamp_with_desktop_headers(url: str) -> Optional[Dict]:
    """Try with desktop user agent"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    response = session.get(url, timeout=20, allow_redirects=True)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        return extract_bandcamp_metadata_robust(soup, url)
    
    return None

def try_bandcamp_with_minimal_headers(url: str) -> Optional[Dict]:
    """Try with minimal headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; BandcampBot/1.0)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    response = session.get(url, timeout=20, allow_redirects=True)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        return extract_bandcamp_metadata_robust(soup, url)
    
    return None

def extract_bandcamp_fallback(soup: BeautifulSoup) -> Optional[Dict]:
    """Final fallback for Bandcamp"""
    try:
        # Last resort: try to get from any text on page
        metadata = {'artist': 'Unknown Artist', 'album_name': 'Unknown Album', 'cover_url': '', 'platform': 'Bandcamp'}
        
        # Look for any h1, h2, h3 tags that might contain info
        for tag in ['h1', 'h2', 'h3']:
            for element in soup.find_all(tag):
                text = element.text.strip()
                if text and len(text) < 100:  # Reasonable length
                    if ' - ' in text:
                        parts = text.split(' - ')
                        if len(parts) >= 2:
                            metadata['artist'] = parts[0].strip()
                            metadata['album_name'] = parts[1].strip()
                            break
        
        # Look for any image that could be a cover
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                if 'cover' in src.lower() or 'art' in src.lower() or 'album' in src.lower():
                    metadata['cover_url'] = src
                    break
        
        return metadata
    
    except Exception as e:
        print(f"Bandcamp fallback failed: {e}")
        return None