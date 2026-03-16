import requests
import time
import csv
from datetime import datetime

# CONFIGURATIE
API_URL = "http://localhost:8000/api/chat"
OUTPUT_FILE = "rag_evaluatie_rapport.csv"

# De 20 testvragen
test_queries = [
    "Wanneer begint het academisch jaar bij UNASAT?",
    "Werkt UNASAT met semesters?",
    "Waar kan ik informatie krijgen over toelatingseisen?",
    "Heeft UNASAT een studentenadministratie?",
    "Waar kunnen studenten terecht voor studiegerelateerde vragen?",
    "Heeft UNASAT een studentenhandleiding?",
    "Heeft UNASAT een orde- en gedragsreglement?",
    "Waar kan ik officiële documenten van UNASAT vinden?",
    "Kan ik UNASAT bezoeken voor informatie?",
    "Heeft UNASAT ICT-gerelateerde opleidingen?",
    "Zijn de opleidingen van UNASAT praktijkgericht?",
    "Is UNASAT gericht op technologie en business?",
    "Hoe kan ik contact opnemen met UNASAT?",
    "Waar kan ik algemene informatie over UNASAT krijgen?",
    "Heeft UNASAT internationale studenten?",
    "Biedt UNASAT ondersteuning aan studenten?",
    "Heeft UNASAT docenten met praktijkervaring?",
    "Wat is het doel van UNASAT?",
    "Wat is het adres van UNASAT?", 
    "Welke software opleidingen zijn er?"
]

def run_evaluation():
    results = []
    print(f"🚀 Start evaluatie van 20 vragen op {API_URL}...")

    for i, query in enumerate(test_queries, 1):
        payload = {
            "question": query,
            "conversation_id": None
        }
        start_time = time.time()
        
        try:
            # Timeout verhoogd naar 120 seconden voor lokale LLM
            response = requests.post(API_URL, json=payload, timeout=120)
            duration = round(time.time() - start_time, 3)
            
            if response.status_code == 200:
                answer = response.json().get("response", "")
                status = "SUCCESS" if "niet gevonden" not in answer.lower() else "NOT_FOUND"
            else:
                status = f"ERROR_{response.status_code}"
                answer = f"Foutcode: {response.text}"
                
        except requests.exceptions.Timeout:
            status = "TIMEOUT"
            duration = 120
            answer = "Server deed er te lang over (Inference latency)"
        except Exception as e:
            status = "CONNECTION_FAIL"
            duration = 0
            answer = str(e)

        results.append({
            "id": i,
            "vraag": query,
            "status": status,
            "latency_sec": duration,
            "antwoord": answer[:100].replace('\n', ' ') + "..."
        })
        
        print(f"[{i}/20] Status: {status} | Tijd: {duration}s")
        
        # Korte pauze om CPU/GPU rust te geven tussen vragen
        time.sleep(1)

    # Opslaan naar CSV
    if results:
        keys = results[0].keys()
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(results)
        print(f"\n✅ Evaluatie voltooid! Resultaten staan in: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_evaluation()