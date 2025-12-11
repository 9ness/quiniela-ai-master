import requests
from bs4 import BeautifulSoup
import logging
import re
import unicodedata

# Config
BASE_URL = "https://www.resultados-futbol.com/quiniela"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Lista blanca aproximada de equipos Españoles (1a y 2a) para filtrado
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
    """Normaliza nombres de equipos para comparación (minusculas, sin tildes)."""
    if not name: return ""
    name = str(name).lower()
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    return name.strip()

def is_spanish_match(local, visitante):
    """Verifica si ambos equipos parecen ser españoles."""
    l_norm = normalize_name(local)
    v_norm = normalize_name(visitante)
    
    # Comprobar si contienen palabras clave de equipos españoles
    is_local_ok = any(k in l_norm for k in SPANISH_TEAMS_KEYWORDS)
    is_visit_ok = any(k in v_norm for k in SPANISH_TEAMS_KEYWORDS)
    
    return is_local_ok and is_visit_ok

def parse_matches_from_html(soup):
    """Extrae partidos de la tabla de quiniela."""
    matches = []
    # Buscar filas de partidos. En r-f.com suelen estar en tablas con clases específicas o listas
    # Analizando la estructura típica: suelen ser links con formato "Local - Visitante"
    # Buscamos divs o trs que contengan info del partido
    
    # Estrategia general: buscar todos los links que parezcan partidos dentro del contenedor principal
    # El contenedor suele ser #quiniela
    container = soup.select_one(".boxcontent") # Clase genérica, ajustaremos
    
    # Si no encontramos por clase específica, buscamos por patrón en links
    links = soup.find_all("a", href=re.compile(r"/partido/"))
    
    seen_matches = set()
    
    for i, link in enumerate(links):
        if len(matches) >= 15: break
        
        text = link.get_text(separator=" ").strip()
        if " - " not in text: continue
        
        parts = text.split(" - ")
        if len(parts) != 2: continue
        
        local, visitante = parts[0].strip(), parts[1].strip()
        
        # Evitar duplicados (a veces el mismo link aparece 2 veces)
        match_id = f"{local}-{visitante}"
        if match_id in seen_matches: continue
        seen_matches.add(match_id)
        
        matches.append({
            "partido": len(matches) + 1,
            "local": local,
            "visitante": visitante,
            "url": link.get("href")
        })
        
    return matches

def get_next_week_matches():
    """Busca la última (o próxima) quiniela válida de equipos españoles."""
    current_url = BASE_URL
    max_attempts = 5 # Buscar hasta 5 jornadas atrás
    
    logging.info(f"Buscando próxima quiniela de La Liga (Max intentos: {max_attempts})...")
    
    for attempt in range(max_attempts):
        logging.info(f"Analizando URL: {current_url}")
        try:
            resp = requests.get(current_url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "lxml")
            
            matches = parse_matches_from_html(soup)
            
            if matches:
                # Verificar si es válida (equipos españoles)
                # Comprobamos la mayoría o todos? La regla dice "Si detectas... aborta".
                # Aquí verificamos si CUMPLE. Si no cumple, buscamos anterior.
                
                is_valid_journey = True
                for m in matches:
                    if not is_spanish_match(m["local"], m["visitante"]):
                        is_valid_journey = False
                        break
                
                if is_valid_journey:
                    logging.info(f"¡Jornada Válida encontrada en intento {attempt+1}!")
                    return matches
                else:
                    logging.warning(f"Jornada descartada (Intl/Champions). Buscando anterior...")
            
            # Estrategia robusta para encontrar el link "Anterior"
            prev_link = None
            
            # 1. Buscar por texto flexible (ignorando case y caracteres extraños)
            all_links = soup.find_all("a", href=True)
            for link in all_links:
                txt = link.get_text().lower()
                if "anterior" in txt:
                    prev_link = link
                    break
            
            # 2. Si falla, buscar por patrón de URL de histórico (común en r-f.com)
            # e.g. /quiniela/historico/26
            if not prev_link:
                for link in all_links:
                    if "/quiniela/historico/" in link["href"]:
                        # Asumimos que si estamos en la 27, el histórico 26 es la anterior
                        # Esto es una heurística por si falla el texto
                        prev_link = link
                        # No break inmediato, idealmente querríamos el ID más alto menor al actual
                        # Pero por simplicidad tomamos el primero que suele ser el de navegación
                        break

            if not prev_link:
                logging.error("No se encontró enlace 'Anterior'. Deteniendo búsqueda.")
                return None
                
            prev_url = prev_link.get("href")
            if not prev_url.startswith("http"):
                prev_url = "https://www.resultados-futbol.com" + prev_url
            
            current_url = prev_url
            
        except Exception as e:
            logging.error(f"Error en iteración de scraping: {e}")
            return None

    logging.error("No se encontró ninguna jornada válida tras varios intentos.")
    return None

