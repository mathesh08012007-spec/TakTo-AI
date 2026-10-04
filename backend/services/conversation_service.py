from database import db, now
from utils import ApiError


def _rows(rows):
    return [dict(r) for r in rows]


def _like(q):
    q = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{q}%"


def list_conversations(user_id, query=""):
    query = (query or "").strip()[:100]
    with db() as conn:
        if query:
            rows = conn.execute(
                """SELECT conversation_id, title, mode, created_at, updated_at FROM conversations c
                   WHERE user_id = ? AND (title LIKE ? ESCAPE '\\' OR EXISTS (
                       SELECT 1 FROM messages m WHERE m.conversation_id = c.conversation_id
                       AND m.content LIKE ? ESCAPE '\\'))
                   ORDER BY updated_at DESC LIMIT 100""",
                (user_id, _like(query), _like(query))).fetchall()
        else:
            rows = conn.execute(
                """SELECT conversation_id, title, mode, created_at, updated_at FROM conversations
                   WHERE user_id = ? ORDER BY updated_at DESC LIMIT 200""", (user_id,)).fetchall()
    return _rows(rows)


def create_conversation(user_id, mode="friend", title="New chat"):
    ts = now()
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO conversations (user_id, title, mode, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, mode, ts, ts))
        cid = cur.lastrowid
    return get_conversation(user_id, cid)


def get_conversation(user_id, conversation_id, required=True):
    with db() as conn:
        row = conn.execute(
            """SELECT conversation_id, title, mode, title_generated, created_at, updated_at
               FROM conversations WHERE conversation_id = ? AND user_id = ?""",
            (conversation_id, user_id)).fetchone()
    if not row and required:
        raise ApiError("That conversation couldn't be found.", 404)
    return dict(row) if row else None


def update_conversation(user_id, conversation_id, title=None, mode=None):
    get_conversation(user_id, conversation_id)
    with db() as conn:
        if title is not None:
            conn.execute("UPDATE conversations SET title = ?, title_generated = 1 WHERE conversation_id = ?",
                         (title, conversation_id))
        if mode is not None:
            conn.execute("UPDATE conversations SET mode = ? WHERE conversation_id = ?", (mode, conversation_id))
    return get_conversation(user_id, conversation_id)


def set_generated_title(conversation_id, title):
    with db() as conn:
        conn.execute("UPDATE conversations SET title = ?, title_generated = 1 WHERE conversation_id = ?",
                     (title, conversation_id))


def delete_conversation(user_id, conversation_id):
    get_conversation(user_id, conversation_id)
    with db() as conn:
        conn.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))


def _touch(conn, conversation_id):
    conn.execute("UPDATE conversations SET updated_at = ? WHERE conversation_id = ?", (now(), conversation_id))


def add_message(conversation_id, role, content):
    ts = now()
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (conversation_id, role, content, ts))
        _touch(conn, conversation_id)
        mid = cur.lastrowid
    return {"message_id": mid, "role": role, "content": content, "created_at": ts}


def get_messages(conversation_id):
    with db() as conn:
        rows = conn.execute(
            """SELECT message_id, role, content, created_at FROM messages
               WHERE conversation_id = ? AND role != 'system' ORDER BY message_id""",
            (conversation_id,)).fetchall()
    return _rows(rows)


def recent_messages(conversation_id, limit):
    with db() as conn:
        rows = conn.execute(
            """SELECT role, content FROM messages
               WHERE conversation_id = ? AND role IN ('user', 'assistant')
               ORDER BY message_id DESC LIMIT ?""", (conversation_id, limit)).fetchall()
    return list(reversed(_rows(rows)))


def last_message(conversation_id):
    with db() as conn:
        row = conn.execute(
            """SELECT message_id, role, content, created_at FROM messages
               WHERE conversation_id = ? ORDER BY message_id DESC LIMIT 1""", (conversation_id,)).fetchone()
    return dict(row) if row else None


def message_count(conversation_id):
    with db() as conn:
        return conn.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = ?",
                            (conversation_id,)).fetchone()[0]


def first_user_message(conversation_id):
    with db() as conn:
        row = conn.execute(
            "SELECT content FROM messages WHERE conversation_id = ? AND role = 'user' ORDER BY message_id LIMIT 1",
            (conversation_id,)).fetchone()
    return row["content"] if row else ""


def delete_message_by_id(conversation_id, message_id):
    with db() as conn:
        conn.execute("DELETE FROM messages WHERE conversation_id = ? AND message_id = ?",
                     (conversation_id, message_id))
        _touch(conn, conversation_id)


def delete_message(user_id, conversation_id, message_id):
    get_conversation(user_id, conversation_id)
    with db() as conn:
        cur = conn.execute("DELETE FROM messages WHERE conversation_id = ? AND message_id = ?",
                           (conversation_id, message_id))
        if cur.rowcount == 0:
            raise ApiError("That message couldn't be found.", 404)
        _touch(conn, conversation_id)


def edit_user_message(user_id, conversation_id, message_id, content):
    """Edit a user message and drop everything after it so the chat can be regenerated."""
    get_conversation(user_id, conversation_id)
    with db() as conn:
        row = conn.execute(
            "SELECT role FROM messages WHERE conversation_id = ? AND message_id = ?",
            (conversation_id, message_id)).fetchone()
        if not row:
            raise ApiError("That message couldn't be found.", 404)
        if row["role"] != "user":
            raise ApiError("Only your own messages can be edited.")
        conn.execute("UPDATE messages SET content = ? WHERE message_id = ?", (content, message_id))
        conn.execute("DELETE FROM messages WHERE conversation_id = ? AND message_id > ?",
                     (conversation_id, message_id))
        _touch(conn, conversation_id)


def clear_messages(user_id, conversation_id):
    get_conversation(user_id, conversation_id)
    with db() as conn:
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        _touch(conn, conversation_id)
