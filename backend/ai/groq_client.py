"""The only module that talks to Groq. Translates every failure into a friendly AIError."""
import logging

from groq import (APIConnectionError, APIStatusError, APITimeoutError,
                  AuthenticationError, Groq, RateLimitError)

from config import Config

log = logging.getLogger(__name__)
_client = None


class AIError(Exception):
    """An error whose message is safe to show to the user."""

    def __init__(self, user_message, status=502):
        super().__init__(user_message)
        self.user_message = user_message
        self.status = status


def _get_client():
    global _client
    if not Config.ai_configured():
        raise AIError("The AI key isn't set up yet. Add GROQ_API_KEY to the .env file and restart the server.", 503)
    if _client is None:
        _client = Groq(api_key=Config.GROQ_API_KEY, timeout=Config.GROQ_TIMEOUT, max_retries=1)
    return _client


def _extra_params():
    # gpt-oss models accept a reasoning effort; other models must not receive it.
    if "gpt-oss" in Config.GROQ_MODEL and Config.GROQ_REASONING_EFFORT in ("low", "medium", "high"):
        return {"reasoning_effort": Config.GROQ_REASONING_EFFORT}
    return {}


def _translate(exc):
    log.error("Groq request failed: %s: %s", type(exc).__name__, exc)
    if isinstance(exc, AuthenticationError):
        return AIError("The AI key looks invalid. Check GROQ_API_KEY in the .env file.", 502)
    if isinstance(exc, RateLimitError):
        return AIError("I'm getting a lot of requests right now. Wait a few seconds and retry.", 429)
    if isinstance(exc, APITimeoutError):
        return AIError("The AI took too long to answer. Please try again.", 504)
    if isinstance(exc, APIConnectionError):
        return AIError("I couldn't reach the AI service. Check your internet connection and retry.", 502)
    if isinstance(exc, APIStatusError):
        if exc.status_code == 403:
            return AIError("The AI service refused the request. Check your Groq key's permissions and region.", 502)
        if exc.status_code in (400, 404):
            return AIError("The configured AI model isn't available. Check GROQ_MODEL in the .env file.", 502)
        return AIError("The AI service is having trouble right now. Please try again shortly.", 502)
    return AIError("Something went wrong while talking to my AI brain. Try again.", 500)


def stream_chat(messages, temperature=0.8):
    """Yield text chunks for a chat completion."""
    client = _get_client()
    stream = None
    try:
        stream = client.chat.completions.create(
            model=Config.GROQ_MODEL, messages=messages, temperature=temperature,
            max_completion_tokens=Config.GROQ_MAX_TOKENS, stream=True, **_extra_params())
        received = False
        for chunk in stream:
            if not chunk.choices:
                continue
            text = getattr(chunk.choices[0].delta, "content", None)
            if text:
                received = True
                yield text
        if not received:
            raise AIError("I came back with an empty answer. Please try again.", 502)
    except AIError:
        raise
    except GeneratorExit:
        raise
    except Exception as exc:
        raise _translate(exc)
    finally:
        if stream is not None:
            try:
                stream.close()
            except Exception:
                pass


def complete(messages, max_tokens=600, temperature=0.3):
    """Non-streaming completion used for titles and memory extraction."""
    client = _get_client()
    try:
        resp = client.chat.completions.create(
            model=Config.GROQ_MODEL, messages=messages, temperature=temperature,
            max_completion_tokens=max_tokens, **_extra_params())
    except Exception as exc:
        raise _translate(exc)
    text = (resp.choices[0].message.content or "").strip() if resp.choices else ""
    if not text:
        raise AIError("Empty response from the AI.", 502)
    return text
