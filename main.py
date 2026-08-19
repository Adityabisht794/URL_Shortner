"""
Level 2: PostgreSQL + Indexing + Dedup
----------------------------------------
Same FastAPI app as Level 1, now backed by PostgreSQL instead of
SQLite, with unique indexes on short_code and long_url. The long_url
index enables a new behavior: shortening the same URL twice now
returns the existing short_code instead of minting a duplicate row.

Still no caching, no queueing, no horizontal scaling - one app
process, one DB instance. Those remain open items.

Run:
    docker-compose up -d          # starts Postgres on localhost:5432
    pip install -r requirements.txt
    uvicorn main:app --reload

Endpoints:
    POST /api/shorten          {"long_url": "..."}  -> {"short_code", "short_url"}
    GET  /{short_code}         -> 307 redirect to the long URL
    GET  /api/stats/{short_code} -> click count + metadata
    GET  /api/health           -> liveness check
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import init_db, get_db, URLMapping
from app.encoder import encode

app = FastAPI(title="URL Shortener - Level 2")

BASE_HOST = "http://short.ly"  # placeholder domain for generated links


@app.on_event("startup")
def on_startup():
    init_db()


class ShortenRequest(BaseModel):
    long_url: HttpUrl


class ShortenResponse(BaseModel):
    short_code: str
    short_url: str
    long_url: str


class StatsResponse(BaseModel):
    short_code: str
    long_url: str
    click_count: int
    created_at: str


def _existing_response(mapping: URLMapping) -> ShortenResponse:
    return ShortenResponse(
        short_code=mapping.short_code,
        short_url=f"{BASE_HOST}/{mapping.short_code}",
        long_url=mapping.long_url,
    )


@app.post("/api/shorten", response_model=ShortenResponse)
def shorten_url(payload: ShortenRequest, db: Session = Depends(get_db)):
    long_url_str = str(payload.long_url)

    # Level 2 dedup: long_url is now indexed, so this is an O(log n)
    # lookup, not the table scan it would have been in Level 1. If this
    # URL was already shortened, hand back the existing code instead of
    # minting a new row.
    existing = db.query(URLMapping).filter(URLMapping.long_url == long_url_str).first()
    if existing:
        return _existing_response(existing)

    mapping = URLMapping(long_url=long_url_str, short_code="")
    db.add(mapping)
    db.flush()  # get the autoincrement id without committing yet

    short_code = encode(mapping.id)
    mapping.short_code = short_code

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # The check-then-insert above has a race window: another request
        # could insert the same long_url between our SELECT and our
        # COMMIT. The unique constraint on long_url (added in database.py)
        # is what actually closes that race - this is just handling the
        # rejection gracefully instead of surfacing it as a 500.
        existing = (
            db.query(URLMapping).filter(URLMapping.long_url == long_url_str).first()
        )
        if existing:
            return _existing_response(existing)
        # Rare second case: an actual short_code collision, unrelated to
        # the long_url race above.
        raise HTTPException(500, "Short code collision - please retry")

    db.refresh(mapping)
    return ShortenResponse(
        short_code=short_code,
        short_url=f"{BASE_HOST}/{short_code}",
        long_url=long_url_str,
    )


@app.get("/api/stats/{short_code}", response_model=StatsResponse)
def get_stats(short_code: str, db: Session = Depends(get_db)):
    mapping = db.query(URLMapping).filter(URLMapping.short_code == short_code).first()
    if not mapping:
        raise HTTPException(404, "Short code not found")
    return StatsResponse(
        short_code=mapping.short_code,
        long_url=mapping.long_url,
        click_count=mapping.click_count,
        created_at=mapping.created_at.isoformat(),
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "level": 2}


@app.get("/{short_code}")
def redirect_to_long_url(short_code: str, db: Session = Depends(get_db)):
    # Every single redirect is a synchronous DB read + a DB write
    # (the click_count increment). At Level 1 that's fine. At scale,
    # this line is the first thing that falls over - see LIMITATIONS.md.
    mapping = db.query(URLMapping).filter(URLMapping.short_code == short_code).first()
    if not mapping:
        raise HTTPException(404, "Short URL not found")

    mapping.click_count += 1
    db.commit()

    return RedirectResponse(url=mapping.long_url, status_code=307)
