import os
import json
import argparse
import logging
import gspread
import pandas as pd
import google.generativeai as genai
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from scraper import get_next_week_matches, get_previous_results, normalize_name
from dotenv import load_dotenv

# Cargar variables de entorno locales (buscando en el mismo directorio del script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_credentials():
    """Obtiene credenciales de Google Sheets desde variable de entorno o archivo."""
    # 1. Intentar archivo local primero (más robusto)
    creds_path = os.path.join(BASE_DIR, "credentials.json")
    if os.path.exists(creds_path):
        logging.info(f"Usando credentials.json local: {creds_path}")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        return ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)

    # 2. Intentar Variable de Entorno
    creds_json = os.environ.get("G_SHEETS_CREDENTIALS")
    if creds_json:
        try:
            creds_dict = json.loads(creds_json)
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            return ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        except Exception as e:
            logging.error(f"Error ENV: {e}")
            pass
            
    raise FileNotFoundError("No se encontraron credenciales válidas ni en archivo ni en ENV.")

def setup_sheets(sh):
    """Asegura que las hojas existan con las cabeceras correctas."""
    # SEMANA ACTUAL
    try:
        ws_semana = sh.worksheet("Semana_Actual")
    except gspread.WorksheetNotFound:
        ws_semana = sh.add_worksheet(title="Semana_Actual", rows=20, cols=8)
        ws_semana.append_row([
            "Jornada", "Fecha", "Local", "Visitante", 
            "Pronostico_Logico", "Justificacion_Logica", 
            "Pronostico_Sorpresa", "Justificacion_Sorpresa"
        ])

    # HISTORIAL
    try:
        ws_historial = sh.worksheet("Historial")
    except gspread.WorksheetNotFound:
        ws_historial = sh.add_worksheet(title="Historial", rows=100, cols=10) # +1 col Feedback
        ws_historial.append_row([
            "Jornada", "Partido", "Local", "Visitante",
            "Pronostico_Logico", "Pronostico_Sorpresa", 
            "Resultado_Real", "Acierto_Logico", "Acierto_Sorpresa", 
            "Feedback_IA"
        ])
    
    return ws_semana, ws_historial

