
import gspread
import os
import json
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Load env explicitly if needed, but we used credentials.json directly here
load_dotenv(os.path.join(BASE_DIR, ".env"))

def reset_sheets():
    print("Resetting Sheets...")
    creds_path = os.path.join(BASE_DIR, "credentials.json")
    if not os.path.exists(creds_path):
        print("No credentials found!")
        return

    gc = gspread.service_account(filename=creds_path)
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    if not sheet_id:
        print("No SHEET ID found in env!")
        return

    sh = gc.open_by_key(sheet_id)
    
    # Clear Semana_Actual
    try:
        ws_semana = sh.worksheet("Semana_Actual")
        ws_semana.clear()
        ws_semana.append_row([
            "Jornada", "Fecha", "Local", "Visitante", 
            "Pronostico_Logico", "Justificacion_Logica", 
            "Pronostico_Sorpresa", "Justificacion_Sorpresa"
        ])
        print("Semana_Actual cleared.")
    except Exception as e:
        print(f"Error resetting Semana_Actual: {e}")

    # Clear Historial
    try:
        ws_hist = sh.worksheet("Historial")
        ws_hist.clear()
        ws_hist.append_row([
            "Jornada", "Partido", "Local", "Visitante",
            "Pronostico_Logico", "Pronostico_Sorpresa", 
            "Resultado_Real", "Acierto_Logico", "Acierto_Sorpresa", 
            "Feedback_IA"
        ])
        print("Historial cleared.")
    except Exception as e:
        print(f"Error resetting Historial: {e}")

if __name__ == "__main__":
    reset_sheets()
