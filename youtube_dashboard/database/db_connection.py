from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from database.models import Base

# Database file location
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'youtube_analytics.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initializes the database by creating all tables."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
