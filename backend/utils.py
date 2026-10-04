"""Small shared helpers: JSON responses, auth guard, rate limiting."""
import threading
import time
from collections import defaultdict, deque
from functools import wraps

from flask import jsonify, request, session


class ApiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def ok(data=None, status=200):
    return jsonify({"success": True, "data": {} if data is None else data}), status


def fail(message, status=400):
    return jsonify({"success": False, "error": message}), status


def get_json():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("That request didn't look right. Please try again.")
    return data


def to_int(value, label="id"):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ApiError(f"Invalid {label}.")


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from services import user_service  # local import avoids a circular import
        user_id = session.get("user_id")
        if not user_id or not user_service.get_user(user_id):
            session.clear()
            raise ApiError("Please log in to continue.", 401)
        return fn(*args, **kwargs)
    return wrapper


_hits = defaultdict(deque)
_lock = threading.Lock()


def rate_limit(name, limit, window_seconds):
    """Simple in-memory sliding window limiter (per user, or per IP when logged out)."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            who = session.get("user_id") or request.remote_addr or "anon"
            key = (name, who)
            now = time.monotonic()
            with _lock:
                q = _hits[key]
                while q and now - q[0] > window_seconds:
                    q.popleft()
                if len(q) >= limit:
                    raise ApiError("You're going a bit fast. Give it a few seconds and try again.", 429)
                q.append(now)
            return fn(*args, **kwargs)
        return wrapper
    return decorator
