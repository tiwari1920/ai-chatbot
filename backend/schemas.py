"""
AI Chatbot — Pydantic schemas
Created by: Satyam Tiwari (iamsatyampandit@gmail.com)
"""

from datetime import datetime
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    session_id: str = Field(..., description="Client-generated UUID identifying the browser session")
    conversation_id: str | None = Field(None, description="Existing conversation to continue, or omit to start a new one")


class MessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    created_at: datetime


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationDetail(ConversationOut):
    messages: list[MessageOut]
