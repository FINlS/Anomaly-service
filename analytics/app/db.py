import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])
LokalSession = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

def getDb():
    db = LokalSession()
    try:
        yield db
    finally:
        db.close()