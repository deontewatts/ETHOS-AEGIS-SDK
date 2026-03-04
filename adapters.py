"""
ethos_aegis_sdk.adapters — Re-exports all UniversalGuard adapters.

from ethos_aegis_sdk.adapters import (
    OpenAIAdapter, AnthropicAdapter, MistralAdapter,
    GeminiAdapter, GeminiVertexAdapter, GenericAdapter,
)
"""
from __future__ import annotations

import importlib
import sys
import os

def _ensure_repo_on_path() -> None:
    _here = os.path.dirname(os.path.abspath(__file__))
    _repo = os.path.normpath(os.path.join(_here, "..", "..", ".."))
    if _repo not in sys.path:
        sys.path.insert(0, _repo)

_ensure_repo_on_path()

from ethos_aegis.agent.adapters.base_adapter     import BaseAdapter
from ethos_aegis.agent.adapters.openai_adapter   import OpenAIAdapter
from ethos_aegis.agent.adapters.anthropic_adapter import AnthropicAdapter
from ethos_aegis.agent.adapters.generic_adapter  import GenericAdapter
from ethos_aegis.agent.adapters.mistral_adapter  import MistralAdapter
from ethos_aegis.agent.adapters.gemini_adapter   import GeminiAdapter, GeminiVertexAdapter

__all__ = [
    "BaseAdapter",
    "OpenAIAdapter",
    "AnthropicAdapter",
    "MistralAdapter",
    "GeminiAdapter",
    "GeminiVertexAdapter",
    "GenericAdapter",
]
