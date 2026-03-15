import os
from pathlib import Path
from dotenv import load_dotenv

# =========================================
# SELECT ENV FILE
# =========================================
# base directory = backend folder
BASE_DIR = Path(__file__).resolve().parent.parent

# kies environment
ENV = os.getenv("ENV", "local")

# laad juiste env file
if ENV == "docker":
    env_file = BASE_DIR / ".env.docker"
else:
    env_file = BASE_DIR / ".env.local"

load_dotenv(env_file)

print("Loaded ENV file:", env_file)
print("SECRET_KEY:", os.getenv("SECRET_KEY"))


# =========================================
# BASE DIRECTORIES
# =========================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
FAISS_DIR = DATA_DIR / "faiss_index"
SOURCE_DOCS_DIR = DATA_DIR / "source_docs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
FAISS_DIR.mkdir(parents=True, exist_ok=True)
SOURCE_DOCS_DIR.mkdir(parents=True, exist_ok=True)


# =========================================
# SYSTEM INFO
# =========================================

SYSTEM_NAME = os.getenv("SYSTEM_NAME", "UNASAT Intelligent Support System")
SYSTEM_SHORT = os.getenv("SYSTEM_SHORT", "UISS")

APP_VERSION = "1.0.0"


# =========================================
# LOGGING
# =========================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# =========================================
# SECURITY
# =========================================

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set")

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")


# =========================================
# INPUT LIMITS
# =========================================

MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", 2000))


# =========================================
# LLM PROVIDER
# =========================================

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

MODEL_PROFILE = os.getenv("MODEL_PROFILE", "local")  
# local | cloud


# =========================================
# LOCAL MODEL (OLLAMA)
# =========================================

LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "tinyllama:latest")

DEFAULT_OLLAMA_URL = "http://ollama:11434/api/generate"

if ENV == "local":
    DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"

OLLAMA_URL = os.getenv("OLLAMA_URL", DEFAULT_OLLAMA_URL)


# =========================================
# CLOUD MODEL
# =========================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CLOUD_MODEL_NAME = os.getenv(
    "CLOUD_MODEL_NAME",
    "gpt-4o-mini"
)

CLOUD_SIMULATION = os.getenv("CLOUD_SIMULATION", "false").lower() == "true"

if MODEL_PROFILE == "cloud" and not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY must be set when using cloud models")


# =========================================
# VECTOR DATABASE
# =========================================

VECTOR_DB = os.getenv("VECTOR_DB", "faiss")

FAISS_PATH = FAISS_DIR / "index.faiss"


# =========================================
# DATABASE (MYSQL)
# =========================================

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "uiss_user")
DB_PASS = os.getenv("DB_PASS", "uiss_password")
DB_NAME = os.getenv("DB_NAME", "uiss_db")

MYSQL_CONFIG = {
    "host": DB_HOST,
    "port": DB_PORT,
    "user": DB_USER,
    "password": DB_PASS,
    "database": DB_NAME
}


# =========================================
# MONITORING
# =========================================

CPU_ALERT_THRESHOLD = int(os.getenv("CPU_ALERT_THRESHOLD", 90))
RAM_ALERT_THRESHOLD = int(os.getenv("RAM_ALERT_THRESHOLD", 90))
DISK_ALERT_THRESHOLD = int(os.getenv("DISK_ALERT_THRESHOLD", 90))


# =========================================
# RAG CONFIG
# =========================================

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))

TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", 5))