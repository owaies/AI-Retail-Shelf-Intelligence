from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg

from app.core.config import settings


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    with psycopg.connect(settings.database_url) as conn:
        yield conn


def apply_migration(sql: str) -> None:
    """Execute an idempotent migration as one database transaction."""
    with connection() as conn:
        conn.execute(sql)
        conn.commit()


def database_configured() -> bool:
    return bool(settings.database_url)
