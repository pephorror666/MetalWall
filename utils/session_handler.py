# File: metalwall_app/utils/session_handler.py
# ===========================
# SESSION MANAGEMENT
# ===========================

import streamlit as st
import json
import base64
from datetime import datetime

def save_session_to_storage():
    """Save current session state to browser's localStorage using query params"""
    if st.session_state.get('remember_me', False) and st.session_state.get('current_user'):
        session_data = {
            'username': st.session_state.current_user,
            'remember_me': True,
            'timestamp': datetime.now().isoformat()
        }
        # Encode the session data and set it as a query parameter
        encoded_data = base64.urlsafe_b64encode(json.dumps(session_data).encode()).decode()
        st.query_params['session'] = encoded_data

def load_session_from_storage() -> bool:
    """Load session from query parameters"""
    try:
        if 'session' in st.query_params:
            encoded_data = st.query_params['session']
            session_data = json.loads(base64.urlsafe_b64decode(encoded_data).decode())
            
            # Check if session is not too old (7 days max)
            session_time = datetime.fromisoformat(session_data['timestamp'])
            if (datetime.now() - session_time).days < 7:
                st.session_state.current_user = session_data['username']
                st.session_state.remember_me = session_data['remember_me']
                return True
    except:
        pass
    return False

def clear_session_storage():
    """Clear the session from query params"""
    # Clear only the session parameter
    params = dict(st.query_params)
    if 'session' in params:
        del params['session']
        st.query_params.clear()
        for key, value in params.items():
            st.query_params[key] = value