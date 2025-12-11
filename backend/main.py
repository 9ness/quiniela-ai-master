import os
import json
import gspread
import pandas as pd
import google.generativeai as genai
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import logging

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_credentials():
    """Obtiene credenciales de Google Sheets desde variable de entorno o archivo."""
    creds_json = os.environ.get("G_SHEETS_CREDENTIALS")
    if creds_json:
        try:
            creds_dict = json.loads(creds_json)
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            return ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        except json.JSONDecodeError as e:
            logging.error(f"Error al decodificar credenciales JSON: {e}")
            raise
    elif os.path.exists("credentials.json"):
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        return ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    else:
        raise FileNotFoundError("No se encontraron credenciales de Google Sheets (G_SHEETS_CREDENTIALS o credentials.json)")

def main():
    try:
        logging.info("Iniciando proceso de Quiniela AI...")
        
        # 1. Autenticación Google Sheets
        creds = get_credentials()
        client = gspread.authorize(creds)
        
        # Abrir Sheet por ID (Más seguro y robusto)
        sheet_id = os.environ.get("GOOGLE_SHEET_ID")
        if not sheet_id:
            raise ValueError("Falta la variable de entorno GOOGLE_SHEET_ID")

        try:
            sh = client.open_by_key(sheet_id)
        except gspread.SpreadsheetNotFound:
            logging.error(f"No se encontró el Google Sheet con ID: {sheet_id}")
            return

        # 2. Leer Historial (Últimas 5 jornadas)
        worksheet_historial = sh.worksheet("Historial")
        data = worksheet_historial.get_all_records()
        df = pd.DataFrame(data)
        
        # Asumimos que el historial tiene columnas como 'Jornada', 'Partido_1', 'Resultado_1', etc.
        last_5_games = df.tail(5).to_dict(orient='records')
        logging.info(f"Leídos {len(last_5_games)} registros históricos.")

        # 3. Configurar Gemini
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Falta la variable de entorno GOOGLE_API_KEY")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')

        # 4. Generar Prompt
        context_str = json.dumps(last_5_games, indent=2, ensure_ascii=False)
        
        prompt = f"""
        Actúa como un experto analista de fútbol español (La Quiniela).
        
        Aquí tienes los resultados de las últimas 5 jornadas para que entiendas las tendencias:
        {context_str}
        
        Tu tarea es:
        1. Analizar la jornada actual (que no te he pasado, asume que debes predecir una genérica o dame un formato estándar si no tienes los partidos específicos, pero idealmente el usuario debería proveer los partidos de la semana. ASUMIREMOS QUE LA TAREA ES GENERAR UNA PREDICCIÓN BASADA EN PATRONES GENERALES O DATOS SIMULADOS SI NO HAY INPUT DE PARTIDOS).
        
        NOTA CRÍTICA: Como este script es automático, vamos a asumir que necesitas generar una predicción para 15 partidos (formato estándar Quiniela).
        
        Genera una predicción para 15 partidos en formato JSON estricto:
        [
            {{"partido": 1, "local": "Equipo A", "visitante": "Equipo B", "pronostico": "1", "razonamiento": "..."}},
            ...
        ]
        """
        # Nota: En un caso real, deberíamos leer los partidos de la semana actual de otra hoja o API.
        # Aquí simplificamos pidiendo a Gemini que razone o "simule" si no hay datos de entrada de los partidos.
        # MEJORA: Leer partidos de la hoja 'Proxima_Jornada' si existe. 
        # Vamos a intentar leer de 'Proxima_Jornada' si existe, si no, prompt genérico.
        
        try:
            worksheet_proxima = sh.worksheet("Proxima_Jornada")
            proxima_jornada_data = worksheet_proxima.get_all_records()
            matches_str = json.dumps(proxima_jornada_data, ensure_ascii=False)
            prompt += f"\n\nPartidos de esta semana:\n{matches_str}\n\nGenera los pronósticos para estos partidos."
        except gspread.WorksheetNotFound:
            logging.warning("No se encontró hoja 'Proxima_Jornada'. Gemini intentará deducir o simular.")

        logging.info("Consultando a Gemini...")
        response = model.generate_content(prompt)
        text_response = response.text
        
        # Limpieza básica de markdown JSON
        if "```json" in text_response:
            text_response = text_response.replace("```json", "").replace("```", "")
        
        try:
            predictions = json.loads(text_response)
        except json.JSONDecodeError:
            logging.error("Gemini no devolvió un JSON válido. Respuesta raw:")
            logging.error(text_response)
            return

        # 5. Escribir en 'Semana_Actual'
        try:
            worksheet_semana = sh.worksheet("Semana_Actual")
            worksheet_semana.clear()
        except gspread.WorksheetNotFound:
            worksheet_semana = sh.add_worksheet(title="Semana_Actual", rows=20, cols=5)
        
        # Headers
        headers = ["Partido", "Local", "Visitante", "Pronostico", "Razonamiento"]
        worksheet_semana.append_row(headers)
        
        rows_to_write = []
        for pred in predictions:
            rows_to_write.append([
                pred.get("partido"),
                pred.get("local", "N/A"),
                pred.get("visitante", "N/A"),
                pred.get("pronostico"),
                pred.get("razonamiento")
            ])
            
        worksheet_semana.append_rows(rows_to_write)
        
        # Actualizar fecha de actualización
        worksheet_semana.update_acell("G1", f"Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        logging.info("Predicciones guardadas exitosamente en 'Semana_Actual'.")

    except Exception as e:
        logging.error(f"Error crítico en el proceso: {e}")
        raise

if __name__ == "__main__":
    main()
