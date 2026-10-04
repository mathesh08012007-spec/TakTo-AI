"""Chat endpoints. Replies stream to the browser as server-sent events over a POST."""
import json
import logging
import re
import threading

from flask import Blueprint, Response, session, stream_with_context

from ai import groq_client, memory
from ai.groq_client import AIError
from ai.personality import StreamFilter, build_system_prompt
from ai.prompts import TITLE_PROMPT
from config import Config
from services import conversation_service as cs
from services import memory_service, user_service
from utils import ApiError, get_json, login_required, rate_limit, to_int

log = logging.getLogger(__name__)
bp = Blueprint("chat", __name__)


def _sse(event):
    return "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"


def _build_messages(user_id, conversation):
    user = user_service.get_user(user_id)
    prefs = user_service.get_preferences(user_id)
    history = cs.recent_messages(conversation["conversation_id"], Config.CONTEXT_MESSAGES)

    # Keep the newest messages that fit in the character budget.
    kept, used = [], 0
    for m in reversed(history):
        used += len(m["content"])
        if kept and used > Config.CONTEXT_CHAR_BUDGET:
            break
        kept.append(m)
    kept.reverse()

    recent_user_text = " ".join(m["content"] for m in kept if m["role"] == "user")[-1500:]
    memories = memory.select_relevant(memory_service.list_memories(user_id), recent_user_text)
    system = build_system_prompt(user, prefs, conversation["mode"], memories)
    return [{"role": "system", "content": system}] + kept


def _make_title(conversation_id, user_text, assistant_text):
    """One small AI call, once per conversation. Falls back to the first words of the chat."""
    title = ""
    try:
        raw = groq_client.complete(
            [{"role": "user", "content": TITLE_PROMPT.format(user=user_text[:400], assistant=assistant_text[:400])}],
            max_tokens=400, temperature=0.4)
        title = re.sub(r"[\"'`*#]", "", raw.strip().splitlines()[0]).strip(" .")[:60]
    except Exception:
        log.warning("Title generation failed; using fallback")
    if not title:
        title = " ".join(user_text.split())[:40] or "New chat"
    cs.set_generated_title(conversation_id, title)
    return title


def _stream_reply(user_id, conversation_id):
    conversation = cs.get_conversation(user_id, conversation_id)
    last_user = cs.last_message(conversation_id)
    user_text = last_user["content"] if last_user else ""

    def generate():
        yield _sse({"type": "meta", "conversation_id": conversation_id,
                    "user_message": last_user})
        flt = StreamFilter()
        saved = False
        try:
            messages = _build_messages(user_id, conversation)
            for chunk in groq_client.stream_chat(messages):
                out = flt.feed(chunk)
                if out:
                    yield _sse({"type": "delta", "text": out})
            tail, suggestions = flt.finish()
            if tail:
                yield _sse({"type": "delta", "text": tail})

            text = flt.visible.strip()
            if not text:
                raise AIError("I came back with an empty answer. Please try again.")
            saved_msg = cs.add_message(conversation_id, "assistant", text)
            saved = True
            yield _sse({"type": "done", "message": saved_msg, "suggestions": suggestions})

            threading.Thread(target=memory.process_exchange, args=(user_id, user_text, text), daemon=True).start()

            fresh = cs.get_conversation(user_id, conversation_id, required=False)
            if fresh and not fresh["title_generated"] and cs.message_count(conversation_id) >= 2:
                yield _sse({"type": "title", "conversation_id": conversation_id,
                            "title": _make_title(conversation_id, user_text, text)})
        except GeneratorExit:
            # The browser stopped or disconnected: keep whatever was written so far.
            partial = flt.visible.strip()
            if partial and not saved:
                cs.add_message(conversation_id, "assistant", partial)
            raise
        except AIError as exc:
            yield _sse({"type": "error", "error": exc.user_message})
        except Exception:
            log.exception("Chat stream failed")
            yield _sse({"type": "error", "error": "Something went wrong while talking to my AI brain. Try again."})

    return Response(stream_with_context(generate()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _validated_mode(data):
    mode = data.get("mode")
    if mode is None:
        return None
    if mode not in Config.MODES:
        raise ApiError("Unknown mode.")
    return mode


@bp.post("/chat")
@login_required
@rate_limit("chat", 30, 60)
def chat():
    data = get_json()
    user_id = session["user_id"]
    text = str(data.get("message", "")).strip()
    if not text:
        raise ApiError("Type a message first.")
    if len(text) > Config.MAX_MESSAGE_CHARS:
        raise ApiError(f"Messages can be up to {Config.MAX_MESSAGE_CHARS} characters.")
    mode = _validated_mode(data)

    if data.get("conversation_id"):
        conv = cs.get_conversation(user_id, to_int(data["conversation_id"], "conversation id"))
        if mode and mode != conv["mode"]:
            cs.update_conversation(user_id, conv["conversation_id"], mode=mode)
    else:
        prefs = user_service.get_preferences(user_id)
        conv = cs.create_conversation(user_id, mode or prefs["favorite_mode"])

    cs.add_message(conv["conversation_id"], "user", text)
    return _stream_reply(user_id, conv["conversation_id"])


@bp.post("/chat/regenerate")
@login_required
@rate_limit("chat", 30, 60)
def regenerate():
    data = get_json()
    user_id = session["user_id"]
    cid = to_int(data.get("conversation_id"), "conversation id")
    conv = cs.get_conversation(user_id, cid)
    mode = _validated_mode(data)
    if mode and mode != conv["mode"]:
        cs.update_conversation(user_id, cid, mode=mode)

    last = cs.last_message(cid)
    if last and last["role"] == "assistant":
        cs.delete_message_by_id(cid, last["message_id"])
        last = cs.last_message(cid)
    if not last or last["role"] != "user":
        raise ApiError("There's nothing to regenerate yet.")
    return _stream_reply(user_id, cid)
