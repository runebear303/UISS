import requests
import json
import time
from sqlalchemy.orm import Session
from app.services.logger import log_system_alert

# CORRECTE CONFIGURATIE VOOR JOUW SETUP
# De hostname moet 'uiss_ollama' zijn, omdat dat je container_name is.
OLLAMA_URL = "http://uiss_ollama:11434/api/generate"
MODEL_NAME = "tinyllama:latest"

def ask_ai_with_sources(db: Session, vraag: str, conversation_id: int = None):
    start_time = time.time()
    
    # Tijdelijke context (wordt later RAG)
    context = "Je bent een assistent voor UNASAT studenten. Beantwoord de vraag kort en bondig."

    payload = {
        "model": MODEL_NAME,
        "prompt": f"<|system|>\n{context}</s>\n<|user|>\n{vraag}</s>\n<|assistant|>\n",
        "stream": False
    }

    try:
        # Debug print om te zien in de logs wat we doen
        print(f"DEBUG: Poging tot verbinden met {OLLAMA_URL}...")
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=45)
        response.raise_for_status()
        
        result_json = response.json()
        answer = result_json.get("response", "Ik kon geen antwoord genereren.")
        
        latency = int((time.time() - start_time) * 1000)
        print(f"DEBUG: Succes! Antwoord: {answer[:30]}...")

        return {
            "answer": answer,
            "conversation_id": conversation_id,
            "provider": "local_ollama",
            "latency_ms": latency,
            "usage": {"total_tokens": len(answer.split())},
            "cost": 0.0
        }

    except requests.exceptions.RequestException as e:
        error_msg = f"Ollama Connection Error: {str(e)}"
        print(f"DEBUG ERROR: {error_msg}") # Dit zie je in 'docker logs uiss_backend'
        log_system_alert(db, "CRITICAL", error_msg, module="llm_service")
        
        return {
            "answer": "Systeemfout: De lokale AI (uiss_ollama) is niet bereikbaar.",
            "conversation_id": conversation_id,
            "provider": "error",
            "latency_ms": 0
        }
