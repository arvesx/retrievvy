import sqlite3
from typing import Callable, Optional

from retrievvy.config import DATA

# Init
# -----

db = sqlite3.connect(DATA)
db.row_factory = sqlite3.Row

db.executescript("""
    PRAGMA foreign_keys = ON;
    PRAGMA journal_mode = WAL;
    PRAGMA synchronous = NORMAL;
    PRAGMA cache_size = -20000;
    PRAGMA temp_store = MEMORY;
""")

SCHEMA = """
CREATE TABLE IF NOT EXISTS indexes (
    name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS bundles (
    id              TEXT NOT NULL,
    idx             TEXT NOT NULL,
    source          TEXT NOT NULL,
    name            TEXT NOT NULL,
    created         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status          TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'chunked', 'completed')),

    PRIMARY KEY (id, idx),
    FOREIGN KEY (idx) REFERENCES indexes (name) ON DELETE CASCADE
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS chunks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    idx             TEXT NOT NULL,
    bundle_id       TEXT NOT NULL,
    content         TEXT NOT NULL,
    ref             TEXT NOT NULL,
    chunk_order     INTEGER NOT NULL,

    FOREIGN KEY (bundle_id, idx) REFERENCES bundles (id, idx) ON DELETE CASCADE
);

-- Enforce unique chunk ordering per bundle
CREATE UNIQUE INDEX IF NOT EXISTS ux_chunks_bundle_order ON chunks(bundle_id, idx, "chunk_order");

CREATE INDEX IF NOT EXISTS idx_chunks_bundle ON chunks(bundle_id);
CREATE INDEX IF NOT EXISTS ix_bundles_idx ON bundles(idx);
CREATE INDEX IF NOT EXISTS ix_chunks_idx_bundle ON chunks(idx, bundle_id);
"""


def init():
    # Schema initialize
    with db:
        db.executescript(SCHEMA)


# In many cases I use the pattern of passing an optional callback
# function to the database operations. That is, because sometimes
# I need to pair another operation with a db operation and they
# need to happen in the same transaction, so if something goes
# wrong, the transaction is rolled back. One such example is the
# deletion of an index, which requires also the deletion of data
# in many other places including the file system.


# Indexes
# -------


def index_add(name: str, cb: Optional[Callable] = None) -> None:
    with db:
        db.execute("INSERT INTO indexes (name) VALUES (?)", (name,))

        if cb:
            cb()


def index_del(name: str, cb: Optional[Callable] = None) -> None:
    with db:
        db.execute("DELETE FROM indexes WHERE name = ?", (name,))

        if cb:
            cb()


def index_get(name: str):
    cur = db.cursor()
    cur.execute("SELECT * FROM indexes WHERE name = ?", (name,))
    row = cur.fetchone()
    return dict(row) if row else None


def index_list(page: int = 0, items: int = 0):
    sql = "SELECT name FROM indexes ORDER BY name ASC"
    args = []  # happily avoid sql injection :)

    if items > 0:
        sql += " LIMIT ? OFFSET ?"
        args.extend([items, page * items])

    cur = db.cursor()
    cur.execute(sql, args)
    rows = cur.fetchall()

    return [dict(row) for row in rows]


# Bundles
# -------


def bundle_add(
    bundle_id: str, index: str, source: str, name: str, cb: Optional[Callable] = None
) -> None:
    with db:
        db.execute(
            "INSERT INTO bundles (id, idx, source, name) VALUES (?, ?, ?, ?)",
            (bundle_id, index, source, name),
        )

        if cb:
            cb()


def bundle_del(bundle_id: str, index: str, cb: Optional[Callable] = None) -> None:
    with db:
        db.execute("DELETE FROM bundles WHERE id = ? AND idx = ?", (bundle_id, index))

        if cb:
            cb()


def bundle_get(bundle_id: str, index: str):
    cur = db.cursor()
    cur.execute("SELECT * FROM bundles WHERE id = ? AND idx = ?", (bundle_id, index))
    row = cur.fetchone()
    return dict(row) if row else None


def bundle_list(index: str, page: int = 0, items: int = 0):
    sql = "SELECT * FROM bundles WHERE idx = ?"
    args = [index]

    if items > 0:
        sql += " LIMIT ? OFFSET ?"
        args.extend([items, page * items])

    cur = db.cursor()
    cur.execute(sql, args)
    rows = cur.fetchall()

    return [dict(row) for row in rows]


# Chunks
# ------


def chunk_add(
    index: str,
    bundle_id: str,
    content: str,
    ref: str,
    chunk_order: int,
    cb: Optional[Callable] = None,
) -> None:
    with db:
        db.execute(
            "INSERT INTO chunks (idx, bundle_id, content, ref, chunk_order) VALUES (?, ?, ?, ?, ?)",
            (index, bundle_id, content, ref, chunk_order),
        )

        if cb:
            cb()


def chunks_add(
    chunks: list[tuple[str, str, str, str, int]],
    cb: Optional[Callable] = None,
) -> None:
    with db:
        db.executemany(
            "INSERT INTO chunks (idx, bundle_id, content, ref, chunk_order) VALUES (?, ?, ?, ?, ?)",
            chunks,
        )

        if cb:
            cb()


def chunk_get(chunk_id: int):
    cur = db.cursor()
    cur.execute("SELECT * FROM chunks WHERE id = ?", (chunk_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def chunks_get(chunk_ids: list[int]):
    if len(chunk_ids) <= 900:
        placeholders = ",".join("?" for _ in chunk_ids)
        sql = f"SELECT * FROM chunks WHERE id IN ({placeholders})"
        cur = db.cursor()
        cur.execute(sql, chunk_ids)
        return [dict(row) for row in cur.fetchall()]

    # Fallback for >900 IDs
    with db:
        db.execute("CREATE TEMP TABLE IF NOT EXISTS temp_ids (id INTEGER PRIMARY KEY)")
        db.execute("DELETE FROM temp_ids")

        db.executemany(
            "INSERT INTO temp_ids (id) VALUES (?)", [(cid,) for cid in chunk_ids]
        )

        cur = db.cursor()
        cur.execute("""
            SELECT c.* FROM chunks c
            JOIN temp_ids t ON c.id = t.id
        """)
        rows = cur.fetchall()
        return [dict(row) for row in rows]
