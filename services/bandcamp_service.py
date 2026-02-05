# File: metalwall_app/services/bandcamp_service.py
# ===========================
# BANDCAMP SERVICE
# ===========================

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict

def bandcamp_search(artist: str, record: str) -> Optional[Dict]:
    """Scrape Bandcamp search results and return first match"""
    try:
        q = f"{artist} {record}".replace(" ", "+")
        url = f"https://bandcamp.com/search?q={q}&item_type=a"
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, "html.parser")
        li = soup.find("li", class_="searchresult")
        if not li:
            return None
        a_tag = li.find("a", href=True)
        heading = li.find("div", class_="heading")
        subhead = li.find("div", class_="subhead")
        if a_tag and heading and subhead:
            clean = a_tag["href"].split("?")[0]
            return {
                "artist": subhead.text.replace("by ", "").strip(),
                "album": heading.text.strip(),
                "url": clean,
            }
    except Exception as e:
        print(f"Error searching Bandcamp: {e}")
        pass
    return None