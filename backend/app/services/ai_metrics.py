import time
import threading

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
        """Thread-safe logging of a successful query."""
        with cls._lock:
            cls._queries += 1
            cls._documents += docs_count
            cls._total_time += response_time

    @classmethod
    def log_error(cls):
        """Thread-safe logging of a system error."""
        with cls._lock:
            cls._errors += 1

    @classmethod
    def reset(cls):
        """Resets all metrics to zero (useful for testing)."""
        with cls._lock:
            cls._queries = 0
            cls._errors = 0
            cls._documents = 0
            cls._total_time = 0

    @classmethod
    def get_metrics(cls):
        """Returns the current metrics as a dictionary."""
        with cls._lock:
            avg_response = 0
            if cls._queries > 0:
                avg_response = cls._total_time / cls._queries

            return {
                "queries": cls._queries,
                "errors": cls._errors,
                "documents_retrieved": cls._documents,
                "avg_response_time": round(avg_response, 3),
                "timestamp": time.time() # Added timestamp for the frontend
            }

# Helper function to use in routes.py
def get_ai_metrics():
    return AIMetrics.get_metrics()