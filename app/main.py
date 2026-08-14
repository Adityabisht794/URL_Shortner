from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from . import models, schemas, crud
from .database import engine, get_db


# Create database tables if they don't exist
models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="URL Shortener - Level 1"
)

BASE_HOST = "http://localhost:8000"


# --------------------------------------------------
# Home
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "URL Shortener API is running",
        "docs": "/docs"
    }


# --------------------------------------------------
# Create Short URL
# --------------------------------------------------

@app.post("/shorten", response_model=schemas.ShortenResponse)
def shorten_url(
    payload: schemas.ShortenRequest,
    db: Session = Depends(get_db)
):
    row = crud.create_short_url(
        db,
        str(payload.url)
    )

    return schemas.ShortenResponse(
        short_code=row.short_code,
        short_url=f"{BASE_HOST}/{row.short_code}",
        original_url=row.original_url
    )


# --------------------------------------------------
# Resolve Short URL - useful for Swagger
# --------------------------------------------------

@app.get(
    "/api/resolve/{short_code}",
    response_model=schemas.ResolveResponse
)
def resolve_url(
    short_code: str,
    db: Session = Depends(get_db)
):
    row = crud.get_by_short_code(
        db,
        short_code
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found"
        )

    return schemas.ResolveResponse(
        short_code=row.short_code,
        original_url=row.original_url
    )


# --------------------------------------------------
# Redirect Short URL
# --------------------------------------------------

@app.get("/{short_code}")
def redirect_to_original(
    short_code: str,
    db: Session = Depends(get_db)
):
    row = crud.get_by_short_code(
        db,
        short_code
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found"
        )

    # Increment visit count
    crud.increment_visit_count(
        db,
        short_code
    )

    # Redirect browser to original URL
    return RedirectResponse(
        url=row.original_url,
        status_code=307
    )


# --------------------------------------------------
# Statistics
# --------------------------------------------------

@app.get(
    "/api/stats/{short_code}",
    response_model=schemas.StatsResponse
)
def get_stats(
    short_code: str,
    db: Session = Depends(get_db)
):
    row = crud.get_by_short_code(
        db,
        short_code
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found"
        )

    return row


# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "level": 1
    }