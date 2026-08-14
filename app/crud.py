from sqlalchemy.orm import Session
from sqlalchemy import update
from . import models, encoder


def create_short_url(db: Session, original_url: str) -> models.URLMapping:
    # LEVEL 1 flow (this is the important part to watch):
    #   1. INSERT a row with a placeholder short_code to get an auto id
    #   2. base62-encode that id into the real short_code
    #   3. UPDATE the row
    # Two round trips to ONE database, and step 1 must fully commit before
    # step 2 can know the id. This is fine at low QPS. It will not survive
    # multiple app servers writing at once without care -> LIMITATIONS.md #1.
    row = models.URLMapping(short_code="pending", original_url=original_url)
    db.add(row)
    db.commit()
    db.refresh(row)

    row.short_code = encoder.encode(row.id)
    db.commit()
    db.refresh(row)
    return row


def get_by_short_code(db: Session, short_code: str) -> models.URLMapping | None:
    return (
        db.query(models.URLMapping)
        .filter(models.URLMapping.short_code == short_code)
        .first()
    )


def increment_visit_count(db: Session, short_code: str) -> None:
    # LEVEL 1: a write on every single redirect. Every read is also a write.
    # See LIMITATIONS.md #2 - this is the first thing that falls over under
    # real read traffic, and exactly why Level 2 introduces caching.
    db.execute(
        update(models.URLMapping)
        .where(models.URLMapping.short_code == short_code)
        .values(visit_count=models.URLMapping.visit_count + 1)
    )
    db.commit()
