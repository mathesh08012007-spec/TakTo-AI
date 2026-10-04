# 🤖 TakTo AI — Your Personal AI Companion

<p align="center">
  <strong>Think better. Learn faster. Build smarter.</strong>
</p>

<p align="center">
  A full-stack AI companion that acts as your <strong>friend, mentor, study partner, coding assistant, and brainstorming partner</strong>.
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Backend-000000?style=for-the-badge\&logo=flask\&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge\&logo=sqlite\&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-AI-F55036?style=for-the-badge)
![JavaScript](https://img.shields.io/badge/JavaScript-Vanilla-F7DF1E?style=for-the-badge\&logo=javascript\&logoColor=black)

</p>

<p align="center">

<a href="#-features">Features</a> • <a href="#-architecture">Architecture</a> • <a href="#-installation">Installation</a> • <a href="#-usage">Usage</a> • <a href="#-api">API</a> • <a href="#-security">Security</a>

</p>

---

## 🧠 What is TakTo AI?

**TakTo AI** is a full-stack personal AI companion designed to do more than simply answer questions.

It understands the user's context, helps with decision-making, teaches concepts, assists with programming, generates ideas, and remembers useful long-term information — while keeping the user in control of stored memories.

> **"Don't just answer the user. Understand them, help them think, and help them move forward."**

---

## ✨ Why TakTo AI?

Most AI chat applications focus only on generating responses.

TakTo AI focuses on **continuous interaction**.

```text
             ┌───────────────────────┐
             │       👤 USER         │
             └───────────┬───────────┘
                         │
                         ▼
             ┌───────────────────────┐
             │      🤖 TakTo AI      │
             │                       │
             │  Understand Context   │
             │  Select AI Mode       │
             │  Retrieve Memories    │
             │  Generate Response    │
             └───────────┬───────────┘
                         │
                         ▼
             ┌───────────────────────┐
             │   💬 Useful Response  │
             └───────────────────────┘
```

---

# 🚀 Features

## 🎭 7 AI Modes

Choose how TakTo should interact with you.

| Mode                | Purpose                                            |
| ------------------- | -------------------------------------------------- |
| 🧑‍🤝‍🧑 **Friend** | Casual conversations and support                   |
| 🧭 **Mentor**       | Guidance and decision-making                       |
| 📚 **Study**        | Learn concepts with simple explanations            |
| 💻 **Coding**       | Debugging and programming assistance               |
| 💡 **Idea**         | Brainstorming and creative thinking                |
| 🎮 **Fun**          | Games, jokes and entertainment                     |
| 🧠 **Think**        | Structured reasoning with pros/cons and next steps |

### Think Mode

Think mode follows:

```text
What I understand
        ↓
Available options
        ↓
Pros & Cons
        ↓
My take
        ↓
Next step
```

---

## ⚡ Real-Time Streaming

AI responses are streamed as they are generated.

```text
AI is thinking...

Hello 👋
        ↓
Hello! 👋 How
        ↓
Hello! 👋 How are
        ↓
Hello! 👋 How are you?
```

Includes:

* ⚡ Streaming responses
* ⏹️ Stop generation
* 🔄 Regenerate
* 🔁 Retry on errors
* ✏️ Edit messages
* 🗑️ Delete messages
* 📋 Copy code
* ⏱️ Message timestamps
* ⌨️ Typing indicator
* 📜 Automatic scrolling

---

# 🧠 Long-Term Memory

TakTo can remember **useful information about the user**.

For example:

```text
User:
"I'm learning Python for Data Science."

        ↓

TakTo AI

        ↓

Memory:
Learning → Python
Interest → Data Science
```

The user remains in control.

### Memory controls

* 👁️ View memories
* 🗑️ Delete individual memories
* 🧹 Clear all memories
* 🔐 Sensitive information is not intentionally stored

Passwords, API keys, tokens and financial information are excluded from memory extraction.

---

# 💬 Conversation Management

TakTo AI provides a complete conversation system.

### Supported operations

```text
Create conversation
        ↓
Chat
        ↓
Rename
        ↓
Search
        ↓
Edit
        ↓
Regenerate
        ↓
Delete / Clear
```

Features include:

* Create conversations
* Rename conversations
* Search conversations
* Reopen previous conversations
* Continue conversations
* Delete conversations
* Clear messages
* Edit previous messages
* Regenerate AI responses
* Smart AI-generated titles

---

# 🎮 Fun Corner

Need a break?

TakTo AI includes an AI-powered entertainment section.

```text
🎲 Random Question
🤔 Would You Rather
🧩 Mini Quiz
🧠 Riddle
💡 Brain Teaser
😂 Joke
💻 Coding Challenge
🔥 Motivation Challenge
```

---

# 👤 Personal Profile

Users can customize their AI experience.

```text
Name
Email
        │
        ├── Tone
        ├── Favorite Mode
        ├── Learning Goals
        └── Interests
```

---

# 🎨 Modern UI

TakTo AI supports:

* 🌙 Dark mode
* ☀️ Light mode
* 📱 Responsive design
* 📂 Mobile sidebar drawer
* ⌨️ Keyboard accessibility
* ♿ ARIA labels
* 🎯 Visible focus states
* 💻 Desktop-friendly chat interface

---

# 🏗️ Architecture

```text
                         👤 USER
                           │
                           ▼
              ┌─────────────────────────┐
              │       FRONTEND          │
              │                         │
              │ HTML + CSS + Vanilla JS │
              └────────────┬────────────┘
                           │
                           │ REST API
                           │ + Streaming
                           ▼
              ┌─────────────────────────┐
              │       FLASK APP         │
              │      backend/app.py     │
              └────────────┬────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
     ┌─────────┐     ┌───────────┐    ┌──────────┐
     │ Routes  │     │ AI Layer  │    │ Services │
     │         │     │           │    │          │
     │ Auth    │     │ Groq      │    │ Users    │
     │ Chat    │     │ Prompts   │    │ Chat     │
     │ Profile │     │ Memory    │    │ Memory   │
     └─────────┘     └─────┬─────┘    └────┬─────┘
                           │               │
                           ▼               ▼
                     ┌────────────────────────┐
                     │        SQLite           │
                     │                          │
                     │ Users                    │
                     │ Conversations           │
                     │ Messages                │
                     │ Memories                │
                     └────────────────────────┘
```

---

# 🔄 AI Chat Pipeline

Every message follows this pipeline:

```text
User Message
     │
     ▼
Save Message
     │
     ▼
Load Recent Messages
     │
     ▼
Retrieve Relevant Memories
     │
     ▼
Load User Profile
     │
     ▼
Select AI Mode
     │
     ▼
Build System Prompt
     │
     ▼
Groq AI
     │
     ▼
Stream Response
     │
     ▼
Save Assistant Response
     │
     ├──────────────► Generate Title
     │
     └──────────────► Extract Useful Memory
```

Usually this requires **1 AI call**, with additional calls only when title generation or memory extraction is required.

---

# 🛠️ Tech Stack

### Backend

* 🐍 Python 3.10+
* 🌶️ Flask
* 🔀 Flask-CORS
* 🔐 Werkzeug
* 📦 python-dotenv
* 🤖 Groq SDK

### Database

* 🗄️ SQLite

### Frontend

* HTML5
* CSS3
* Vanilla JavaScript
* Responsive CSS

### AI

* Groq API
* Configurable Groq model
* Streaming responses
* Prompt-based personality system
* Context-aware memory

---

# 📁 Project Structure

```text
my-ai-companion/
│
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── database.py
│   ├── utils.py
│   ├── requirements.txt
│   │
│   ├── ai/
│   │   ├── groq_client.py
│   │   ├── personality.py
│   │   ├── memory.py
│   │   └── prompts.py
│   │
│   ├── routes/
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── conversations.py
│   │   ├── memory.py
│   │   └── profile.py
│   │
│   ├── services/
│   │   ├── conversation_service.py
│   │   ├── memory_service.py
│   │   └── user_service.py
│   │
│   └── tests/
│       └── smoke_test.py
│
├── frontend/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── chat.html
│   ├── profile.html
│   │
│   ├── img/
│   ├── css/
│   └── js/
│
├── database/
│   └── companion.db
│
├── .env.example
├── .gitignore
└── README.md
```

---

# ⚙️ Installation

## 1️⃣ Clone the repository

```bash
git clone https://github.com/mathesh08012007-spec/TakTo-AI.git
cd TakTo-AI
```

---

## 2️⃣ Create virtual environment

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3️⃣ Install dependencies

```bash
pip install -r backend/requirements.txt
```

---

# 🔑 Configure Groq

Create a Groq API key from the Groq Console.

Copy:

```text
.env.example
```

to:

```text
.env
```

### Windows

```powershell
copy .env.example .env
```

### macOS / Linux

```bash
cp .env.example .env
```

Configure:

```env
GROQ_API_KEY=your_groq_api_key

SECRET_KEY=your_random_secret_key

DATABASE_PATH=database/companion.db

GROQ_MODEL=openai/gpt-oss-120b
```

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

> ⚠️ Never commit `.env` or your Groq API key to GitHub.

---

# ▶️ Run the Application

Start the Flask server:

```bash
python backend/app.py
```

Then open:

```text
http://localhost:5000
```

That's it.

The Flask backend serves both the API and frontend.

---

# 🧪 Testing

Run the automated offline smoke test:

```bash
python backend/tests/smoke_test.py
```

The tests cover:

```text
Registration
     ↓
Login
     ↓
Streaming
     ↓
Suggestions
     ↓
Memory
     ↓
Conversation Management
     ↓
Edit / Delete
     ↓
Search
     ↓
User Isolation
     ↓
Error Handling
```

---

# 🔌 API

All API responses follow:

```json
{
  "success": true,
  "data": {}
}
```

or:

```json
{
  "success": false,
  "error": "message"
}
```

### Authentication

| Method | Endpoint             | Description   |
| ------ | -------------------- | ------------- |
| POST   | `/api/auth/register` | Register user |
| POST   | `/api/auth/login`    | Login         |
| POST   | `/api/auth/logout`   | Logout        |
| GET    | `/api/auth/me`       | Current user  |

### Chat

| Method | Endpoint               | Description         |
| ------ | ---------------------- | ------------------- |
| POST   | `/api/chat`            | Send message        |
| POST   | `/api/chat/regenerate` | Regenerate response |

### Conversations

| Method | Endpoint                       | Description               |
| ------ | ------------------------------ | ------------------------- |
| GET    | `/api/conversations`           | List/search conversations |
| POST   | `/api/conversations`           | Create conversation       |
| GET    | `/api/conversations/:id`       | Open conversation         |
| PUT    | `/api/conversations/:id`       | Rename/change mode        |
| DELETE | `/api/conversations/:id`       | Delete conversation       |
| POST   | `/api/conversations/:id/clear` | Clear messages            |

### Memory

| Method | Endpoint            | Description    |
| ------ | ------------------- | -------------- |
| GET    | `/api/memories`     | List memories  |
| DELETE | `/api/memories/:id` | Delete memory  |
| DELETE | `/api/memories`     | Clear memories |

### Profile

| Method | Endpoint       |
| ------ | -------------- |
| GET    | `/api/profile` |
| PUT    | `/api/profile` |

### Health

```text
GET /api/health
```

---

# 🔐 Security

TakTo AI includes several security protections.

### Authentication

* Passwords hashed using Werkzeug
* HTTP-only session cookies
* SameSite cookie protection
* Secure cookies supported behind HTTPS

### API Security

* Parameterized SQL queries
* Input validation
* Request-size limits
* Message-size limits
* Per-user data isolation
* Rate limiting

### AI Security

Sensitive information is intentionally excluded from memory extraction, including:

```text
❌ Passwords
❌ API keys
❌ Tokens
❌ Card numbers
❌ Secrets
```

---

# 🗃️ Database

SQLite is automatically initialized when the application starts.

Main tables:

```text
users
   │
   ├── user_preferences
   │
   ├── conversations
   │       │
   │       └── messages
   │
   └── memories
```

SQLite can later be replaced with another database by changing the database/service layer.

---

# 🚀 Deployment

For production, use a production WSGI server instead of Flask's development server.

Example:

```bash
pip install gunicorn
```

```bash
gunicorn \
  --chdir backend \
  -w 1 \
  --threads 8 \
  --timeout 120 \
  -b 0.0.0.0:8000 \
  app:app
```

For production:

```text
Internet
    │
    ▼
HTTPS / Nginx / Caddy
    │
    ▼
Gunicorn
    │
    ▼
Flask
    │
    ├── Groq
    │
    └── SQLite
```

---

# 🐛 Troubleshooting

| Problem                   | Solution                                    |
| ------------------------- | ------------------------------------------- |
| AI key not configured     | Check `.env` and restart server             |
| Invalid AI key            | Generate/copy a new Groq key                |
| Model unavailable         | Change `GROQ_MODEL`                         |
| Too many requests         | Wait for rate limit to reset                |
| Streaming appears delayed | Disable proxy buffering                     |
| Logged out after restart  | Keep a fixed `SECRET_KEY`                   |
| Module not found          | Activate `.venv` and reinstall requirements |
| Port already used         | Change `PORT` in `.env`                     |

---

# 🗺️ Roadmap

Potential future improvements:

```text
[x] Multi-mode AI
[x] Streaming responses
[x] Conversation management
[x] Long-term memory
[x] User profiles
[x] Fun corner
[x] Responsive UI
[x] Security validation
[ ] Voice conversation
[ ] Speech-to-text
[ ] Text-to-speech
[ ] RAG knowledge base
[ ] File/document chat
[ ] Multi-model support
[ ] Redis rate limiting
[ ] Cloud database
```

---

# 📊 Project Highlights

```text
🤖 AI Companion
        +
🧠 Long-Term Memory
        +
💬 Real-Time Streaming
        +
🎭 Multiple Personalities
        +
👤 User Profiles
        +
🔐 Secure Authentication
        +
📱 Responsive Interface
        =
🚀 TakTo AI
```

---

# 👨‍💻 Developer

**Mathesh K**

B.Tech — Artificial Intelligence & Data Science

Interested in:

```text
Artificial Intelligence
Machine Learning
Data Science
Web Development
Generative AI
LLM Applications
```

---

# ⭐ Support the Project

If you find **TakTo AI** useful:

⭐ Star the repository
🍴 Fork the project
🐛 Report issues
💡 Suggest features
🔀 Submit pull requests

---

<p align="center">

<strong>Built with Python, Flask, JavaScript, SQLite & Groq AI ❤️</strong>

<br><br>

<em>Think better. Learn faster. Build smarter.</em>

</p>
