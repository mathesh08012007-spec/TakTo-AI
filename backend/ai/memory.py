"""Memory selection (what to inject) and extraction (what to save)."""
import json
import logging
import re

from ai import groq_client
from ai.prompts import MEMORY_PROMPT
from config import Config
from services import memory_service

log = logging.getLogger(__name__)

SENSITIVE_RE = re.compile(
    r"(password|passcode|pass\s?word|api[\s_-]?key|secret|token|\bgsk_|\bsk-|\bcvv\b|\botp\b|card\s?number|"
    r"\b\d{12,19}\b|aadhaar|\bpan\s?number|\bssn\b|bank\s?account|\biban\b|credit\s?card|private\s?key)",
    re.IGNORECASE)

# Cheap pre-filter so we don't spend an AI call on every "hi" or one-off question.
PERSONAL_RE = re.compile(
    r"\b(i am|i'm|im|i have|i've|my|i want|i need|i prefer|i like|i love|i hate|i wish|learning|studying|"
    r"preparing|goal|aim|working on|building|exam|placement|interested|remember|planning to|trying to)\b",
    re.IGNORECASE)

STOPWORDS = set("the a an and or but of to in on for with is are was were be been it this that i you me my "
                "your we they he she at as by from so do does did not no yes can will just have has had "
                "user about what how why when who which if then than too very".split())


def _tokens(text):
    return {w for w in re.findall(r"[a-z0-9+#]+", text.lower()) if w not in STOPWORDS and len(w) > 1}


def select_relevant(memories, query, limit=None):
    """Pick the few memories worth sending to the model: keyword overlap, importance, recency."""
    limit = limit or Config.RELEVANT_MEMORIES
    if not memories:
        return []
    q = _tokens(query)
    scored = []
    for i, m in enumerate(memories):  # memories arrive sorted by importance, then recency
        overlap = len(q & _tokens(m["memory_text"]))
        score = overlap * 3 + m["importance"] / 2 - i * 0.05
        # Goals and preferences are broadly useful even without a keyword match.
        if m["category"] in ("goal", "preference"):
            score += 1.5
        scored.append((score, m))
    scored.sort(key=lambda s: s[0], reverse=True)
    return [m for _, m in scored[:limit]]


def looks_memorable(user_text):
    return len(user_text) >= 20 and bool(PERSONAL_RE.search(user_text)) and not SENSITIVE_RE.search(user_text)


def _parse_json(text):
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _similar(a, b):
    ta, tb = _tokens(a), _tokens(b)
    return bool(ta and tb) and len(ta & tb) / len(ta | tb) >= 0.6


def process_exchange(user_id, user_text, assistant_text):
    """Run after a reply is complete. Never raises: memory is a bonus, not a requirement."""
    try:
        if not looks_memorable(user_text):
            return
        existing = memory_service.list_memories(user_id)
        known = "\n".join(f"- {m['memory_text']}" for m in existing[:15]) or "(none yet)"
        raw = groq_client.complete([{"role": "user", "content": MEMORY_PROMPT.format(
            existing=known, user=user_text[:1500], assistant=assistant_text[:800])}], max_tokens=800)
        data = _parse_json(raw)
        if not data or data.get("should_remember") is not True:
            return
        text = str(data.get("memory", "")).strip()
        category = str(data.get("category", "")).strip().lower()
        try:
            importance = max(1, min(10, int(data.get("importance", 5))))
        except (TypeError, ValueError):
            importance = 5
        if not text or len(text) > 300 or category not in memory_service.CATEGORIES:
            return
        if SENSITIVE_RE.search(text):
            return
        duplicate = next((m["memory_id"] for m in existing if _similar(m["memory_text"], text)), None)
        memory_service.save_memory(user_id, text, category, importance, duplicate_of=duplicate)
    except Exception:
        log.exception("Memory extraction failed")
