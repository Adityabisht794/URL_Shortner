from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud, models
from app.database import Base, engine, get_db
from app.schemas import (
    HealthResponse,
    ShortenRequest,
    ShortenResponse,
    StatsResponse,
)

BASE_HOST = "http://short.ly"

app = FastAPI(
    title="URL Shortener - Level 2",
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


def build_shorten_response(
    mapping: models.URLMapping,
) -> ShortenResponse:
    return ShortenResponse(
        short_code=mapping.short_code,
        short_url=f"{BASE_HOST}/{mapping.short_code}",
        long_url=mapping.long_url,
    )


@app.post(
    "/api/shorten",
    response_model=ShortenResponse,
)
def shorten_url(
    payload: ShortenRequest,
    db: Session = Depends(get_db),
):
    long_url = str(payload.long_url)

    existing = crud.get_by_long_url(
        db=db,
        long_url=long_url,
    )

    if existing:
        return build_shorten_response(existing)

    try:
        mapping = crud.create_short_url(
            db=db,
            long_url=long_url,
        )

        return build_shorten_response(mapping)

    except IntegrityError:
        existing = crud.get_by_long_url(
            db=db,
            long_url=long_url,
        )

        if existing:
            return build_shorten_response(existing)

        raise HTTPException(
            status_code=500,
            detail="Short code collision - please retry",
        )


@app.get(
    "/api/stats/{short_code}",
    response_model=StatsResponse,
)
def get_stats(
    short_code: str,
    db: Session = Depends(get_db),
):
    mapping = crud.get_url_stats(
        db=db,
        short_code=short_code,
    )

    if not mapping:
        raise HTTPException(
            status_code=404,
            detail="Short code not found",
        )

    return StatsResponse(
        short_code=mapping.short_code,
        long_url=mapping.long_url,
        click_count=mapping.click_count,
        created_at=mapping.created_at,
    )


@app.get(
    "/api/health",
    response_model=HealthResponse,
)
def health():
    return {
        "status": "ok",
        "level": 2,
    }


@app.get("/{short_code}")
def redirect_to_long_url(
    short_code: str,
    db: Session = Depends(get_db),
):
    mapping = crud.get_by_short_code(
        db=db,
        short_code=short_code,
    )

    if not mapping:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found",
        )

    crud.increment_click_count(
        db=db,
        short_code=short_code,
    )

    return RedirectResponse(
        url=mapping.long_url,
        status_code=307,
    )
