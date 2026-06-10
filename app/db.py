from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.settings import DB_PATH
from app.models import User

engine = create_engine(DB_PATH)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

User.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
