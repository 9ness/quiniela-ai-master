import os
import argparse
import sys
from datetime import datetime
from dotenv import load_dotenv

# Asegurar que podemos importar desde src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import setup_logger
from src.services import sheets, scraper, gemini

# Cargar variables de entorno (buscando en root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

logger = setup_logger()

def run_friday_flow(client, sheet_id, model):
    """Orquesta el flujo: Validar Pasado -> Limpiar -> Scrapear Futuro -> Predecir -> Guardar."""
    logger.info(">>> INICIANDO ORQUESTACION <<<")
    
    ws_semana = sheets.get_worksheet(client, sheet_id, "Semana_Actual")
    ws_historial = sheets.get_worksheet(client, sheet_id, "Historial")
    
    # --- PASO 1: VALIDAR Y MOVER A HISTORIAL ---
    current_data = ws_semana.get_all_records()
    if current_data:
        logger.info(f"Validando {len(current_data)} partidos anteriores...")
        real_results = scraper.get_previous_results()
        
        # Mapa de resultados reales
        results_map = {}
        for r in real_results:
            key = f"{scraper.normalize_name(r['local'])}-{scraper.normalize_name(r['visitante'])}"
            results_map[key] = r['resultado_real']
            
        rows_to_history = []
        for i, row in enumerate(current_data):
            key = f"{scraper.normalize_name(row['Local'])}-{scraper.normalize_name(row['Visitante'])}"
            real_res = results_map.get(key, "?")
            
            p_log = str(row['Pronostico_Logico']).upper().strip()
            p_sor = str(row['Pronostico_Sorpresa']).upper().strip()
            
            is_hit_log = (p_log == real_res) if real_res != "?" else False
            is_hit_sor = (p_sor == real_res) if real_res != "?" else False
            
            feedback = "Pendiente"
            if real_res != "?":
                feedback = "Acierto Lógico" if is_hit_log else ("Acierto Sorpresa" if is_hit_sor else "Fallo")
                
            rows_to_history.append([
                row['Jornada'], row.get('Partido', i+1), row['Local'], row['Visitante'],
                p_log, p_sor, real_res,
                "TRUE" if is_hit_log else "FALSE",
                "TRUE" if is_hit_sor else "FALSE",
                feedback
            ])
            
        if rows_to_history:
            ws_historial.append_rows(rows_to_history)
            logger.info(f"Archivadas {len(rows_to_history)} filas en Historial.")
            
        ws_semana.clear()
        ws_semana.append_row([
            "Jornada", "Fecha", "Local", "Visitante", 
            "Pronostico_Logico", "Justificacion_Logica", 
            "Pronostico_Sorpresa", "Justificacion_Sorpresa"
        ])
    else:
        logger.info("Semana_Actual vacía, saltando validación.")

    # --- PASO 2: OBTENER NUEVOS PARTIDOS ---
    logger.info("Obteniendo partidos próxima jornada...")
    next_matches = scraper.get_next_week_matches()
    
    if not next_matches:
        logger.warning("No se encontraron partidos válidos o aptos.")
        return

    # Verificar duplicados (si la hoja no estaba vacía o se re-llenó)
    existing = ws_semana.get_all_records()
    if existing:
        first_ex = existing[0]
        first_new = next_matches[0]
        if (scraper.normalize_name(first_ex['Local']) == scraper.normalize_name(first_new['local']) and
            scraper.normalize_name(first_ex['Visitante']) == scraper.normalize_name(first_new['visitante'])):
            logger.warning("DETENIDO: Datos duplicados detectados en Semana_Actual.")
            return

    # --- PASO 3: IA PREDICCION ---
    predictions = gemini.generate_predictions(model, next_matches)
    if not predictions:
        logger.error("No se recibieron predicciones de Gemini.")
        return

    # --- PASO 4: GUARDAR ---
    logger.info("Guardando predicciones...")
    
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
    # Indexar predicciones por 'partido' id
    pred_map = {p.get("partido"): p for p in predictions}
    
    for i, match in enumerate(next_matches):
        # Intentar match por ID, fallback por índice
        p = pred_map.get(match["partido"])
        if not p and i < len(predictions):
            p = predictions[i] # Fallback posicional
            
        if not p: p = {}
        
        final_rows.append([
            new_jornada, today, match["local"], match["visitante"],
            p.get("pronostico_logico", "?"), p.get("justificacion_logica", ""),
            p.get("pronostico_sorpresa", "?"), p.get("justificacion_sorpresa", "")
        ])
        
    ws_semana.append_rows(final_rows)
    logger.info("¡Flujo completado exitosamente!")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["AUTO", "MANUAL_PREDICT"], default="MANUAL_PREDICT")
    args = parser.parse_args()
    
    try:
        sheet_id = os.environ.get("GOOGLE_SHEET_ID")
        if not sheet_id:
            raise ValueError("GOOGLE_SHEET_ID no definido en .env")
            
        client = sheets.get_client()
        model = gemini.configure_gemini()
        
        if args.mode == "MANUAL_PREDICT" or args.mode == "AUTO":
            run_friday_flow(client, sheet_id, model)
            
    except Exception as e:
        logger.critical(f"Error Fatal en Main: {e}")
        raise

if __name__ == "__main__":
    main()
