import json
import os

def load_env_file(filepath):
    env_vars = {}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return env_vars

# Load backend env
backend_env = load_env_file('backend/.env')

api_key = backend_env.get('GOOGLE_API_KEY', '')
sheet_id = backend_env.get('GOOGLE_SHEET_ID', '')

# Read credentials
creds_json = ""
try:
    with open('backend/credentials.json', 'r') as f:
        creds_content = json.load(f)
        creds_json = json.dumps(creds_content)
except Exception as e:
    print(f"Error reading credentials: {e}")

# Write frontend .env.local
# Note: JSON inside the string might need escaping if handled by shell, 
# but for .env file usually single quotes work if the value has spaces or special chars.
# However, Next.js dotenv handling might process quotes. 
# Best practice is often to not use quotes unless needed, but for JSON we have quotes inside.
# We will iterate and print it out.
# Let's try to just put it raw if no spaces, but JSON definitely has spaces and quotes.
# We will wrap in single quotes.

content = f"""GOOGLE_API_KEY={api_key}
NEXT_PUBLIC_SHEET_ID={sheet_id}
G_SHEETS_CREDENTIALS='{creds_json}'
"""

with open('frontend/.env.local', 'w', encoding='utf-8') as f:
    f.write(content)

print("frontend/.env.local updated successfully.")
