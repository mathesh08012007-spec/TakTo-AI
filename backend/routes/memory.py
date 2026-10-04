from flask import Blueprint, session

from services import memory_service
from utils import login_required, ok

bp = Blueprint("memory", __name__)


@bp.get("/memories")
@login_required
def list_memories():
    return ok({"memories": memory_service.list_memories(session["user_id"])})


@bp.delete("/memories/<int:memory_id>")
@login_required
def delete_memory(memory_id):
    memory_service.delete_memory(session["user_id"], memory_id)
    return ok({"deleted": memory_id})


@bp.delete("/memories")
@login_required
def clear_memories():
    return ok({"deleted": memory_service.clear_memories(session["user_id"])})
