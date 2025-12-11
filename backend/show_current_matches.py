
import requests
from bs4 import BeautifulSoup
import logging

BASE_URL = "https://www.resultados-futbol.com/quiniela"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def show_matches():
    print(f"Fetching {BASE_URL}...")
    resp = requests.get(BASE_URL, headers=HEADERS)
    soup = BeautifulSoup(resp.content, "lxml")
    
    # Same logic as scraper.py but print everything
    import re
    links = soup.find_all("a", href=re.compile(r"/partido/"))
    seen = set()
    found = []
    
    for link in links:
        text = link.get_text(separator=" ").strip()
        if " - " not in text: continue
        parts = text.split(" - ")
        if len(parts) != 2: continue
        
        match_id = text
        if match_id in seen: continue
        seen.add(match_id)
        found.append(text)
        
    with open("current_matches_log.txt", "w", encoding="utf-8") as f:
        f.write("\n--- PARTIDOS ENCONTRADOS ---\n")
        for m in found:
            f.write(f"{m}\n")
            
    if not found:
        with open("current_matches_log.txt", "a", encoding="utf-8") as f:
            f.write("No matches found (HTML parsing might be failing).\n")

if __name__ == "__main__":
    show_matches()
