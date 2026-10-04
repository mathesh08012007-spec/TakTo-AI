import re
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from database import db, now
from utils import ApiError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _public(row):
    return {"user_id": row["user_id"], "name": row["name"], "email": row["email"]}


def validate_registration(name, email, password, confirm):
    if not name or not email or not password or not confirm:
        raise ApiError("Please fill in all the fields.")
    if len(name) > 80:
        raise ApiError("Name is too long (80 characters max).")
    if len(email) > 254 or not EMAIL_RE.match(email):
        raise ApiError("That email address doesn't look right.")
    if len(password) < 8:
        raise ApiError("Password must be at least 8 characters.")
    if len(password) > 128:
        raise ApiError("Password is too long (128 characters max).")
    if password != confirm:
        raise ApiError("Passwords don't match.")


def create_user(name, email, password):
    ts = now()
    try:
        with db() as conn:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (name, email, generate_password_hash(password), ts))
            user_id = cur.lastrowid
            conn.execute("INSERT INTO user_preferences (user_id, updated_at) VALUES (?, ?)", (user_id, ts))
    except sqlite3.IntegrityError:
        raise ApiError("An account with this email already exists.", 409)
    return get_user(user_id)


def authenticate(email, password):
    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not row or not check_password_hash(row["password_hash"], password):
        raise ApiError("Wrong email or password.", 401)
    return _public(row)


def get_user(user_id):
    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return _public(row) if row else None


def get_preferences(user_id):
    with db() as conn:
        row = conn.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,)).fetchone()
    if not row:
        return {"tone": "auto", "favorite_mode": "friend", "learning_goals": "", "interests": ""}
    return {k: row[k] for k in ("tone", "favorite_mode", "learning_goals", "interests")}


def get_profile(user_id):
    return {**get_user(user_id), **get_preferences(user_id)}


def update_profile(user_id, data):
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    tone = str(data.get("tone", "auto")).strip().lower()
    mode = str(data.get("favorite_mode", "friend")).strip().lower()
    goals = str(data.get("learning_goals", "")).strip()
    interests = str(data.get("interests", "")).strip()

    if not name or len(name) > 80:
        raise ApiError("Please enter a name (80 characters max).")
    if len(email) > 254 or not EMAIL_RE.match(email):
        raise ApiError("That email address doesn't look right.")
    if tone not in Config.TONES:
        raise ApiError("Unknown tone.")
    if mode not in Config.MODES:
        raise ApiError("Unknown mode.")
    if len(goals) > 1000 or len(interests) > 1000:
        raise ApiError("Goals and interests can be up to 1000 characters each.")

    ts = now()
    try:
        with db() as conn:
            conn.execute("UPDATE users SET name = ?, email = ? WHERE user_id = ?", (name, email, user_id))
            conn.execute(
                """INSERT INTO user_preferences (user_id, tone, favorite_mode, learning_goals, interests, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(user_id) DO UPDATE SET tone = excluded.tone,
                     favorite_mode = excluded.favorite_mode, learning_goals = excluded.learning_goals,
                     interests = excluded.interests, updated_at = excluded.updated_at""",
                (user_id, tone, mode, goals, interests, ts))
    except sqlite3.IntegrityError:
        raise ApiError("Another account already uses this email.", 409)
    return get_profile(user_id)
