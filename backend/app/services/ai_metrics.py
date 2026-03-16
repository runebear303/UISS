import time
import threading
from app.database.db import SessionLocal
from app.database.model import LLMLog
class AIMetrics:
    # Class-level variables for tracking
    _queries = 0
    _errors = 0
    _documents = 0
    _total_time = 0
    
    # A lock to ensure thread-safety during updates
    _lock = threading.Lock()
    @classmethod
    def log_query(cls, docs_count: int, response_time: float):
        """Slaat de latency en metrics op in de database voor het dashboard."""
        with cls._lock:
            db = SessionLocal()
            try:
                # Maak een nieuw log-item aan in de database
                new_log = LLMLog(
                    prompt_length=0, # Je kunt hier evt len(user_query) meegeven
                    response_time=response_time,
                    docs_retrieved=docs_count,
                    status="SUCCESS"
                )
                db.add(new_log)
                db.commit()
            except Exception as e:
                print(f"❌ Database Log Fout: {e}")
                db.rollback()
            finally:
                db.close()

    @classmethod
    def log_error(cls):
        """Registreert een fout in de database."""
        db = SessionLocal()
        try:
            new_log = LLMLog(status="ERROR", response_time=0, docs_retrieved=0)
            db.add(new_log)
            db.commit()
        except Exception as e:
            print(f"❌ Database Error Log Fout: {e}")
        finally:
            db.close()
   
    