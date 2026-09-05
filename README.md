# Tiwari — AI Chatbot

A full-stack AI chatbot: a vanilla HTML/CSS/JS frontend, a **FastAPI** chat
API and a **Flask** admin dashboard running side by side in one process, an
AI API integration layer, and a database layer that runs on **SQLite**
locally and **PostgreSQL** in production with no code changes.

**Created by:** Satyam Tiwari
**Email:** iamsatyampandit@gmail.com

---

## Architecture

```
ai-chatbot/
├── backend/
│   ├── main.py          # Entry point — mounts FastAPI + Flask + static frontend
│   ├── fastapi_app.py    # Chat API: /api/chat, /api/conversations, ...
│   ├── flask_app.py       # Server-rendered admin dashboard: /admin
│   ├── ai_service.py      # Calls the AI provider's API
│   ├── database.py        # SQLAlchemy models (SQLite / PostgreSQL)
│   ├── schemas.py          # Pydantic request/response models
│   └── config.py            # All environment-driven settings
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── requirements.txt
├── .env.example
└── README.md
```

**Why both Flask and FastAPI?** FastAPI serves the real, async chat API that
the frontend talks to. Flask serves a separate, classic server-rendered
admin dashboard at `/admin` that reads the exact same database — a genuine
second surface, not a token inclusion. Both are mounted into a single ASGI
app in `main.py` (Flask runs under `WSGIMiddleware`), so one `uvicorn`
process serves everything.

## Setup

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# then edit .env and add your AI_API_KEY (leave DATABASE_URL empty to use SQLite)

# 4. Run
uvicorn backend.main:app --reload --port 8000
```

Then open:
- **Chat UI** — http://localhost:8000/
- **Admin dashboard (Flask)** — http://localhost:8000/admin
- **API docs (FastAPI, auto-generated)** — http://localhost:8000/docs

Without an `AI_API_KEY`, the app still runs end-to-end in **demo mode** —
messages are saved and echoed back so you can test the frontend, database,
and session handling before wiring up a real key.

## Switching to PostgreSQL

Just set `DATABASE_URL` in `.env`, e.g.:

```
DATABASE_URL=postgresql://user:password@localhost:5432/chatbot_db
```

Create the database first (`createdb chatbot_db`), then run the app —
tables are created automatically on startup, no migration step needed for
a fresh database.

## How it works

1. The browser generates a session ID (stored in `localStorage`) so chat
   history persists across page reloads without requiring login.
2. Sending a message hits `POST /api/chat`, which saves the user's message,
   loads the conversation's full history, calls the AI API for a reply,
   saves that reply, and returns it.
3. The sidebar lists past conversations for that session (`GET
   /api/conversations`) and reloads any of them (`GET
   /api/conversations/{id}`).
4. `/admin` (Flask) shows aggregate stats — total conversations, total
   messages, and the 10 most recent conversations — read straight from the
   same database.

## Tech stack

| Layer          | Technology                     |
|----------------|---------------------------------|
| Frontend       | HTML, CSS, vanilla JavaScript   |
| API framework  | FastAPI (async, `/api/*`)       |
| Admin panel    | Flask (`/admin`)                |
| AI integration | AI provider's chat/completions API, via `httpx` |
| Database (dev) | SQLite                          |
| Database (prod)| PostgreSQL                      |
| ORM            | SQLAlchemy                      |

---

© 2026 Satyam Tiwari · iamsatyampandit@gmail.com
