"""tenacity retry/backoff around every chat-model call made by the graph.

The graph nodes (``rag_agent/nodes.py``) only use three entry points on the
model object: ``invoke``, ``bind_tools(...).invoke`` and
``with_structured_output(...).invoke``. :func:`wrap_chat_model` proxies exactly
those, so retrying is added without touching the nodes or their prompts.

Only transient failures are retried — timeouts, connection errors, HTTP 429 and
5xx. Auth/validation errors fail immediately, because retrying them just delays
the error. When a call still fails after the configured attempts the wrapper
raises :class:`LLMRetryExhausted`; the API catches it and turns the turn into a
fallback answer (see ``RagService.stream_answer``) rather than a failed request.
"""
from __future__ import annotations

import logging
from typing import Any

from tenacity import (
    RetryError,
    Retrying,
    before_sleep_log,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from api.settings import settings

logger = logging.getLogger("api.llm")


class LLMRetryExhausted(RuntimeError):
    """The model stayed unavailable after every retry attempt."""

    def __init__(self, message: str, *, attempts: int, last_error: BaseException | None = None) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.last_error = last_error


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True

    try:
        import httpx
    except ImportError:  # pragma: no cover - httpx ships with the openai client
        httpx = None  # type: ignore[assignment]
    if httpx is not None and isinstance(exc, (httpx.TimeoutException, httpx.TransportError)):
        return True

    try:
        import openai
    except ImportError:  # pragma: no cover - ChatDeepSeek requires the openai SDK
        openai = None  # type: ignore[assignment]
    if openai is not None:
        transient = (
            openai.APIConnectionError,
            openai.APITimeoutError,
            openai.RateLimitError,
            openai.InternalServerError,
        )
        if isinstance(exc, transient):
            return True
        status_code = getattr(exc, "status_code", None)
        if isinstance(status_code, int) and (status_code == 429 or status_code >= 500):
            return True

    return False


def _invoke_with_retry(fn, *args: Any, **kwargs: Any) -> Any:
    """Call ``fn`` with exponential backoff + jitter; raise on exhaustion."""
    attempts = settings.llm_max_attempts
    retryer = Retrying(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential_jitter(
            initial=settings.llm_retry_initial_wait,
            max=settings.llm_retry_max_wait,
            jitter=settings.llm_retry_jitter,
        ),
        retry=retry_if_exception(_is_retryable),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=False,
    )
    try:
        for attempt in retryer:
            with attempt:
                return fn(*args, **kwargs)
    except RetryError as exc:
        last = exc.last_attempt.exception() if exc.last_attempt else None
        raise LLMRetryExhausted(
            f"LLM call failed after {attempts} attempts: {last}",
            attempts=attempts,
            last_error=last,
        ) from last
    raise LLMRetryExhausted(  # pragma: no cover - the loop always returns or raises
        f"LLM call failed after {attempts} attempts",
        attempts=attempts,
    )


class _RetryingRunnable:
    """Proxy for the runnables returned by ``bind_tools`` / structured output."""

    def __init__(self, runnable: Any) -> None:
        self._runnable = runnable

    def invoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any:
        return _invoke_with_retry(self._runnable.invoke, input, config=config, **kwargs)

    def __getattr__(self, name: str) -> Any:  # stream/ainvoke/config passthrough
        return getattr(self._runnable, name)


class RetryingChatModel:
    """Drop-in chat-model proxy that retries transient API failures."""

    def __init__(self, model: Any) -> None:
        self._model = model

    def invoke(self, *args: Any, **kwargs: Any) -> Any:
        return _invoke_with_retry(self._model.invoke, *args, **kwargs)

    def bind_tools(self, tools: Any, **kwargs: Any) -> _RetryingRunnable:
        return _RetryingRunnable(self._model.bind_tools(tools, **kwargs))

    def with_structured_output(self, schema: Any, **kwargs: Any) -> _RetryingRunnable:
        return _RetryingRunnable(self._model.with_structured_output(schema, **kwargs))

    def __getattr__(self, name: str) -> Any:  # model_name, temperature, ...
        return getattr(self._model, name)


def wrap_chat_model(model: Any) -> Any:
    """Return a retrying proxy, or the model itself when retries are disabled."""
    if not settings.llm_retry_enabled:
        return model
    return RetryingChatModel(model)
