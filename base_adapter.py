"""
Base adapter interface — all AI system adapters implement this contract.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseAdapter(ABC):
    """
    Universal adapter contract for wrapping any LLM with Ethos Aegis protection.
    Implement this class to guard any AI system: OpenAI, Anthropic, Mistral,
    local models (Ollama, llama.cpp), or any custom inference endpoint.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier, e.g. 'openai', 'anthropic'."""

    @abstractmethod
    def complete(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Send messages to the underlying model and return the response text.
        The SentinelAI wrapper calls this AFTER the payload has been adjudicated
        and ONLY if the verdict is not CONDEMNED.
        """

    @abstractmethod
    def stream(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Streaming variant. Yields response chunks.
        Implement as a generator that yields str tokens.
        """

    def supports_streaming(self) -> bool:
        """Override to True if the adapter supports streaming."""
        return False

    def model_id(self) -> str:
        """Return the active model identifier string."""
        return "unknown"
