"""
Shared pytest fixtures.

Phase 2 requires PostgreSQL (Supabase) — SQLite is rejected by database.py
— so tests run against a real Postgres database too. Point TEST_DATABASE_URL
at a *disposable* database (a separate local Postgres instance, a Docker
container, or a spare Supabase project/branch). Tables are dropped and
recreated at the start and end of the test session so it never leaves
stray data behind, but it WILL wipe whatever schema already exists at that
URL — never point it at a database with real data.

If TEST_DATABASE_URL isn't set, we fall back to DATABASE_URL from .env,
which means running `pytest` without configuring a separate test DB will
drop and reseed your actual database. A warning is printed either way.
"""
import os
import sys
import warnings

# Ensure backend/ is on sys.path when running `pytest` from the backend dir
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

_test_db_url = os.getenv("TEST_DATABASE_URL")
if _test_db_url:
    os.environ["DATABASE_URL"] = _test_db_url
else:
    warnings.warn(
        "TEST_DATABASE_URL is not set — tests will run against DATABASE_URL "
        "(your real database) and DROP/RECREATE ALL TABLES in it. Set "
        "TEST_DATABASE_URL in .env to a disposable Postgres database instead.",
        stacklevel=1,
    )

os.environ.setdefault("SECRET_KEY", "test_secret_key_for_pytest")

if not os.environ.get("DATABASE_URL"):
    raise RuntimeError(
        "Neither TEST_DATABASE_URL nor DATABASE_URL is set. Add one to backend/.env "
        "before running pytest — see .env.example."
    )

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def _clean_test_db():
    from database import Base, engine
    Base.metadata.drop_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client(_clean_test_db):
    from main import app  # imported after env vars + table drop are set up
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def auth_token(client):
    """Logs in as the seeded demo user and returns a bearer token."""
    resp = client.post("/api/auth/login", json={"email": "admin@intelliroute.com", "password": "Admin@123"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