def get_previous_results():
    """Obtiene resultados de la jornada ANTERIOR."""
    try:
        # 1. Ir a la home de quiniela para buscar link "Anterior"
        resp = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.content, "lxml")
        
        prev_link = soup.find("a", string=re.compile(r"Anterior", re.I))
        if not prev_link:
            logging.warning("No se encontró enlace a jornada anterior.")
            return []
            
        prev_url = prev_link.get("href")
        if not prev_url.startswith("http"):
            prev_url = "https://www.resultados-futbol.com" + prev_url
            
        logging.info(f"Haciendo scraping de jornada anterior: {prev_url}")
        
        resp_prev = requests.get(prev_url, headers=HEADERS, timeout=10)
        soup_prev = BeautifulSoup(resp_prev.content, "lxml")
        
        # En la página de histórico, los resultados (1 X 2) suelen estar marcados
        # Buscamos la tabla de resultados
        # Fila típica: Local - Visitante ... Resultado (color/texto)
        
        results = []
        # Reutilizamos logica de buscar partidos pero ahora necesitamos el signo
        # En r-f.com historico, suele haber una tabla con clase 'quiniela' 
        # y celdas con clase 'resultado' o checkmarks
        
        rows = soup_prev.select("table.quiniela tr")
        if not rows:
             # Fallback a buscar divs
             rows = soup_prev.select("tr")

        for row in rows:
            # Extraer equipos
            links = row.find_all("a", href=re.compile(r"/partido/"))
            if not links: continue
            
            # Asumimos que el link tiene "Local - Visitante"
            match_link = links[0]
            if " - " not in match_link.text: continue
            
            local, visitante = match_link.text.split(" - ")
            local, visitante = local.strip(), visitante.strip()
            
            # Extraer signo (1 X 2)
            # Buscamos celda activa o texto de resultado
            # A menudo hay celdas td con contenido "1", "X", "2", y una clase "acierto" o "ganador"
            signo = "?"
            tds = row.find_all("td")
            
            # Intento heurístico: buscar celda coloreada o con clase especial
            real_res = None
            
            # Buscar texto de resultado explícito (e.g. "2-1") para calcular signo
            score_text = row.get_text()
            # Simple regex para 1-0, 2-2 etc? Es arriesgado.
            
            # Mejor: en la web de quiniela, suelen marcar el signo ganador en una columna específica (1, X, 2)
            # Iterar celdas 1, X, 2
            cols = row.select(".col_1, .col_x, .col_2") # Clases hipotéticas
            # Si r-f usa estructura estándar, las columnas de pronóstico tienen clases.
            # Al no poder ver el HTML exacto en runtime sin muchas tools, haremos un scraping genérico de resultado
            # Si no podemos determinarlo fiable, dejaremos "?"
            
            # PLAN B: Usar el marcador numérico si está visible
            # E.g. buscar un string como "2 - 1" cerca de los equipos
            # Si encontramos 2-1 -> 1. 
            
            score_match = re.search(r"(\d+)\s*-\s*(\d+)", row.get_text())
            if score_match:
                g_loc = int(score_match.group(1))
                g_vis = int(score_match.group(2))
                if g_loc > g_vis: real_res = "1"
                elif g_loc < g_vis: real_res = "2"
                else: real_res = "X"
            
            if real_res:
                results.append({
                    "local": local,
                    "visitante": visitante,
                    "resultado_real": real_res
                })
                
        return results

    except Exception as e:
        logging.error(f"Error scraping anterior: {e}")
        return []
