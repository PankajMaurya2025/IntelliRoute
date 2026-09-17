"""
Database connection and session management for IntelliRoute.

As of Phase 2 this connects to PostgreSQL (Supabase) exclusively — no
SQLite fallback. DATABASE_URL must be a postgresql:// (or
postgresql+psycopg2://) connection string, e.g. Supabase's pooled
connection string from Project Settings -> Database -> Connection string.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Copy .env.example to .env and set it to your "
        "Supabase PostgreSQL connection string, e.g.\n"
        "  postgresql+psycopg2://postgres:<password>@<host>:5432/postgres?sslmode=require"
    )

if DATABASE_URL.startswith("sqlite"):
    raise RuntimeError(
        "SQLite is no longer supported as of Phase 2 — set DATABASE_URL to a "
        "PostgreSQL (Supabase) connection string in your .env file."
    )

# Supabase connections require SSL in transit; pool_pre_ping avoids
# stale-connection errors after the pooler recycles idle connections.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
