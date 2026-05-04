import os
import json
import logging
import requests

logger = logging.getLogger(__name__)

def analyze_intent_mistral(user_text: str) -> dict:
    """
    Llama a Mistral vía HTTP puro (REST API) para evitar conflictos de librerías.
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        logger.error("Falta MISTRAL_API_KEY en las variables de entorno.")
        return {"intent": "error_configuracion"}

    url = "https://api.mistral.ai/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    system_prompt = """Eres el cerebro de extracción de datos para un bot de WhatsApp de una PyME.
Tu objetivo es analizar el mensaje del usuario y extraer la información en formato JSON.
No inventes datos. Si no menciona algo, usa null.

Debes devolver ÚNICAMENTE un JSON válido con esta estructura exacta:
{
  "intent": "agendar_cita" | "consultar_horario" | "consultar_ubicacion" | "otro",
  "service": "nombre del servicio o null",
  "date": "fecha mencionada o null",
  "time": "hora mencionada o null"
}"""

    payload = {
        "model": "mistral-small-latest",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ],
        "response_format": {"type": "json_object"}
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() # Lanza error si el status no es 200 OK
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        return json.loads(content)

    except Exception as e:
        logger.error(f"Error llamando a Mistral: {e}")
        return {"intent": "desconocido", "error": str(e)}
