import os
import json
import logging
import google.generativeai as genai

logger = logging.getLogger()

def configure_gemini():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY no encontrada en variables de entorno.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-pro', generation_config={"response_mime_type": "application/json"})

def generate_predictions(model, matches):
    """Genera predicciones usando Gemini 2.5 Pro."""
    prompt = f"""
    Eres un experto en probabilidad deportiva y fútbol español (La Liga).
    Para los siguientes partidos, genera dos predicciones:
    
    1. Lógica: El resultado más probable matemáticamente.
    2. Sorpresa: Un resultado plausible pero arriesgado (para buscar valor).

    Devuelve ÚNICAMENTE un JSON válido con la siguiente estructura (lista de objetos):
    [
      {{
        "partido": ID_PARTIDO,
        "pronostico_logico": "1", "X" o "2",
        "justificacion_logica": "Breve explicación...",
        "pronostico_sorpresa": "1", "X" o "2",
        "justificacion_sorpresa": "Breve explicación..."
      }}
    ]

    PARTIDOS A ANALIZAR:
    {json.dumps(matches, indent=2)}
    """
    
    try:
        logger.info("Enviando prompt a Gemini...")
        response = model.generate_content(prompt)
        text = response.text
        # Limpieza básica por si el modelo incluye markdown
        if "```json" in text:
            text = text.replace("```json", "").replace("```", "")
        
        return json.loads(text)
    except Exception as e:
        logger.error(f"Error generando predicciones con Gemini: {e}")
        return []
