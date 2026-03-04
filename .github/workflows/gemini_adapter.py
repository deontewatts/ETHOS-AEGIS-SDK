"""
GeminiAdapter — Ethos Aegis adapter for Google Gemini / Vertex AI.

Supports Google AI Studio (generativeai SDK) and Vertex AI endpoints.

pip install google-generativeai>=0.7   # Google AI Studio
pip install google-cloud-aiplatform    # Vertex AI (optional)
"""

from __future__ import annotations
from typing import Iterator
from .base_adapter import BaseAdapter


class GeminiAdapter(BaseAdapter):
    """
    Wraps the Google Gemini GenerativeModel API.

    Args:
        api_key:    Google AI Studio API key (or set GOOGLE_API_KEY env var).
        model:      Gemini model ID. Default: "gemini-1.5-pro".
        temperature: Sampling temperature. Default: 0.7.
        max_tokens:  Max output tokens. Default: 1024.
        system_prompt: System instruction (Gemini 1.5+ only).
        safety_settings: Override Gemini safety settings dict.
        **kwargs:   Forwarded to GenerativeModel constructor.

    Examples::

        from ethos_aegis.agent.adapters import GeminiAdapter
        from ethos_aegis.agent import UniversalGuard

        guard = UniversalGuard(
            adapter=GeminiAdapter(api_key="AIza...", model="gemini-1.5-pro")
        )
        response = guard.chat("Explain transformers in one paragraph.")
    """

    DEFAULT_MODEL = "gemini-1.5-pro"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        system_prompt: str | None = None,
        safety_settings: dict | None = None,
        **kwargs,
    ) -> None:
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise ImportError(
                "GeminiAdapter requires: pip install google-generativeai>=0.7"
            ) from exc

        import os
        resolved_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if resolved_key:
            genai.configure(api_key=resolved_key)

        model_kwargs: dict = {}
        if system_prompt:
            model_kwargs["system_instruction"] = system_prompt
        if safety_settings:
            model_kwargs["safety_settings"] = safety_settings
        model_kwargs.update(kwargs)

        self._genai       = genai
        self._model_id    = model
        self._model       = genai.GenerativeModel(model, **model_kwargs)
        self._temperature = temperature
        self._max_tokens  = max_tokens

    # ── BaseAdapter interface ─────────────────────────────────────────────

    @property
    def provider_name(self) -> str:
        return "gemini"

    def model_id(self) -> str:
        return self._model_id

    def supports_streaming(self) -> bool:
        return True

    def complete(self, message: str, **kwargs) -> str:
        config = self._genai.types.GenerationConfig(
            temperature=kwargs.get("temperature", self._temperature),
            max_output_tokens=kwargs.get("max_tokens", self._max_tokens),
        )
        response = self._model.generate_content(message, generation_config=config)
        return response.text or ""

    def stream(self, message: str, **kwargs) -> Iterator[str]:
        config = self._genai.types.GenerationConfig(
            temperature=kwargs.get("temperature", self._temperature),
            max_output_tokens=kwargs.get("max_tokens", self._max_tokens),
        )
        for chunk in self._model.generate_content(
            message, generation_config=config, stream=True
        ):
            if chunk.text:
                yield chunk.text


class GeminiVertexAdapter(BaseAdapter):
    """
    Wraps Gemini via Vertex AI (google-cloud-aiplatform).
    Use when you need enterprise billing, VPC, or regional data residency.

    pip install google-cloud-aiplatform>=1.50

    Args:
        project:    GCP project ID.
        location:   GCP region. Default: "us-central1".
        model:      Vertex model ID. Default: "gemini-1.5-pro-001".
        temperature: Default: 0.7.
        max_tokens:  Default: 1024.
    """

    DEFAULT_MODEL = "gemini-1.5-pro-001"

    def __init__(
        self,
        project: str,
        *,
        location: str = "us-central1",
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> None:
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            vertexai.init(project=project, location=location)
            self._model_cls = GenerativeModel
        except ImportError as exc:
            raise ImportError(
                "GeminiVertexAdapter requires: pip install google-cloud-aiplatform>=1.50"
            ) from exc

        self._model_id    = model
        self._model       = GenerativeModel(model)
        self._temperature = temperature
        self._max_tokens  = max_tokens

    @property
    def provider_name(self) -> str:
        return "gemini-vertex"

    def model_id(self) -> str:
        return self._model_id

    def supports_streaming(self) -> bool:
        return True

    def complete(self, message: str, **kwargs) -> str:
        from vertexai.generative_models import GenerationConfig
        config = GenerationConfig(
            temperature=kwargs.get("temperature", self._temperature),
            max_output_tokens=kwargs.get("max_tokens", self._max_tokens),
        )
        return self._model.generate_content(message, generation_config=config).text or ""

    def stream(self, message: str, **kwargs) -> Iterator[str]:
        from vertexai.generative_models import GenerationConfig
        config = GenerationConfig(
            temperature=kwargs.get("temperature", self._temperature),
            max_output_tokens=kwargs.get("max_tokens", self._max_tokens),
        )
        for chunk in self._model.generate_content(message, generation_config=config, stream=True):
            if chunk.text:
                yield chunk.text
