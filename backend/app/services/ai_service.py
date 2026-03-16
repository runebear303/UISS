import requests
import json
import time
from sqlalchemy.orm import Session
from app.services.logger import log_system_alert

# Configuratie voor jouw Docker setup
OLLAMA_URL = "http://ollama:11434/api/generate"
MODEL_NAME = "tinyllama"

def ask_ai_with_sources(db: Session, vraag: str, conversation_id: int = None):
    start_time = time.time()
    
    # 1. RAG Logica: Haal relevante documenten op (Simpel voorbeeld)
    # Hier kun je later je vector-search logica (ChromaDB/FAISS) plaatsen
    context = "Gebruik de UNASAT reglementen om deze vraag te beantwoorden."

    # 2. Payload voor Ollama
    payload = {
        "model": MODEL_NAME,
        "prompt": f"Context: {context}\n\nGebruiker: {vraag}\n\nAssistent:",
        "stream": False
    }

    try:
        # Verbinding maken met de Ollama container
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        result_json = response.json()
        answer = result_json.get("response", "Ik kon geen antwoord genereren.")
        
        latency = int((time.time() - start_time) * 1000)

        return {
            "answer": answer,
            "conversation_id": conversation_id,
            "provider": "local_ollama",
            "latency_ms": latency,
            "usage": {"total_tokens": len(answer.split()) + len(vraag.split())}, # Schatting
            "cost": 0.0  # Lokaal is gratis!
        }

    except requests.exceptions.RequestException as e:
        # Als Ollama niet bereikbaar is, loggen we dit
        error_msg = f"Ollama Connection Error: {str(e)}"
        print(error_msg)
        log_system_alert(db, "CRITICAL", error_msg, module="llm_service")
        
        return {
            "answer": "Systeemfout: De lokale AI (Ollama) is momenteel niet bereikbaar.",
            "conversation_id": conversation_id,
            "provider": "error",
            "latency_ms": 0
        }