def run_friday_flow(sh, ws_semana, ws_historial, model):
    """Flujo Estricto de Viernes (Rotación)"""
    logging.info(">>> INICIANDO FLUJO DE VIERNES <<<")
    
    # --- PASO A: VALIDAR PASADO ---
    current_data = ws_semana.get_all_records()
    
    if current_data:
        logging.info(f"Paso A: Validando {len(current_data)} partidos de la semana anterior...")
        real_results = get_previous_results()
        
        # Mapa de resultados para búsqueda rápida
        # Clave: LocalNormalizado-VisitanteNormalizado
        results_map = {}
        for r in real_results:
            key = f"{normalize_name(r['local'])}-{normalize_name(r['visitante'])}"
            results_map[key] = r['resultado_real']
            
        rows_to_history = []
        
        for i, row in enumerate(current_data):
            # Construir clave
            key = f"{normalize_name(row['Local'])}-{normalize_name(row['Visitante'])}"
            real_res = results_map.get(key, "?") # ? si no se encuentra (partido aplazado o error scraping)
            
            p_log = str(row['Pronostico_Logico']).upper().strip()
            p_sor = str(row['Pronostico_Sorpresa']).upper().strip()
            
            is_hit_log = (p_log == real_res) if real_res != "?" else False
            is_hit_sor = (p_sor == real_res) if real_res != "?" else False
            
            feedback = "Pendiente"
            if real_res != "?":
                feedback = "Acierto Lógico" if is_hit_log else ("Acierto Sorpresa" if is_hit_sor else "Fallo")
            
            rows_to_history.append([
                row['Jornada'],
                row.get('Partido', i+1),
                row['Local'],
                row['Visitante'],
                p_log,
                p_sor,
                real_res,
                "TRUE" if is_hit_log else "FALSE",
                "TRUE" if is_hit_sor else "FALSE",
                feedback
            ])
            
        # Mover a Historial
        if rows_to_history:
            ws_historial.append_rows(rows_to_history)
            logging.info(f"Guardadas {len(rows_to_history)} filas en Historial.")
            
        # Limpiar
        logging.info("Limpiando hoja Semana_Actual...")
        ws_semana.clear()
        ws_semana.append_row([
            "Jornada", "Fecha", "Local", "Visitante", 
            "Pronostico_Logico", "Justificacion_Logica", 
            "Pronostico_Sorpresa", "Justificacion_Sorpresa"
        ])
    else:
        logging.info("Paso A: Semana_Actual vacía, nada que validar.")

    # --- PASO B: PREDECIR FUTURO ---
    logging.info("Paso B: Obteniendo partidos de la próxima jornada...")
    next_matches = get_next_week_matches()
    
    if next_matches is None:
        logging.error("ABORTANDO: Se detectaron equipos no válidos (Champions/Selecciones).")
        return # Abortar
        
    if not next_matches:
        logging.warning("No se encontraron partidos próximos.")
        return

    # CONTROL DE DUPLICADOS
    # Verificar si ya están escritos. Leemos de nuevo por si acaso (aunque acabamos de limpiar)
    # Si acabamos de limpiar, estará vacía. Pero si saltamos Paso A (estaba vacía), ok.
    # SI el usuario ejecuta esto manualmente 2 veces rapidas, la 2a vez la hoja tendra datos.
    # Check simple: ¿La hoja tiene > 1 fila? Si es así, validamos si es la misma jornada.
    
    existing_data = ws_semana.get_all_records()
    if existing_data:
        # Comprobar primer partido
        first_existing = existing_data[0]
        first_new = next_matches[0]
        
        # Comparación laxa
        if (normalize_name(first_existing['Local']) == normalize_name(first_new['local']) and 
            normalize_name(first_existing['Visitante']) == normalize_name(first_new['visitante'])):
            logging.warning("DUPLICADOS: Los partidos de esta jornada ya existen en Semana_Actual. Abortando para no sobrescribir.")
            return

    # GENERAR PREDICCIONES CON GEMINI
    logging.info("Consultando a Gemini 1.5 Flash...")
    
    prompt = f"""
    Eres un experto en probabilidad deportiva. Para los siguientes partidos de La Liga, dame dos predicciones:
    Lógica: El resultado más probable matemáticamente.
    Sorpresa: Un resultado plausible que pagaría bien pero tiene riesgo. 
    Devuelve un JSON estricto.

    PARTIDOS:
    {json.dumps(next_matches, indent=2)}

    FORMATO DE RESPUESTA JSON (Lista de objetos):
    [
      {{
        "partido": 1,
        "pronostico_logico": "1",
        "justificacion_logica": "Breve razón...",
        "pronostico_sorpresa": "X",
        "justificacion_sorpresa": "Breve razón..."
      }},
      ...
    ]
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        if "```json" in text:
            text = text.replace("```json", "").replace("```", "")
        predictions = json.loads(text)
    except Exception as e:
        logging.error(f"Error Gemini: {e}")
        return

    # --- PASO C: ESCRITURA ---
    logging.info("Paso C: Escribiendo nuevas predicciones...")
    
    # Calcular jornada
    hist_data = ws_historial.get_all_records()
    last_jornada = 0
    if hist_data:
        try:
            last_jornada = int(hist_data[-1]["Jornada"])
        except: pass
    new_jornada = last_jornada + 1
    today = datetime.now().strftime("%Y-%m-%d")
    
    final_rows = []
    # Mapear
    pred_map = {p.get("partido"): p for p in predictions} # Por indice partido 1..15
    # OJO: Gemini puede no devolver "partido" ID exacto si no se lo decimos bien, 
    # pero le pasamos los datos con ID. Asumimos que respeta.
    
    # Fallback: asumimos mismo orden si el ID falla
    use_index = False
    if not pred_map: use_index = True 
    
    for i, match in enumerate(next_matches):
        p = pred_map.get(match["partido"]) 
        if not p and use_index and i < len(predictions):
             p = predictions[i]
        if not p: p = {}
             
        final_rows.append([
            new_jornada,
            today,
            match["local"],
            match["visitante"],
            p.get("pronostico_logico", "?"),
            p.get("justificacion_logica", ""),
            p.get("pronostico_sorpresa", "?"),
            p.get("justificacion_sorpresa", "")
        ])

    ws_semana.append_rows(final_rows)
    logging.info("¡Proceso Completado con Éxito!")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["AUTO", "MANUAL_PREDICT"], required=True)
    args = parser.parse_args()

    try:
        creds = get_credentials()
        client = gspread.authorize(creds)
        sheet_id = os.environ.get("GOOGLE_SHEET_ID")
        if not sheet_id: raise ValueError("GOOGLE_SHEET_ID missing")
        sh = client.open_by_key(sheet_id)
        ws_semana, ws_historial = setup_sheets(sh)
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key: raise ValueError("GOOGLE_API_KEY missing")
        genai.configure(api_key=api_key)
        
        # GEMINI 2.5 PRO CONFIG (El más potente disponible según lista usuario)
        model = genai.GenerativeModel('gemini-2.5-pro', generation_config={"response_mime_type": "application/json"})

        if args.mode == "MANUAL_PREDICT":
            # Para manual, usamos el mismo flujo de Viernes para asegurar consistencia
            # OJO: El usuario pidió "no queremos que al desplegar haga llamada manual... necesitamos opcion de ejecutar manual cuando yo quiera"
            # Si quiere FORZAR, quizás quiera saltarse el check de duplicados?
            # "No sobrescribas ni borres nada... para evitar reseteos accidentales si ejecuto el script manualmente"
            # Así que el flujo seguro es el mismo.
            run_friday_flow(sh, ws_semana, ws_historial, model)
            
        elif args.mode == "AUTO":
             run_friday_flow(sh, ws_semana, ws_historial, model)

    except Exception as e:
        logging.critical(f"Error Fatal: {e}")
        raise

if __name__ == "__main__":
    main()
