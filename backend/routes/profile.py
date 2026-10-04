from flask import Blueprint, session

from services import user_service
from utils import get_json, login_required, ok

bp = Blueprint("profile", __name__)


@bp.get("/profile")
@login_required
def get_profile():
    return ok({"profile": user_service.get_profile(session["user_id"])})


@bp.put("/profile")
@login_required
def update_profile():
    return ok({"profile": user_service.update_profile(session["user_id"], get_json())})
