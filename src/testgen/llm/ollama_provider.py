from __future__ import annotations

import json

from ..config import Config
from .base import LLMResponse, ToolCall


def _get(obj: object, key: str):
    """Ollama responses may arrive as pydantic objects or plain dicts; handle both."""
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


class OllamaProvider:
    """LLMProvider for Ollama (cloud or local), with native tool calling."""

    name = "ollama"

    def __init__(self, config: Config, api_key: str | None = None) -> None:
        from ollama import Client

        api_key = api_key or __import__("os").environ.get("OLLAMA_API_KEY")
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.client = Client(host=config.ollama_host, headers=headers)
        self.model = config.model
        self.temperature = config.temperature

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> LLMResponse:
        kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "options": {"temperature": self.temperature},
        }
        if tools:
            kwargs["tools"] = tools

        try:
            response = self.client.chat(**kwargs)
        except Exception as e:
            raise RuntimeError(f"Ollama chat failed: {e}") from e

        message = _get(response, "message") or {}
        content = _get(message, "content")

        calls: list[ToolCall] = []
        for raw in _get(message, "tool_calls") or []:
            fn = _get(raw, "function") or {}
            arguments = _get(fn, "arguments") or {}
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}
            calls.append(ToolCall(name=_get(fn, "name"), arguments=dict(arguments)))

        return LLMResponse(content=content or None, tool_calls=calls)
