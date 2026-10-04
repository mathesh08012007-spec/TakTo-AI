"""SQLite access layer.

Every service talks to the database through `db()` only, so swapping SQLite for
another store later means rewriting this file and the services, not the routes.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from config import Config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id        INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    tone           TEXT NOT NULL DEFAULT 'auto',
    favorite_mode  TEXT NOT NULL DEFAULT 'friend',
    learning_goals TEXT NOT NULL DEFAULT '',
    interests      TEXT NOT NULL DEFAULT '',
    updated_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title           TEXT NOT NULL DEFAULT 'New chat',
    mode            TEXT NOT NULL DEFAULT 'friend',
    title_generated INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS messages (
    message_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content         TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, message_id);

CREATE TABLE IF NOT EXISTS memories (
    memory_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    memory_text TEXT NOT NULL,
    category    TEXT NOT NULL CHECK (category IN
                ('preference','goal','interest','learning','project','personal_context')),
    importance  INTEGER NOT NULL DEFAULT 5,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id, importance DESC);
"""


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _connect():
    conn = sqlite3.connect(Config.DATABASE_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db():
    """Open a connection, commit on success, roll back on error, always close."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    conn = _connect()
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
