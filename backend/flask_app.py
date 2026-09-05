"""
AI Chatbot — Flask application
Created by: Satyam Tiwari (iamsatyampandit@gmail.com)

A small, classic Flask app mounted alongside the FastAPI API (see main.py).
It reads from the exact same database and gives a lightweight server-rendered
admin dashboard — a deliberate second surface so the project genuinely
exercises both frameworks against one shared data layer, rather than Flask
being present in name only.
"""

from flask import Flask, render_template_string

from .config import settings
from .database import SessionLocal, Conversation, Message

flask_app = Flask(__name__)

DASHBOARD_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{{ app_name }} — Admin</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root { color-scheme: dark; }
    body {
      margin: 0; padding: 2.5rem 1.5rem 4rem; background: #101418; color: #e7e4dd;
      font-family: 'Segoe UI', Inter, system-ui, sans-serif;
    }
    .wrap { max-width: 760px; margin: 0 auto; }
    h1 { font-size: 1.6rem; margin-bottom: .25rem; }
    p.sub { color: #9aa2ab; margin-top: 0; }
    .stats { display: flex; gap: 1rem; margin: 2rem 0; flex-wrap: wrap; }
    .card {
      background: #171d24; border: 1px solid #232b33; border-radius: 10px;
      padding: 1.1rem 1.4rem; flex: 1; min-width: 140px;
    }
    .card .n { font-size: 1.8rem; font-weight: 600; color: #4fd1ae; }
    .card .l { color: #9aa2ab; font-size: .85rem; margin-top: .2rem; }
    table { width: 100%; border-collapse: collapse; margin-top: .5rem; }
    th, td { text-align: left; padding: .55rem .6rem; border-bottom: 1px solid #232b33; font-size: .9rem; }
    th { color: #9aa2ab; font-weight: 500; }
    footer { margin-top: 3rem; color: #6b7480; font-size: .85rem; }
    a { color: #4fd1ae; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>{{ app_name }} · Admin</h1>
    <p class="sub">Served by the Flask side of the app, reading the shared database.</p>

    <div class="stats">
      <div class="card"><div class="n">{{ conversation_count }}</div><div class="l">Conversations</div></div>
      <div class="card"><div class="n">{{ message_count }}</div><div class="l">Messages</div></div>
    </div>

    <h2 style="font-size:1.05rem;">Recent conversations</h2>
    <table>
      <tr><th>Title</th><th>Session</th><th>Created</th></tr>
      {% for c in recent %}
      <tr><td>{{ c.title }}</td><td>{{ c.session_id[:8] }}…</td><td>{{ c.created_at }}</td></tr>
      {% else %}
      <tr><td colspan="3">No conversations yet.</td></tr>
      {% endfor %}
    </table>

    <footer>
      {{ app_name }} v{{ version }} · Created by {{ creator }}
      (<a href="mailto:{{ email }}">{{ email }}</a>)
    </footer>
  </div>
</body>
</html>
"""


@flask_app.get("/")
def dashboard():
    db = SessionLocal()
    try:
        conversation_count = db.query(Conversation).count()
        message_count = db.query(Message).count()
        recent = (
            db.query(Conversation)
            .order_by(Conversation.created_at.desc())
            .limit(10)
            .all()
        )
    finally:
        db.close()

    return render_template_string(
        DASHBOARD_TEMPLATE,
        app_name=settings.APP_NAME,
        version=settings.VERSION,
        creator=settings.CREATOR_NAME,
        email=settings.CREATOR_EMAIL,
        conversation_count=conversation_count,
        message_count=message_count,
        recent=recent,
    )


@flask_app.get("/health")
def health():
    return {"status": "ok", "service": "flask-admin"}
