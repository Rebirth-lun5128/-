from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import settings

_connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    pool_recycle=3600,
    echo=False,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
