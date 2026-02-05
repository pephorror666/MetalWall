# File: metalwall_app/database/models.py
# ===========================
# DATABASE MODELS AND SCHEMA
# ===========================

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import json

@dataclass
class Album:
    """Album data model"""
    id: int
    username: str
    url: str
    artist: str
    album_name: str
    cover_url: Optional[str]
    platform: str
    tags: List[str]
    likes: List[str]
    timestamp: datetime
    created_at: datetime
    
    @classmethod
    def from_db_row(cls, row):
        """Create Album instance from database row"""
        return cls(
            id=row[0],
            username=row[1],
            url=row[2],
            artist=row[3],
            album_name=row[4],
            cover_url=row[5],
            platform=row[6],
            tags=eval(row[7]) if isinstance(row[7], str) else row[7],
            likes=eval(row[8]) if isinstance(row[8], str) else [],
            timestamp=datetime.fromisoformat(row[9]),
            created_at=datetime.fromisoformat(row[10]) if row[10] else datetime.fromisoformat(row[9])
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'url': self.url,
            'artist': self.artist,
            'album_name': self.album_name,
            'cover_url': self.cover_url,
            'platform': self.platform,
            'tags': self.tags,
            'likes': self.likes,
            'timestamp': self.timestamp.isoformat(),
            'created_at': self.created_at.isoformat()
        }

@dataclass
class Concert:
    """Concert data model"""
    id: int
    username: str
    bands: str
    date: str
    venue: str
    city: str
    tags: List[str]
    info: str
    likes: List[str]
    timestamp: datetime
    created_at: datetime
    
    @classmethod
    def from_db_row(cls, row):
        """Create Concert instance from database row"""
        return cls(
            id=row[0],
            username=row[1],
            bands=row[2],
            date=row[3],
            venue=row[4],
            city=row[5],
            tags=eval(row[6]) if isinstance(row[6], str) else row[6],
            info=row[7],
            likes=eval(row[8]) if isinstance(row[8], str) else [],
            timestamp=datetime.fromisoformat(row[9]),
            created_at=datetime.fromisoformat(row[10]) if row[10] else datetime.fromisoformat(row[9])
        )

@dataclass
class AlbumDiscovery:
    """Album discovery data model"""
    id: int
    username: str
    base_artist: str
    base_album: str
    discovered_artist: str
    discovered_album: str
    discovered_url: Optional[str]
    cover_url: Optional[str]
    discovered_at: datetime
    
    @classmethod
    def from_db_row(cls, row):
        """Create AlbumDiscovery instance from database row"""
        return cls(
            id=row[0],
            username=row[1],
            base_artist=row[2],
            base_album=row[3],
            discovered_artist=row[4],
            discovered_album=row[5],
            discovered_url=row[6],
            cover_url=row[7],
            discovered_at=datetime.fromisoformat(row[8])
        )