"""
OpenAI adapter — wraps openai>=1.0 (ChatCompletion).
Install: pip install openai
"""
from typing import Any, Dict, Generator, List, Optional
from .base_adapter import BaseAdapter


class OpenAIAdapter(BaseAdapter):
    """
    Drop-in adapter for any OpenAI-compatible endpoint.
    Works with: OpenAI, Azure OpenAI, OpenRouter, Groq, Together AI,
    Anyscale, Fireworks, and any server that speaks the OpenAI wire format.

    Usage:
        adapter = OpenAIAdapter(api_key="sk-...", model="gpt-4o")
        guard = UniversalGuard(adapter=adapter)
        response = guard.chat("user message here")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        base_url: Optional[str] = None,       # Override for OpenRouter/Groq/etc.
        organization: Optional[str] = None,
        timeout: float = 30.0,
    ):
        try:
            import openai as _openai
        except ImportError:
            raise ImportError(
                "openai package not installed. Run: pip install openai"
            )

        self._client = _openai.OpenAI(
            api_key=api_key,
            base_url=base_url,
            organization=organization,
            timeout=timeout,
        )
        self._model = model

    @property
    def provider_name(self) -> str:
        return "openai"

    def model_id(self) -> str:
        return self._model

    def complete(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        response = self._client.chat.completions.create(
            model=self._model,
            messages=full_messages,
            **kwargs,
        )
        return response.choices[0].message.content or ""

    def stream(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        with self._client.chat.completions.create(
            model=self._model,
            messages=full_messages,
            stream=True,
            **kwargs,
        ) as stream:
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta

    def supports_streaming(self) -> bool:
        return True
