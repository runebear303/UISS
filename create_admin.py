import bcrypt
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData

# De verbindingsgegevens
DB_URL = "mysql+mysqldb://uiss_user:uiss_password@localhost:3306/uiss_db"

def create_admin():
    engine = create_engine(DB_URL)
    metadata = MetaData()
    
    # Definiëren van de tabel
    users = Table('users', metadata,
        Column('id', Integer, primary_key=True),
        Column('username', String(50), unique=True),
        Column('hashed_password', String(100)),
        Column('role', String(20))
    )

    # Jouw gegevens
    username = "admin"
    password = "uissPass" 
    
    # Wachtwoord hashen
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    with engine.connect() as conn:
        try:
            # Data invoegen
            stmt = users.insert().values(
                username=username, 
                hashed_password=hashed, 
                role="admin"
            )
            conn.execute(stmt)
            conn.commit()
            print(f"Admin '{username}' succesvol aangemaakt!")
        except Exception as e:
            print(f"Fout: {e}")

if __name__ == "__main__":
    create_admin()