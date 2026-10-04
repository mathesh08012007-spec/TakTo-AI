from config import Config
from database import db, now
from utils import ApiError

CATEGORIES = ("preference", "goal", "interest", "learning", "project", "personal_context")


def list_memories(user_id):
    with db() as conn:
        rows = conn.execute(
            """SELECT memory_id, memory_text, category, importance, created_at, updated_at
               FROM memories WHERE user_id = ? ORDER BY importance DESC, updated_at DESC""",
            (user_id,)).fetchall()
    return [dict(r) for r in rows]


def save_memory(user_id, text, category, importance, duplicate_of=None):
    """Insert a memory, or refresh an existing one when `duplicate_of` is given."""
    ts = now()
    with db() as conn:
        if duplicate_of:
            conn.execute(
                """UPDATE memories SET memory_text = ?, category = ?,
                   importance = MAX(importance, ?), updated_at = ?
                   WHERE memory_id = ? AND user_id = ?""",
                (text, category, importance, ts, duplicate_of, user_id))
            return
        conn.execute(
            """INSERT INTO memories (user_id, memory_text, category, importance, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""", (user_id, text, category, importance, ts, ts))
        # Keep the table bounded: drop the least important, oldest rows past the cap.
        conn.execute(
            """DELETE FROM memories WHERE user_id = ? AND memory_id IN (
                 SELECT memory_id FROM memories WHERE user_id = ?
                 ORDER BY importance DESC, updated_at DESC LIMIT -1 OFFSET ?)""",
            (user_id, user_id, Config.MAX_MEMORIES_PER_USER))


def delete_memory(user_id, memory_id):
    with db() as conn:
        cur = conn.execute("DELETE FROM memories WHERE memory_id = ? AND user_id = ?", (memory_id, user_id))
        if cur.rowcount == 0:
            raise ApiError("That memory couldn't be found.", 404)


def clear_memories(user_id):
    with db() as conn:
        cur = conn.execute("DELETE FROM memories WHERE user_id = ?", (user_id,))
        return cur.rowcount
