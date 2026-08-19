"""
Level 2 storage layer: PostgreSQL + explicit indexes.

Level 1 used a single SQLite file. SQLite serializes writers at the
file level, so it never scales past one process reliably. Level 2
swaps that for PostgreSQL, a real client/server database that handles
many concurrent connections and enforces constraints server-side.

Two indexes do two different jobs here:
  - short_code: unique + indexed. Powers the hot-path redirect lookup
    (GET /{short_code}) as an O(log n) btree lookup instead of a scan.
    This existed conceptually in Level 1 too, but SQLite's single-file
    locking meant it didn't matter much under concurrent load.
  - long_url: unique + indexed (new in Level 2). Powers the dedup
    check in POST /api/shorten and, because it's a DB-level unique
    constraint (not just an app-level check), also closes the race
    condition where two concurrent requests try to shorten the same
    URL at the same instant - see the IntegrityError handling in
    main.py for how that race is resolved.

Known simplification, flagged rather than solved here: long_url is
indexed as the raw VARCHAR(2048). Postgres has a per-index-entry size
ceiling (roughly 1/3 of the 8KB page, ~2700 bytes) that a pathological
URL with heavy multibyte/percent-encoding could theoretically approach.
The standard production fix is a unique index on a hash of the URL
instead of the URL itself - deferred for now since it trades this
problem for hash-collision handling, which is a bigger change than
this level warrants.
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime, timezone

# Placeholder dev credentials - matches docker-compose.yml. Override via
# the DATABASE_URL env var for any real deployment.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://urlshort:urlshort@localhost:5432/urlshortener",
)

# pool_pre_ping matters for Postgres specifically (it didn't for SQLite,
# which has no network connection to go stale): it checks a pooled
# connection is still alive before handing it to a request, instead of
# surfacing "server closed the connection unexpectedly" mid-request.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class URLMapping(Base):
    __tablename__ = "url_mappings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    short_code = Column(String(10), unique=True, index=True, nullable=False)
    long_url = Column(String(2048), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    click_count = Column(Integer, default=0)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
