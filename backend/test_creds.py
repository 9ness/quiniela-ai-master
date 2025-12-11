
import gspread
import os
import json
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
creds_path = os.path.join(BASE_DIR, "credentials.json")
load_dotenv(os.path.join(BASE_DIR, ".env"))

print(f"Loading creds from: {creds_path}")
try:
    gc = gspread.service_account(filename=creds_path)
    print("Auth successful!")
    
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    print(f"Accessing Sheet ID: {sheet_id}")
    
    sh = gc.open_by_key(sheet_id)
    print(f"Sheet Title: {sh.title}")
    
    ws = sh.worksheet("Semana_Actual")
    print("Existing values:", ws.get_all_values())
    
except Exception as e:
    print(f"ERROR: {e}")
