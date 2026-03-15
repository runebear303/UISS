import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import MYSQL_CONFIG


DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_CONFIG['user']}:"
    f"{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}:"
    f"{MYSQL_CONFIG.get('port',3306)}/"
    f"{MYSQL_CONFIG['database']}"
)

engine = create_engine(
      DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

def wait_for_db(engine, retries=10, interval=3):
    """Wacht tot MySQL echt klaar is voor verbinding."""
    print("⏳ Controleren op database verbinding...")
    for i in range(retries):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                print("✅ Database verbinding succesvol!")
                return True
        except Exception:
            print(f"⚠️ Database nog niet bereikbaar... Poging {i+1}/{retries}")
            time.sleep(interval)
    raise RuntimeError("❌ MySQL niet bereikbaar na meerdere pogingen.")

# Voer de check direct uit bij het laden van dit script
wait_for_db(engine)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# FastAPI dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()