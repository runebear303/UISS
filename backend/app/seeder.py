import bcrypt
from sqlalchemy.orm import Session
from app.database.db import SessionLocal, engine, Base
from app.database.model import User, Document

def hash_password(password: str) -> str:
    """Maakt een veilige bcrypt hash van een wachtwoord string."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def seed_data():
    db = SessionLocal()
    try:
        # 1. Zorg dat tabellen bestaan
        Base.metadata.create_all(bind=engine)

        # 2. Admin account
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            new_admin = User(
                username="admin",
                hashed_password=hash_password("admin123"),
                role="admin"
            )
            db.add(new_admin)
            print("✅ Admin aangemaakt (admin / admin123)")
        
        # 3. Test data voor RAG
        if db.query(Document).count() == 0:
            test_doc = Document(
                title="UNASAT Intro",
                source="seed",
                text="Welkom bij UNASAT. De aanwezigheidsplicht voor technische vakken is 80%."
            )
            db.add(test_doc)
            print("✅ Test document toegevoegd")

        db.commit()
    except Exception as e:
        print(f"❌ Seed fout: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()