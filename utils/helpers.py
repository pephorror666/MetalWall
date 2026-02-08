# File: metalwall_app/utils/helpers.py
# ===========================
# UTILITY FUNCTIONS
# ===========================

import streamlit as st
import re
from datetime import datetime
from typing import List

def verify_credentials(username: str, password: str) -> tuple[bool, str]:
    """Verify user credentials"""
    try:
        if username in st.secrets:
            if st.secrets[username]["password"] == password:
                return True, st.secrets[username].get("email", username)
        return False, ""
    except Exception as e:
        print(f"Authentication error: {e}")
        return False, ""

def get_time_ago(timestamp: datetime) -> str:
    """Calculate relative time"""
    now = datetime.now()
    diff = now - timestamp
    minutes = int(diff.total_seconds() / 60)
    hours = int(diff.total_seconds() / 3600)
    days = int(diff.total_seconds() / 86400)
    
    if minutes < 1:
        return "just now"
    elif minutes < 60:
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif hours < 24:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        return f"{days} day{'s' if days > 1 else ''} ago"

def format_date_display(date_str: str) -> str:
    """Convert YYYY-MM-DD to DD/MM/YYYY"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%d/%m/%Y')
    except:
        return date_str

def get_days_until(date_str: str) -> int:
    """Calculate days until concert"""
    try:
        concert_date = datetime.strptime(date_str, '%Y-%m-%d')
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        concert_date = concert_date.replace(hour=0, minute=0, second=0, microsecond=0)
        return (concert_date - today).days
    except:
        return 0

def process_tags(tags_str: str) -> List[str]:
    """Process tags string into list of tags"""
    tags = []
    for tag in tags_str.split():
        tag = tag.strip()
        if tag:
            if tag.startswith('#'):
                tag = tag[1:]
            
            # Clean the tag: lowercase and remove extra whitespace
            tag = tag.lower().strip()
            
            # Allow letters, numbers, hyphens, and underscores
            # Remove any characters that aren't alphanumeric, hyphen, or underscore
            tag = ''.join(c for c in tag if c.isalnum() or c in '-_')
            
            # Only add if not empty and not too long
            if tag and len(tag) <= 30:
                # Remove multiple consecutive hyphens
                while '--' in tag:
                    tag = tag.replace('--', '-')
                # Remove leading/trailing hyphens/underscores
                tag = tag.strip('-_')
                if tag and tag not in tags:
                    tags.append(tag)
    
    # Limit to 5 tags
    return tags[:5]

def show_success_message(message: str):
    """Show a success message and update session state"""
    st.session_state.success_message = message
    st.session_state.form_submitted = True
    st.success(message)