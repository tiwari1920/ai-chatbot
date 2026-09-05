"""
AI Chatbot — AI service layer
Created by: Satyam Tiwari (iamsatyampandit@gmail.com)

Talks to the AI provider's chat-completions style API. Ships pointed at
Anthropic's Messages API by default, but AI_API_URL / AI_API_KEY / AI_MODEL
are all configurable, so any compatible provider can be dropped in.

If no AI_API_KEY is configured, falls back to a lightweight local reply so
the rest of the app (frontend, database, sessions) can be exercised and
demoed without needing a key on hand.
"""

import httpx

from .config import settings


class AIServiceError(Exception):
    pass


def _fallback_reply(user_message: str) -> str:
    return (
        "(Demo mode — no AI_API_KEY configured, so this is a canned reply.) "
        f"You said: \"{user_message.strip()}\". Add your API key to the .env "
        "file to get real AI-generated responses."
    )


def _gemini_url() -> str:
    return (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.AI_MODEL}:generateContent?key={settings.AI_API_KEY}"
    )


def _build_request(history: list[dict]) -> tuple[str, dict, dict]:
    """Returns (url, payload, headers) in the shape the configured provider expects."""
    if settings.AI_PROVIDER == "openai":
        payload = {
            "model": settings.AI_MODEL,
            "max_tokens": settings.AI_MAX_TOKENS,
            "messages": [{"role": "system", "content": settings.AI_SYSTEM_PROMPT}, *history],
        }
        headers = {
            "content-type": "application/json",
            "Authorization": f"Bearer {settings.AI_API_KEY}",
        }
        return settings.AI_API_URL, payload, headers

    if settings.AI_PROVIDER == "gemini":
        # Gemini uses "user"/"model" roles (not "assistant"), and each turn's
        # text sits inside a "parts" list rather than a plain string.
        contents = [
            {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
            for m in history
        ]
        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": settings.AI_SYSTEM_PROMPT}]},
            "generationConfig": {"maxOutputTokens": settings.AI_MAX_TOKENS},
        }
        headers = {"content-type": "application/json"}
        return _gemini_url(), payload, headers

    # default: anthropic
    payload = {
        "model": settings.AI_MODEL,
        "max_tokens": settings.AI_MAX_TOKENS,
        "system": settings.AI_SYSTEM_PROMPT,
        "messages": history,
    }
    headers = {
        "content-type": "application/json",
        "x-api-key": settings.AI_API_KEY,
        "anthropic-version": "2023-06-01",
    }
    return settings.AI_API_URL, payload, headers


def _extract_reply(data: dict) -> str:
    if settings.AI_PROVIDER == "openai":
        choices = data.get("choices", [])
        if not choices:
            raise AIServiceError("AI API returned no choices.")
        return choices[0].get("message", {}).get("content", "")

    if settings.AI_PROVIDER == "gemini":
        candidates = data.get("candidates", [])
        if not candidates:
            raise AIServiceError(f"AI API returned no candidates: {data}")
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts)

    # default: anthropic — content is a list of blocks; take the text ones.
    blocks = data.get("content", [])
    return "".join(block.get("text", "") for block in blocks if block.get("type") == "text")


async def get_ai_reply(history: list[dict]) -> str:
    """
    history: list of {"role": "user"|"assistant", "content": str}, oldest first.
    Returns the assistant's reply text.
    """
    if not settings.AI_API_KEY:
        return _fallback_reply(history[-1]["content"] if history else "")

    url, payload, headers = _build_request(history)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        raise AIServiceError(f"AI API returned an error: {exc.response.status_code} {exc.response.text}") from exc
    except httpx.RequestError as exc:
        raise AIServiceError(f"Could not reach the AI API: {exc}") from exc

    text = _extract_reply(data)
    if not text:
        raise AIServiceError("AI API returned no text content.")
    return text
