# File: metalwall_app/app.py
# ===========================
# THE METAL WALL - MODULAR VERSION
# ===========================

import streamlit as st
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import init_session_state, PAGE_CONFIG
from database.init_db import init_db
from ui.styling import get_custom_css

def main():
    """Main entry point for the MetalWall app"""
    # Set page config FIRST
    st.set_page_config(**PAGE_CONFIG)
    
    # Apply custom CSS
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Initialize session state
    init_session_state()
    
    # Try to load session from storage
    from utils.session_handler import load_session_from_storage
    if st.session_state.current_user is None:
        load_session_from_storage()
    
    # Initialize database
    init_db()
    
    # Debug: Show session state
    #st.write("DEBUG: Session state:", st.session_state)
    
    # Import and run pages here to avoid circular imports
    from ui.pages import main_page
    main_page()

if __name__ == "__main__":
    main()