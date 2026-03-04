"""
Generic HTTP adapter — wraps any OpenAI-compatible REST endpoint.
No external dependencies beyond the stdlib `urllib`.
"""
import json
import urllib.request
import urllib.error
from typing import Any, Dict, Generator, List, Optional
from .base_adapter import BaseAdapter


class GenericAdapter(BaseAdapter):
    """
    Zero-dependency adapter for any OpenAI-compatible HTTP endpoint.
    Works with: Ollama, llama.cpp server, LM Studio, vLLM, and any server
    that accepts POST /v1/chat/completions with the OpenAI message format.

    Usage:
        adapter = GenericAdapter(
            base_url="http://localhost:11434/v1",
            model="llama3",
            api_key="ollama",     # many local servers accept any string
        )
        guard = UniversalGuard(adapter=adapter)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model: str = "llama3",
        api_key: str = "local",
        timeout: float = 60.0,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._timeout = timeout

    @property
    def provider_name(self) -> str:
        return "generic"

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

        body = json.dumps({
            "model": self._model,
            "messages": full_messages,
            "stream": False,
            **kwargs,
        }).encode()

        req = urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]

    def stream(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        # Fallback: non-streaming complete
        yield self.complete(messages, system, **kwargs)

    def supports_streaming(self) -> bool:
        return False
