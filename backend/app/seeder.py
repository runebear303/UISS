from sqlalchemy.orm import Session
from app.database.db import SessionLocal, engine, Base
from app.database.model import User, Document
from passlib.context import CryptContext

# Wachtwoord hashing (moet matchen met je auth service)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def seed_data():
    db = SessionLocal()
    try:
        # 1. Maak de tabellen aan als ze nog niet bestaan
        Base.metadata.create_all(bind=engine)

        # 2. Voeg Admin toe (als deze nog niet bestaat)
        admin_exists = db.query(User).filter(User.username == "admin").first()
        if not admin_exists:
            admin_user = User(
                username="admin",
                hashed_password=get_password_hash("admin123"), # Wijzig dit later!
                role="admin"
            )
            db.add(admin_user)
            print("✅ Admin account aangemaakt: admin / admin123")
        else:
            print("ℹ️ Admin account bestond al.")

        # 3. Voeg Test Documenten toe voor RAG
        doc_count = db.query(Document).count()
        if doc_count == 0:
            test_docs = [
                Document(
                    title="UNASAT Reglement",
                    source="reglement_2026.pdf",
                    text="Studenten moeten minimaal 80% aanwezigheid hebben bij hoorcolleges."
                ),
                Document(
                    title="UISS Handleiding",
                    source="uiss_guide.txt",
                    text="De UISS chatbot helpt studenten bij het vinden van antwoorden op vragen over de opleiding."
                )
            ]
            db.add_all(test_docs)
            print(f"✅ {len(test_docs)} test documenten toegevoegd.")
        else:
            print(f"ℹ️ Er stonden al {doc_count} documenten in de database.")

        db.commit()

    except Exception as e:
        print(f"❌ Fout bij seeden: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()