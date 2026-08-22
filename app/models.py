from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from .database import Base


class URLMapping(Base):
    __tablename__ = "url_mappings"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    short_code = Column(
        String(10),
        unique=True,
        index=True,
        nullable=False,
    )

    long_url = Column(
        String(2048),
        unique=True,
        index=True,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    click_count = Column(
        Integer,
        default=0,
        nullable=False,
    )
