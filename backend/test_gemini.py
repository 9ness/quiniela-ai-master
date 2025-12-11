
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv("backend/.env")

api_key = os.environ.get("GOOGLE_API_KEY")
print(f"API Key found: {bool(api_key)}")

try:
    genai.configure(api_key=api_key)
    model_name = 'models/gemini-1.5-flash'
    print(f"Using model: {model_name}")
    model = genai.GenerativeModel(model_name)
    print("Model initialized. Generating content...")
    
    response = model.generate_content("Hello, can you predict a football match result?")
    print("Response received!")
    print(response.text)
    
except Exception as e:
    print(f"ERROR: {e}")
