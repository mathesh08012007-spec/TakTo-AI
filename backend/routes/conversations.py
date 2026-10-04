from flask import Blueprint, request, session

from config import Config
from services import conversation_service as cs
from services import user_service
from utils import ApiError, get_json, login_required, ok

bp = Blueprint("conversations", __name__)


def _uid():
    return session["user_id"]


def _clean_title(value):
    title = " ".join(str(value or "").split())
    if not title or len(title) > 100:
        raise ApiError("Title must be between 1 and 100 characters.")
    return title


def _check_mode(mode):
    if mode not in Config.MODES:
        raise ApiError("Unknown mode.")
    return mode


@bp.get("/conversations")
@login_required
def list_all():
    return ok({"conversations": cs.list_conversations(_uid(), request.args.get("q", ""))})


@bp.post("/conversations")
@login_required
def create():
    data = get_json()
    mode = data.get("mode") or user_service.get_preferences(_uid())["favorite_mode"]
    title = _clean_title(data["title"]) if data.get("title") else "New chat"
    return ok({"conversation": cs.create_conversation(_uid(), _check_mode(mode), title)}, 201)


@bp.get("/conversations/<int:cid>")
@login_required
def get_one(cid):
    conv = cs.get_conversation(_uid(), cid)
    return ok({"conversation": conv, "messages": cs.get_messages(cid)})


@bp.put("/conversations/<int:cid>")
@login_required
def update(cid):
    data = get_json()
    title = _clean_title(data["title"]) if "title" in data else None
    mode = _check_mode(data["mode"]) if "mode" in data else None
    return ok({"conversation": cs.update_conversation(_uid(), cid, title, mode)})


@bp.delete("/conversations/<int:cid>")
@login_required
def delete(cid):
    cs.delete_conversation(_uid(), cid)
    return ok({"deleted": cid})


@bp.post("/conversations/<int:cid>/clear")
@login_required
def clear(cid):
    cs.clear_messages(_uid(), cid)
    return ok({"cleared": cid})


@bp.put("/conversations/<int:cid>/messages/<int:mid>")
@login_required
def edit_message(cid, mid):
    content = str(get_json().get("content", "")).strip()
    if not content:
        raise ApiError("A message can't be empty.")
    if len(content) > Config.MAX_MESSAGE_CHARS:
        raise ApiError(f"Messages can be up to {Config.MAX_MESSAGE_CHARS} characters.")
    cs.edit_user_message(_uid(), cid, mid, content)
    return ok({"message_id": mid, "content": content})


@bp.delete("/conversations/<int:cid>/messages/<int:mid>")
@login_required
def delete_message(cid, mid):
    cs.delete_message(_uid(), cid, mid)
    return ok({"deleted": mid})
