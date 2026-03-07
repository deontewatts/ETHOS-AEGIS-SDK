"""
Anthropic adapter — wraps anthropic>=0.25 (Messages API).
Install: pip install anthropic
"""
from typing import Any, Dict, Generator, List, Optional
from .base_adapter import BaseAdapter


class AnthropicAdapter(BaseAdapter):
    """
    Adapter for Anthropic Claude models via the Messages API.

    Usage:
        adapter = AnthropicAdapter(api_key="sk-ant-...", model="claude-sonnet-4-6")
        guard = UniversalGuard(adapter=adapter)
        response = guard.chat("user message here")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 4096,
        timeout: float = 60.0,
    ):
        try:
            import anthropic as _anthropic
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Run: pip install anthropic"
            )

        self._client = _anthropic.Anthropic(api_key=api_key, timeout=timeout)
        self._model = model
        self._max_tokens = max_tokens

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def model_id(self) -> str:
        return self._model

    def complete(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        kwargs.setdefault("max_tokens", self._max_tokens)
        response = self._client.messages.create(
            model=self._model,
            system=system or "",
            messages=messages,
            **kwargs,
        )
        return response.content[0].text if response.content else ""

    def stream(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        kwargs.setdefault("max_tokens", self._max_tokens)
        with self._client.messages.stream(
            model=self._model,
            system=system or "",
            messages=messages,
            **kwargs,
        ) as stream:
            for text in stream.text_stream:
                yield text

    def supports_streaming(self) -> bool:
        return True
