import json
import os

try:
    with open('backend/credentials.json', 'r') as f:
        data = json.load(f)
        print(json.dumps(data))
except Exception as e:
    print(f"Error: {e}")
