"""
AI Chatbot — Database layer
Created by: Satyam Tiwari (iamsatyampandit@gmail.com)

Uses SQLAlchemy so the exact same models run against SQLite (great for local
development, zero setup) or PostgreSQL (for production) — the only thing
that changes is the DATABASE_URL environment variable.
"""

import uuid
from datetime import datetime

from sqlalchemy import create_engine, Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from .config import settings

# SQLite needs this connect_arg when used from multiple threads (FastAPI +
# Flask, each with their own worker threads); PostgreSQL does not.
connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def _uuid() -> str:
    return str(uuid.uuid4())


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=_uuid)
    session_id = Column(String(36), index=True, nullable=False)
    title = Column(String(255), default="New conversation")
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship(
        "Message", back_populates="conversation",
        cascade="all, delete-orphan", order_by="Message.created_at",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


def init_db() -> None:
    """Create tables if they don't exist yet. Safe to call on every boot."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency: yields a session, always closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
