"""
AI Chatbot — FastAPI application
Created by: Satyam Tiwari (iamsatyampandit@gmail.com)

Owns the actual chat API: sending a message, getting an AI reply, and
persisting/retrieving conversation history. Async end-to-end, since talking
to the AI API and the database benefits from it under concurrent chats.
"""

from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .database import init_db, get_db, Conversation, Message
from .schemas import ChatRequest, ChatResponse, ConversationOut, ConversationDetail
from .ai_service import get_ai_reply, AIServiceError

fastapi_app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description=f"Backend API for {settings.APP_NAME}, built by {settings.CREATOR_NAME}.",
)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.CORS_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@fastapi_app.on_event("startup")
def on_startup() -> None:
    init_db()


@fastapi_app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.VERSION}


@fastapi_app.get("/api/about")
def about():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "creator": settings.CREATOR_NAME,
        "email": settings.CREATOR_EMAIL,
    }


@fastapi_app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    # Load or create the conversation.
    conversation = None
    if payload.conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == payload.conversation_id, Conversation.session_id == payload.session_id)
            .first()
        )
    if conversation is None:
        conversation = Conversation(
            session_id=payload.session_id,
            title=payload.message[:60],
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Save the user's message.
    user_msg = Message(conversation_id=conversation.id, role="user", content=payload.message)
    db.add(user_msg)
    db.commit()

    # Build the full history for the AI call.
    history = [
        {"role": m.role, "content": m.content}
        for m in db.query(Message).filter(Message.conversation_id == conversation.id).order_by(Message.created_at)
    ]

    try:
        reply_text = await get_ai_reply(history)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    assistant_msg = Message(conversation_id=conversation.id, role="assistant", content=reply_text)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return ChatResponse(
        conversation_id=conversation.id,
        reply=reply_text,
        created_at=assistant_msg.created_at,
    )


@fastapi_app.get("/api/conversations", response_model=list[ConversationOut])
def list_conversations(session_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Conversation)
        .filter(Conversation.session_id == session_id)
        .order_by(Conversation.created_at.desc())
        .all()
    )


@fastapi_app.get("/api/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str, session_id: str, db: Session = Depends(get_db)):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.session_id == session_id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@fastapi_app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, session_id: str, db: Session = Depends(get_db)):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.session_id == session_id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conversation)
    db.commit()
    return {"deleted": conversation_id}
