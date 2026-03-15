import requests
import mysql.connector
import os

def check_connections():
    print("🚀 Start UISS Systeem Check...\n")

    # 1. Check Database (MySQL)
    print("🔍 1. Database verbinding testen...")
    try:
        conn = mysql.connector.connect(
            host="localhost", # Gebruik localhost als je dit vanaf je desktop draait
            port=3306,
            user="uiss_user",
            password="uiss_password",
            database="uiss_db"
        )
        print("✅ MySQL is bereikbaar!")
        conn.close()
    except Exception as e:
        print(f"❌ MySQL Fout: {e}")

    # 2. Check Backend (FastAPI)
    print("\n🔍 2. Backend API testen...")
    try:
        response = requests.get("http://localhost:8000/docs")
        if response.status_code == 200:
            print("✅ Backend draait en Swagger docs zijn online!")
    except Exception as e:
        print(f"❌ Backend Fout: Is uiss_backend gestart?")

    # 3. Check Ollama (AI)
    print("\n🔍 3. Ollama AI Service testen...")
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = [m['name'] for m in response.json().get('models', [])]
            print(f"✅ Ollama is online! Beschikbare modellen: {models}")
            if 'tinyllama:latest' not in models:
                print("⚠️  Waarschuwing: TinyLlama is nog niet gedownload.")
    except Exception as e:
        print(f"❌ Ollama Fout: Is uiss_ollama gestart?")

if __name__ == "__main__":
    check_connections()