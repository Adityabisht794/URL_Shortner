from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# LEVEL 1: single SQLite file on local disk.
# This is a single point of failure and a single point of write contention -
# see LIMITATIONS.md for what breaks as traffic grows, and how Level 2 fixes it.
SQLALCHEMY_DATABASE_URL = "sqlite:///./shortener.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
