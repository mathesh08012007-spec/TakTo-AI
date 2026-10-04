from flask import Blueprint, session

from services import user_service
from utils import ApiError, get_json, login_required, ok, rate_limit

bp = Blueprint("auth", __name__)


def _start_session(user):
    session.clear()
    session["user_id"] = user["user_id"]
    session.permanent = True


@bp.post("/auth/register")
@rate_limit("register", 10, 3600)
def register():
    data = get_json()
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    confirm = str(data.get("confirm_password", ""))
    user_service.validate_registration(name, email, password, confirm)
    user = user_service.create_user(name, email, password)
    _start_session(user)
    return ok({"user": user}, 201)


@bp.post("/auth/login")
@rate_limit("login", 10, 60)
def login():
    data = get_json()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    if not email or not password:
        raise ApiError("Enter your email and password.")
    user = user_service.authenticate(email, password)
    _start_session(user)
    return ok({"user": user})


@bp.post("/auth/logout")
def logout():
    session.clear()
    return ok({"message": "Logged out."})


@bp.get("/auth/me")
@login_required
def me():
    return ok({"user": user_service.get_user(session["user_id"])})
