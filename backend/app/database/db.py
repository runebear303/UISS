from sqlalchemy import create_engine
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