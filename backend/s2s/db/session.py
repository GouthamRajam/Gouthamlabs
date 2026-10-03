"""Database engine and sessions."""
from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from s2s.config import settings


@lru_cache(maxsize=None)
def engine(url: str | None = None) -> Engine:
    return create_engine(url or settings().database_url, pool_pre_ping=True, future=True)


def session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=engine(), expire_on_commit=False)


@contextmanager
def session() -> Iterator[Session]:
    """A session that commits on success and rolls back on error."""
    s = session_factory()()
    try:
        yield s
        s.commit()
    except BaseException:
        s.rollback()
        raise
    finally:
        s.close()
