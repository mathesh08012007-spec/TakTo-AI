"""End-to-end smoke test using Flask's test client.

The Groq network calls are replaced with local stand-ins so the test runs offline
and without an API key. Everything else (routes, auth, SQLite, streaming, memory,
titles) is the real code.

Run from the project root:   python backend/tests/smoke_test.py
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
os.environ["DATABASE_PATH"] = str(Path(tempfile.mkdtemp()) / "test.db")
os.environ["GROQ_API_KEY"] = "test-key"

from ai import groq_client  # noqa: E402
from app import create_app  # noqa: E402

CALLS = {"stream": 0, "complete": 0}


def fake_stream(messages, temperature=0.8):
    CALLS["stream"] += 1
    assert messages[0]["role"] == "system" and "friendly AI companion" in messages[0]["content"]
    for piece in ["Sure! Let's ", "start with Flask.", "\n<<SUG", "GEST>> Give me code | Explain simply | Show alternatives"]:
        yield piece


def fake_complete(messages, max_tokens=600, temperature=0.3):
    CALLS["complete"] += 1
    prompt = messages[0]["content"]
    if prompt.startswith("Write a short title"):
        return "Flask Project Plan"
    return ('{"should_remember": true, "memory": "User is learning Flask for a Groq chatbot", '
            '"category": "learning", "importance": 8}')


groq_client.stream_chat = fake_stream
groq_client.complete = fake_complete

app = create_app()
c = app.test_client()


def api(method, path, body=None, client=None):
    r = getattr(client or c, method)(path, json=body) if body is not None else getattr(client or c, method)(path)
    return r


def events(resp):
    out = []
    for block in resp.get_data(as_text=True).split("\n\n"):
        if block.startswith("data: "):
            out.append(json.loads(block[6:]))
    return out


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        sys.exit(1)


check("health", api("get", "/api/health").get_json()["data"]["status"] == "ok")
check("me requires login", api("get", "/api/auth/me").status_code == 401)

bad = api("post", "/api/auth/register", {"name": "A", "email": "nope", "password": "12345678", "confirm_password": "12345678"})
check("register rejects bad email", bad.status_code == 400 and not bad.get_json()["success"])
bad = api("post", "/api/auth/register", {"name": "A", "email": "a@b.co", "password": "short", "confirm_password": "short"})
check("register rejects short password", bad.status_code == 400)
bad = api("post", "/api/auth/register", {"name": "A", "email": "a@b.co", "password": "password1", "confirm_password": "password2"})
check("register rejects mismatch", bad.status_code == 400)

r = api("post", "/api/auth/register", {"name": "Asha", "email": "Asha@Example.com", "password": "password1", "confirm_password": "password1"})
check("register ok", r.status_code == 201)
check("duplicate email rejected", api("post", "/api/auth/register", {"name": "X", "email": "asha@example.com", "password": "password1", "confirm_password": "password1"}).status_code == 409)
check("me works", api("get", "/api/auth/me").get_json()["data"]["user"]["email"] == "asha@example.com")

r = api("post", "/api/chat", {"message": "I'm learning Flask and want to build a Groq chatbot project", "mode": "coding"})
ev = events(r)
types = [e["type"] for e in ev]
check("stream event order", types[0] == "meta" and "delta" in types and "done" in types)
text = "".join(e["text"] for e in ev if e["type"] == "delta")
check("marker filtered from stream", "SUGGEST" not in text and text == "Sure! Let's start with Flask.\n")
done = next(e for e in ev if e["type"] == "done")
check("suggestions parsed", done["suggestions"] == ["Give me code", "Explain simply", "Show alternatives"])
cid = ev[0]["conversation_id"]
check("title generated once", next(e for e in ev if e["type"] == "title")["title"] == "Flask Project Plan")

time.sleep(0.5)
mems = api("get", "/api/memories").get_json()["data"]["memories"]
check("memory saved", len(mems) == 1 and mems[0]["category"] == "learning")

conv = api("get", f"/api/conversations/{cid}").get_json()["data"]
check("messages stored", [m["role"] for m in conv["messages"]] == ["user", "assistant"])
check("mode stored", conv["conversation"]["mode"] == "coding" and conv["conversation"]["title"] == "Flask Project Plan")

r = api("post", "/api/chat", {"message": "Hello again", "conversation_id": cid})
ev = events(r)
check("second message, no extra title call", "title" not in [e["type"] for e in ev] and CALLS["complete"] == 2)

r = api("post", "/api/chat/regenerate", {"conversation_id": cid})
check("regenerate streams", "done" in [e["type"] for e in events(r)])
msgs = api("get", f"/api/conversations/{cid}").get_json()["data"]["messages"]
check("regenerate replaced last reply", [m["role"] for m in msgs] == ["user", "assistant", "user", "assistant"])

first_user = msgs[0]["message_id"]
check("edit user message", api("put", f"/api/conversations/{cid}/messages/{first_user}", {"content": "Edited"}).status_code == 200)
msgs = api("get", f"/api/conversations/{cid}").get_json()["data"]["messages"]
check("edit truncates later messages", len(msgs) == 1 and msgs[0]["content"] == "Edited")
r = api("post", "/api/chat/regenerate", {"conversation_id": cid})
check("regenerate after edit", "done" in [e["type"] for e in events(r)])

mid = api("get", f"/api/conversations/{cid}").get_json()["data"]["messages"][-1]["message_id"]
check("delete message", api("delete", f"/api/conversations/{cid}/messages/{mid}").status_code == 200)

check("rename", api("put", f"/api/conversations/{cid}", {"title": "My Plan"}).get_json()["data"]["conversation"]["title"] == "My Plan")
check("search by title", len(api("get", "/api/conversations?q=plan").get_json()["data"]["conversations"]) == 1)
check("search by content", len(api("get", "/api/conversations?q=Edited").get_json()["data"]["conversations"]) == 1)
check("search miss", len(api("get", "/api/conversations?q=zzz%25").get_json()["data"]["conversations"]) == 0)

check("empty message rejected", api("post", "/api/chat", {"message": "   "}).status_code == 400)
check("bad mode rejected", api("post", "/api/chat", {"message": "hi", "mode": "evil"}).status_code == 400)

p = api("put", "/api/profile", {"name": "Asha K", "email": "asha@example.com", "tone": "casual",
                                 "favorite_mode": "think", "learning_goals": "Python", "interests": "AI"})
check("profile update", p.get_json()["data"]["profile"]["favorite_mode"] == "think")
check("profile rejects bad tone", api("put", "/api/profile", {"name": "A", "email": "a@b.co", "tone": "rude", "favorite_mode": "think"}).status_code == 400)

other = app.test_client()
api("post", "/api/auth/register", {"name": "Bo", "email": "bo@example.com", "password": "password1", "confirm_password": "password1"}, other)
check("other user cannot read conversation", api("get", f"/api/conversations/{cid}", client=other).status_code == 404)
check("other user cannot chat in it", api("post", "/api/chat", {"message": "hi", "conversation_id": cid}, other).status_code == 404)
check("other user has no memories", api("get", "/api/memories", client=other).get_json()["data"]["memories"] == [])

mid = mems[0]["memory_id"]
check("other user cannot delete memory", api("delete", f"/api/memories/{mid}", client=other).status_code == 404)
check("delete memory", api("delete", f"/api/memories/{mid}").status_code == 200)
check("clear memories", api("delete", "/api/memories").status_code == 200)

check("clear conversation", api("post", f"/api/conversations/{cid}/clear", {}).status_code == 200)
check("delete conversation", api("delete", f"/api/conversations/{cid}").status_code == 200)
check("deleted conversation is gone", api("get", f"/api/conversations/{cid}").status_code == 404)

check("logout", api("post", "/api/auth/logout", {}).status_code == 200)
check("logged out", api("get", "/api/auth/me").status_code == 401)
check("login wrong password", api("post", "/api/auth/login", {"email": "asha@example.com", "password": "nope"}).status_code == 401)
check("login ok", api("post", "/api/auth/login", {"email": "ASHA@example.com", "password": "password1"}).status_code == 200)
check("unknown api route is JSON 404", api("get", "/api/nope").get_json()["success"] is False)

# Error path: Groq failure surfaces a friendly message, user message is kept for retry.
def boom(messages, temperature=0.8):
    raise groq_client.AIError("I'm getting a lot of requests right now. Wait a few seconds and retry.", 429)
    yield
groq_client.stream_chat = boom
import routes.chat as chat_routes
chat_routes.groq_client.stream_chat = boom
r = api("post", "/api/chat", {"message": "Will this fail?"})
ev = events(r)
check("AI error becomes friendly SSE error", ev[-1]["type"] == "error" and "retry" in ev[-1]["error"].lower())
cid2 = ev[0]["conversation_id"]
check("failed turn keeps user message", api("get", f"/api/conversations/{cid2}").get_json()["data"]["messages"][-1]["role"] == "user")

print("\nAll checks passed.")
