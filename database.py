from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./db.sqlite"

engine = create_engine(DATABASE_URL, echo=True)

SessionMaker = sessionmaker(autoflush=False, bind=engine)
