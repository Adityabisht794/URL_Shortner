from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models
from .encoder import encode


def get_by_long_url(
    db: Session,
    long_url: str,
) -> models.URLMapping | None:
    return (
        db.query(models.URLMapping)
        .filter(models.URLMapping.long_url == long_url)
        .first()
    )


def get_by_short_code(
    db: Session,
    short_code: str,
) -> models.URLMapping | None:
    return (
        db.query(models.URLMapping)
        .filter(models.URLMapping.short_code == short_code)
        .first()
    )


def create_short_url(
    db: Session,
    long_url: str,
) -> models.URLMapping:
    mapping = models.URLMapping(
        long_url=long_url,
        short_code="",
    )

    db.add(mapping)

    try:
        db.flush()

        mapping.short_code = encode(mapping.id)

        db.commit()
        db.refresh(mapping)

        return mapping

    except IntegrityError:
        db.rollback()
        raise


def increment_click_count(
    db: Session,
    short_code: str,
) -> None:
    db.execute(
        update(models.URLMapping)
        .where(models.URLMapping.short_code == short_code)
        .values(click_count=models.URLMapping.click_count + 1)
    )

    db.commit()


def get_url_stats(
    db: Session,
    short_code: str,
) -> models.URLMapping | None:
    return get_by_short_code(db, short_code)
