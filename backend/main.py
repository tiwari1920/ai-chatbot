"""
AI Chatbot — Entry point
Created by: Satyam Tiwari (iamsatyampandit@gmail.com)

Run with:  uvicorn backend.main:app --reload --port 8000

One ASGI app serves three things, matched in this order:
  1. The FastAPI chat API            -> /api/*     (defined in fastapi_app.py)
  2. The classic Flask admin panel   -> /admin/*    (defined in flask_app.py, run as WSGI)
  3. The static HTML/CSS/JS frontend -> /           (falls back to index.html)

Both frameworks share the exact same SQLite/PostgreSQL database — Flask
isn't decorative here, it genuinely serves a second, real surface of the app.
"""

from pathlib import Path

from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.staticfiles import StaticFiles

from .fastapi_app import fastapi_app
from .flask_app import flask_app

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# The app object uvicorn runs. fastapi_app already owns every /api/* route
# (registered when fastapi_app.py was imported), so we extend it in place
# rather than wrapping it in another app.
app = fastapi_app

# Flask admin dashboard, mounted as a WSGI app inside this ASGI app.
app.mount("/admin", WSGIMiddleware(flask_app))

# Static frontend, mounted last so it only catches what /api and /admin don't.
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
