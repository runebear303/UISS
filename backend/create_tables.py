from app.database.db import engine, Base
# You MUST import the models file so SQLAlchemy 'sees' the classes
from app import models 

def init_db():
    print("Connecting to MySQL and creating tables...")
    try:
        # This command finds all classes inheriting from Base in models.py
        Base.metadata.create_all(bind=engine)
        print("✅ Success! Your tables (chat_logs, messages, etc.) are now in the DB.")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

if __name__ == "__main__":
    init_db()