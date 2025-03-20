import sqlite3
from typing import Callable, Optional

from retrievvy.config import DATA

# Init
# -----

db = sqlite3.connect(DATA)
db.row_factory = sqlite3.Row

db.executescript("""
    PRAGMA foreign_keys = ON;
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

CREATE TABLE IF NOT EXISTS blocks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    idx             TEXT NOT NULL,
    bundle_id       TEXT NOT NULL,
    content         TEXT NOT NULL,
    ref             TEXT NOT NULL,
    block_order     INTEGER NOT NULL,

    FOREIGN KEY (bundle_id, idx) REFERENCES bundles (id, idx) ON DELETE CASCADE
);

-- Enforce unique block ordering per bundle
CREATE UNIQUE INDEX IF NOT EXISTS ux_blocks_bundle_order ON blocks(bundle_id, idx, "block_order");

CREATE INDEX IF NOT EXISTS idx_blocks_bundle ON blocks(bundle_id);
CREATE INDEX IF NOT EXISTS idx_blocks_idx    ON blocks(idx);
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


def bundle_list(bundle_id: str, index: str, page: int = 0, items: int = 0):
    sql = "SELECT * FROM bundles WHERE id = ? AND idx = ?"
    args = [bundle_id, index]

    if items > 0:
        sql += " LIMIT ? OFFSET ?"
        args.extend([items, page * items])

    cur = db.cursor()
    cur.execute(sql, args)
    rows = cur.fetchall()

    return [dict(row) for row in rows]
