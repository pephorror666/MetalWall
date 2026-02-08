# File: metalwall_app/ui/styling.py
# ===========================
# UI STYLING AND CSS
# ===========================

def get_custom_css() -> str:
    """Return custom CSS for the app"""
    return """
    <style>
        body {
            background-color: #0a0e27;
            color: #e0e0e0;
        }
        .clickable-image {
            cursor: pointer;
            transition: transform 0.2s;
        }
        .clickable-image:hover {
            transform: scale(1.02);
        }
        .tag-button {
            margin-right: 5px;
            margin-bottom: 2px;
        }
        /* Success notification styling */
        .stSuccess {
            background-color: #1a472a !important;
            border-color: #2e7d32 !important;
            color: #e0e0e0 !important;
        }
        .guest-notice {
            background-color: #2d3748;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #4299e1;
        }
        .admin-tools {
            background-color: #1a1a2e;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #4a4a6a;
            margin: 10px 0;
        }
        .sort-option {
            padding: 8px 12px;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .sort-option:hover {
            background-color: #2a2a4a;
        }
        .sort-option.active {
            background-color: #4299e1;
            color: white;
        }
        .random-album-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid #4a4a6a;
            margin: 20px 0;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
        }
        .discovery-path {
            background-color: #2d3748;
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            border-left: 4px solid #9d4edd;
        }
        .album-cover {
            width: 100%;
            border-radius: 8px;
            object-fit: cover;
            height: 180px;
        }
        .no-cover {
            width: 100%;
            height: 180px;
            background: #333;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
        }
    </style>
    """