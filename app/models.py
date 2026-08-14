from sqlalchemy import Column, Integer, String, DateTime, func
from .database import Base


class URLMapping(Base):
    __tablename__ = "url_mappings"

    # LEVEL 1: auto-increment primary key is what we base62-encode into the
    # short code. This is simple but means the DB is the single source of
    # truth for "the next id" -> only one writer can safely hand out ids
    # at a time. See LIMITATIONS.md, item #1.
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    short_code = Column(String(10), unique=True, index=True, nullable=False)
    original_url = Column(String(2048), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    visit_count = Column(Integer, default=0, nullable=False)
