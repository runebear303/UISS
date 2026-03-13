from app.database.db import engine
from app.database.model import Base


def init_database():

    Base.metadata.create_all(bind=engine)