# Takto: your AI companion

A full-stack AI companion: part friend, part mentor, part brainstorming partner. It talks naturally, helps you think through decisions, teaches, debugs code, brainstorms, and **remembers useful things about you** (with you in full control of what is stored).

> Don't just answer the user. Understand them, help them think, and help them move forward.

## Features

- **7 modes**: Friend, Mentor, Study, Coding, Idea, Fun, Think. Each changes the AI's system prompt. Think mode follows *what I understand → options with pros/cons → my take → next step*.
- **Streaming replies** (tokens appear as they're generated), with a Stop button.
- Markdown + code blocks with a Copy button, timestamps, typing indicator, auto-scroll.
- Regenerate, retry on error, edit a message (re-runs from there), delete a message, clear a conversation.
- Conversations: create, rename, delete, search (titles and message text), reopen, continue. Smart one-time AI titles.
- Follow-up suggestion chips after replies (one click sends them).
- Fun corner: random question, would-you-rather, mini quiz, riddle, brain teaser, joke, coding challenge, motivation challenge. All AI-powered.
- **Long-term memory**: only durable, useful facts are saved (never passwords, keys, financial details). View, delete, or clear everything on the Profile page.
- Accounts: register, login, logout, hashed passwords, session cookies. Profile with tone, favorite mode, goals and interests.
- Light/dark theme, responsive layout (sidebar becomes a drawer on mobile), keyboard accessible, ARIA labels, visible focus.

## Architecture

```text
Browser (HTML/CSS/vanilla JS)
   │  fetch /api/*  (JSON, plus streamed events for chat)
   ▼
Flask app (backend/app.py)  ── serves the frontend too
   ├─ routes/      thin HTTP layer: validation + JSON
   ├─ services/    all SQL lives here (users, conversations, memories)
   ├─ ai/          groq_client (only file that calls Groq), prompts, personality, memory
   └─ database.py  SQLite connection + schema (swap this layer to move to MongoDB later)
```

Per chat message: save user message → load recent messages (capped) → pick the few most relevant memories → add profile + mode → build the system prompt → stream from Groq → save the reply → (once per chat) generate a title → (only when the message looks personal) extract a memory in the background. That is at most 1 to 3 Groq calls, usually 1.

## Tech stack

Python 3.10+, Flask, Flask-CORS, python-dotenv, Werkzeug, Groq official SDK, SQLite, vanilla JS, no frontend build step.

## Folder structure

```text
my-ai-companion/
├── backend/
│   ├── app.py  config.py  database.py  utils.py  requirements.txt
│   ├── ai/        groq_client.py  personality.py  memory.py  prompts.py
│   ├── routes/    auth.py  chat.py  conversations.py  memory.py  profile.py
│   ├── services/  conversation_service.py  memory_service.py  user_service.py
│   └── tests/     smoke_test.py
├── frontend/
│   ├── index.html  login.html  register.html  chat.html  profile.html
│   ├── img/   takto.svg  clouds.svg
│   ├── css/  style.css  chat.css  responsive.css
│   └── js/   api.js  app.js  home.js  auth.js  chat.js  profile.js  markdown.js
├── database/      companion.db is created here on first run
├── .env.example  .gitignore  README.md
```

## Installation

```bash
cd my-ai-companion
python -m venv .venv
```

Activate it:

```bash
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\activate
```

Install:

```bash
pip install -r backend/requirements.txt
```

## Environment setup and Groq configuration

1. Create a free key at <https://console.groq.com/keys>.
2. Copy the example file and edit it:

```bash
cp .env.example .env          # Windows: copy .env.example .env
```

3. Fill in `.env`:

```ini
GROQ_API_KEY=gsk_your_real_key
SECRET_KEY=paste-a-long-random-string
DATABASE_PATH=database/companion.db
GROQ_MODEL=openai/gpt-oss-120b
```

Generate a secret key with: `python -c "import secrets; print(secrets.token_hex(32))"`

**Model:** `GROQ_MODEL` is configurable on purpose. Groq retires models regularly (the older Llama 3.x models have been deprecated). Check <https://console.groq.com/docs/models> and the deprecations page, then change the value. For `gpt-oss` models, `GROQ_REASONING_EFFORT` (`low`, `medium`, `high`) controls speed vs depth; it is ignored for other models.

The key is read only on the server. It never appears in any HTML, CSS or JS file, and `.env` is in `.gitignore`.

## Database setup

Nothing to do. Tables (`users`, `user_preferences`, `conversations`, `messages`, `memories`) are created automatically on startup, with foreign keys and indexes.

```sql
users(user_id PK, name, email UNIQUE, password_hash, created_at)
user_preferences(user_id PK/FK, tone, favorite_mode, learning_goals, interests, updated_at)
conversations(conversation_id PK, user_id FK, title, mode, title_generated, created_at, updated_at)
messages(message_id PK, conversation_id FK, role['user'|'assistant'|'system'], content, created_at)
memories(memory_id PK, user_id FK, memory_text, category, importance, created_at, updated_at)
  category: preference | goal | interest | learning | project | personal_context
```

Deleting a user or conversation cascades to its rows.

## Running locally

```bash
python backend/app.py
```

Open <http://localhost:5000>. Flask serves both the API and the frontend, so there is nothing else to start.

Optional: if you prefer to serve `frontend/` from another static server (e.g. VS Code Live Server on port 5500), add that origin to `CORS_ORIGINS` in `.env` and set `window.APP_CONFIG = { apiBase: "http://localhost:5000/api" }` in a script tag before `js/api.js`. Using the single Flask server is simpler and recommended.

## How to test

Automated, offline (no API key needed; Groq calls are replaced with stand-ins, everything else is real):

```bash
python backend/tests/smoke_test.py
```

It checks registration/login validation, streaming, suggestion parsing, title generation, memory saving, regenerate/edit/delete, search, per-user isolation, and error handling.

Manual with a real key:

1. Register, then use a quick action on the home page. Confirm it opens chat in that mode.
2. Send "Bro I don't feel like studying." and check the tone is casual.
3. Switch to **Think** and send "I'm confused whether I should choose AI or web development."
4. Say "I'm learning Python for data science and I prefer simple explanations." A moment later, open Profile → "What I remember about you".
5. Refresh the page, open the chat from the sidebar, and try rename, search, edit, regenerate, delete.
6. Resize the window below 860px to see the sidebar become a drawer.

## API endpoints

All responses are `{"success": true, "data": {...}}` or `{"success": false, "error": "message"}`.

| Method | Path | Notes |
|---|---|---|
| POST | `/api/auth/register` | name, email, password, confirm_password |
| POST | `/api/auth/login` | email, password |
| POST | `/api/auth/logout` | |
| GET | `/api/auth/me` | current user |
| POST | `/api/chat` | `{message, conversation_id?, mode?}`; streams server-sent events: `meta`, `delta`, `done`, `title`, `error` |
| POST | `/api/chat/regenerate` | `{conversation_id}`; also used for Retry |
| GET / POST | `/api/conversations` | list (`?q=` searches) / create |
| GET / PUT / DELETE | `/api/conversations/<id>` | open (with messages) / rename or change mode / delete |
| POST | `/api/conversations/<id>/clear` | delete all messages |
| PUT / DELETE | `/api/conversations/<id>/messages/<mid>` | edit a user message (drops later messages) / delete |
| GET / DELETE | `/api/memories` | list / clear all |
| DELETE | `/api/memories/<id>` | delete one |
| GET / PUT | `/api/profile` | read / update |
| GET | `/api/health` | status and whether a Groq key is configured |

## Security notes

- Passwords hashed with Werkzeug (`scrypt` by default). Never stored in plaintext.
- HTTP-only, SameSite=Lax session cookies; set `COOKIE_SECURE=1` behind HTTPS.
- All SQL is parameterized; user input is validated (lengths, email, modes, tones); request bodies are capped at 256 KB; messages at 8000 characters.
- Every conversation, message and memory query is scoped to the logged-in user.
- Markdown is escaped before rendering, and only `http(s)` links are allowed.
- In-memory rate limits on login, registration and chat. They are per process, so use Redis or a reverse proxy for multi-worker deployments.
- Groq errors are translated into friendly messages. Tracebacks and raw API errors are logged server-side only.
- Memory extraction skips anything resembling passwords, keys, tokens, card numbers or other secrets.

## Deployment

1. Set a strong `SECRET_KEY`, your real `GROQ_API_KEY`, `COOKIE_SECURE=1`, and `CORS_ORIGINS` to your domain.
2. Use a production server instead of Flask's dev server. On Linux:

```bash
pip install gunicorn
gunicorn --chdir backend -w 1 --threads 8 --timeout 120 -b 0.0.0.0:8000 app:app
```

Use threads rather than many workers because replies stream, and keep `-w 1` while rate limiting is in memory and SQLite is the database.

3. Put Nginx or Caddy in front for HTTPS. For streaming, disable proxy buffering on `/api/chat` (`proxy_buffering off;`).
4. Back up `database/companion.db`. If you outgrow SQLite, replace `database.py` and the three files in `services/`; routes and AI code don't touch SQL.

## Troubleshooting

| Problem | Fix |
|---|---|
| "The AI key isn't set up yet" | `.env` must be in the project root (next to `.env.example`) with `GROQ_API_KEY` set. Restart the server. |
| "The AI key looks invalid" | Re-copy the key from console.groq.com. No quotes or spaces. |
| "The configured AI model isn't available" | Change `GROQ_MODEL` to a model listed at console.groq.com/docs/models. |
| "I'm getting a lot of requests" | Groq free-tier rate limit. Wait a moment, or upgrade your plan. |
| Replies appear all at once behind a proxy | Turn off proxy buffering (see Deployment). |
| Logged out on every restart | `SECRET_KEY` changes between runs. Set a fixed value in `.env`. |
| `ModuleNotFoundError` | Activate the virtualenv and re-run `pip install -r backend/requirements.txt`. |
| Port already in use | Set `PORT=5001` in `.env`. |
| Google Fonts don't load (offline) | The UI falls back to system fonts automatically. |
#   T a k T o - A I  
 