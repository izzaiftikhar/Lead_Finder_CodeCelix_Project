"""DB layer: SQLite (default) or PostgreSQL (DATABASE_URL). Parameterized queries only."""
import sqlite3, threading, uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from .config import settings

PG = settings.DATABASE_URL.startswith(("postgres://", "postgresql://"))
_lock = threading.RLock()


def now():
    return datetime.now(timezone.utc).isoformat()


def uid():
    return str(uuid.uuid4())


@contextmanager
def conn():
    with _lock:
        if PG:
            import psycopg
            c = psycopg.connect(settings.DATABASE_URL)
        else:
            c = sqlite3.connect(settings.DATABASE_PATH, timeout=30)
            c.row_factory = sqlite3.Row
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()


def _q(sql):
    return sql.replace("?", "%s") if PG else sql


def execute(sql, args=()):
    with conn() as c:
        cur = c.cursor()
        cur.execute(_q(sql), tuple(args))
        return cur.rowcount


def insert_returning_id(sql, args=()):
    with conn() as c:
        cur = c.cursor()
        if PG:
            cur.execute(_q(sql) + " RETURNING id", tuple(args))
            return cur.fetchone()[0]
        cur.execute(sql, tuple(args))
        return cur.lastrowid


def rows(sql, args=()):
    with conn() as c:
        cur = c.cursor()
        cur.execute(_q(sql), tuple(args))
        if PG:
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        return [dict(r) for r in cur.fetchall()]


def one(sql, args=()):
    r = rows(sql, args)
    return r[0] if r else None


def scalar(sql, args=(), default=0):
    r = one(sql, args)
    if not r:
        return default
    v = list(r.values())[0]
    return default if v is None else v
