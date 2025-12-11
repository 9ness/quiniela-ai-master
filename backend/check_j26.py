
import requests
from bs4 import BeautifulSoup
import logging
import unicodedata

SPANISH_TEAMS_KEYWORDS = [
    "real madrid", "barcelona", "girona", "atletico", "athletic", "real sociedad", 
    "betis", "valencia", "villarreal", "getafe", "osasuna", "sevilla", "alaves", 
    "las palmas", "rayo", "celta", "mallorca", "cadiz", "granada", "almeria",
    "leganes", "eibar", "espanyol", "valladolid", "sporting", "oviedo", "racing",
    "elche", "levante", "burgos", "ferrol", "tenerife", "albacete", "eldense",
    "zaragoza", "cartagena", "mirandes", "huesca", "alcorcon", "andorra", "amorebieta",
    "coruna", "deportivo", "castellon", "cordoba", "malaga", "ibiza", "ponferradina"
]

def normalize_name(name):
    if not name: return ""
    name = str(name).lower()
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    return name.strip()

def is_spanish_match(local, visitante):
    l_norm = normalize_name(local)
    v_norm = normalize_name(visitante)
    is_local_ok = any(k in l_norm for k in SPANISH_TEAMS_KEYWORDS)
    is_visit_ok = any(k in v_norm for k in SPANISH_TEAMS_KEYWORDS)
    return is_local_ok, is_visit_ok, l_norm, v_norm

url = "https://www.resultados-futbol.com/quiniela/historico/26"
print(f"Checking {url}...")
resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(resp.content, "lxml")

import re
links = soup.find_all("a", href=re.compile(r"/partido/"))
seen = set()

for link in links:
    text = link.get_text(separator=" ").strip()
    if " - " not in text: continue
    parts = text.split(" - ")
    if len(parts) != 2: continue
    local, visitante = parts[0].strip(), parts[1].strip()
    
    mid = f"{local}-{visitante}"
    if mid in seen: continue
    seen.add(mid)
    
    lok, vok, lnorm, vnorm = is_spanish_match(local, visitante)
    if not (lok and vok):
        print(f"REJECTED: {local} ({lnorm}) vs {visitante} ({vnorm}) -> L_OK={lok} V_OK={vok}")
    else:
        print(f"ACCEPTED: {local} vs {visitante}")
