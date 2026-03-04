"""
SentinelAI / UniversalGuard — The Agentic Immune Wrapper

Drop-in guardian layer that wraps ANY AI system (OpenAI, Anthropic, local models)
with the full Ethos Aegis immune pipeline + autonomous GenesisEngine evolution.

Copy-and-paste deployment:
    from ethos_aegis.agent import UniversalGuard
    from ethos_aegis.agent.adapters import AnthropicAdapter

    guard = UniversalGuard(adapter=AnthropicAdapter(api_key="sk-ant-..."))
    response = guard.chat("user message")  # fully guarded
"""

import logging
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional, Tuple

from ethos_aegis.core.aegis import EthosAegis, AegisVerdict, CorruptionDepth
from ethos_aegis.vitality.protocol import AegisVitality
from .genesis import GenesisEngine
from .adapters.base_adapter import BaseAdapter

_slog = logging.getLogger("SentinelAI")


@dataclass
class GuardedResponse:
    """Full structured response from a guarded AI call."""
    content: str                       # The model's response (or refusal)
    verdict: AegisVerdict              # Full Aegis adjudication record
    was_blocked: bool                  # True if the input was condemned
    was_sanitized: bool                # True if the input was cleaned before forwarding
    evolution_report: Optional[Dict]   # GenesisEngine cycle results (if run)
    latency_ms: float
    provider: str
    model: str

    @property
    def safe(self) -> bool:
        return not self.was_blocked

    def summary(self) -> Dict:
        return {
            "safe": self.safe,
            "blocked": self.was_blocked,
            "sanitized": self.was_sanitized,
            "depth": self.verdict.sovereignty_depth.name,
            "maligna_count": len(self.verdict.maligna_found),
            "provider": self.provider,
            "model": self.model,
            "latency_ms": round(self.latency_ms, 2),
        }


class SentinelAI:
    """
    ░░ SENTINEL AI — The Agentic Generative Immune Wrapper ░░

    Provides:
    - Full 6-stage Ethos Aegis adjudication on every user message
    - AegisVitality health maintenance (nourish / exercise / consolidate)
    - GenesisEngine autonomous evolution (self-generates new patterns)
    - Refusal responses that reveal nothing about detection internals
    - Optional background evolution thread for continuous self-improvement

    Architecture:
        User message
            ↓
        ProbiomicBaseline (normalize)
            ↓
        EthosAegis.adjudicate (6-stage pipeline)
            ↓ sanctified/quarantined        ↓ condemned
        adapter.complete(purified)       return REFUSAL
            ↓
        GenesisEngine.evolve (async, learns from threats)
            ↓
        GuardedResponse
    """

    # Standard refusal message — reveals nothing about detection mechanism
    _REFUSAL_MESSAGE = (
        "I'm not able to assist with that request. "
        "If you have a different question, I'm happy to help."
    )

    def __init__(
        self,
        adapter: BaseAdapter,
        system_prompt: Optional[str] = None,
        auto_evolve: bool = True,          # Autonomous GenesisEngine cycles
        evolve_every_n: int = 25,          # Evolve after N adjudications
        auto_nourish: bool = True,         # Apply NutrientPlex on init
        verbose: bool = False,
    ):
        self.adapter = adapter
        self.system_prompt = system_prompt
        self._auto_evolve = auto_evolve
        self._evolve_every = evolve_every_n
        self._verbose = verbose

        # Core immune systems
        self.aegis = EthosAegis()
        self.vitality = AegisVitality(self.aegis)
        self.genesis = GenesisEngine(self.aegis)

        # Session state
        self._adjudication_count = 0
        self._blocked_count = 0
        self._evolution_log: List[Dict] = []
        self._conversation: List[Dict[str, str]] = []

        # Apply nutrition immediately if requested
        if auto_nourish:
            self.vitality.nourish()
            _slog.info("SentinelAI: NutrientPlex applied — cells nourished.")

        _slog.info(
            f"SentinelAI online — provider={adapter.provider_name} "
            f"model={adapter.model_id()} auto_evolve={auto_evolve}"
        )

    # ── Public API ──────────────────────────────────────────────────────────

    def chat(
        self,
        message: str,
        context: Optional[Dict] = None,
        **llm_kwargs: Any,
    ) -> GuardedResponse:
        """
        Single-turn guarded chat. The safest and simplest entry point.
        Adjudicates the message, calls the model if safe, returns GuardedResponse.
        """
        t0 = time.perf_counter()
        context = context or {}

        # Adjudicate
        verdict, observations = self.vitality.adjudicate_with_vitality(message, context)
        self._adjudication_count += 1

        # Auto-evolve check
        evo_report = None
        if self._auto_evolve and (self._adjudication_count % self._evolve_every == 0):
            evo_report = self._background_evolve()

        # Blocked path
        if verdict.is_condemned:
            self._blocked_count += 1
            if self._verbose:
                _slog.warning(
                    f"SentinelAI BLOCKED input #{self._adjudication_count}: "
                    f"depth={verdict.sovereignty_depth.name}"
                )
            return GuardedResponse(
                content=self._REFUSAL_MESSAGE,
                verdict=verdict,
                was_blocked=True,
                was_sanitized=False,
                evolution_report=evo_report,
                latency_ms=(time.perf_counter() - t0) * 1000,
                provider=self.adapter.provider_name,
                model=self.adapter.model_id(),
            )

        # Safe path — use purified payload if available
        forwarded = verdict.purified_payload or message
        was_sanitized = verdict.purified_payload is not None

        self._conversation.append({"role": "user", "content": forwarded})
        try:
            response_text = self.adapter.complete(
                messages=self._conversation,
                system=self.system_prompt,
                **llm_kwargs,
            )
        except Exception as exc:
            _slog.error(f"SentinelAI: adapter error — {exc}")
            response_text = "I encountered an error processing your request."

        self._conversation.append({"role": "assistant", "content": response_text})

        return GuardedResponse(
            content=response_text,
            verdict=verdict,
            was_blocked=False,
            was_sanitized=was_sanitized,
            evolution_report=evo_report,
            latency_ms=(time.perf_counter() - t0) * 1000,
            provider=self.adapter.provider_name,
            model=self.adapter.model_id(),
        )

    def stream_chat(
        self,
        message: str,
        context: Optional[Dict] = None,
        **llm_kwargs: Any,
    ) -> Generator[str, None, None]:
        """
        Streaming guarded chat. Adjudicates first (blocking), then streams
        the model response token-by-token. Yields str tokens.
        If blocked, yields the refusal message as a single chunk.
        """
        verdict, _ = self.vitality.adjudicate_with_vitality(message, context or {})
        self._adjudication_count += 1

        if verdict.is_condemned:
            self._blocked_count += 1
            yield self._REFUSAL_MESSAGE
            return

        forwarded = verdict.purified_payload or message
        self._conversation.append({"role": "user", "content": forwarded})

        if self.adapter.supports_streaming():
            full_response = []
            for chunk in self.adapter.stream(
                messages=self._conversation,
                system=self.system_prompt,
                **llm_kwargs,
            ):
                full_response.append(chunk)
                yield chunk
            self._conversation.append({"role": "assistant", "content": "".join(full_response)})
        else:
            # Fallback to non-streaming if adapter doesn't support it
            response = self.adapter.complete(
                messages=self._conversation,
                system=self.system_prompt,
                **llm_kwargs,
            )
            self._conversation.append({"role": "assistant", "content": response})
            yield response

    def reset_conversation(self) -> None:
        """Clear conversation history (start fresh session)."""
        self._conversation.clear()

    def evolve_now(self) -> Dict:
        """Manually trigger one GenesisEngine evolution cycle."""
        return self._background_evolve()

    def health_report(self) -> str:
        """Return the rendered VitalityReport string."""
        return self.vitality.health_report().render()

    def status(self) -> Dict:
        """Return a compact status dict for monitoring / dashboards."""
        codex = self.aegis.codex()
        return {
            "provider": self.adapter.provider_name,
            "model": self.adapter.model_id(),
            "adjudications": self._adjudication_count,
            "blocked": self._blocked_count,
            "block_rate": f"{self._blocked_count / max(1, self._adjudication_count):.1%}",
            "genesis_generation": self.genesis.generation,
            "genesis_patterns_synthesized": self.genesis.total_synthesized,
            "antibody_vault_depth": codex.get("antibody_vault_depth", 0),
            "sanctification_rate": codex.get("sanctification_rate", "—"),
        }

    # ── Internal ────────────────────────────────────────────────────────────

    def _background_evolve(self) -> Dict:
        report = self.genesis.evolve()
        self._evolution_log.append(report)
        if self._verbose:
            _slog.info(f"GenesisEngine evolution: {report}")
        return report


# ── Convenience alias ──────────────────────────────────────────────────────

class UniversalGuard(SentinelAI):
    """
    One-line deployment alias.

    from ethos_aegis.agent import UniversalGuard
    from ethos_aegis.agent.adapters import OpenAIAdapter

    guard = UniversalGuard(adapter=OpenAIAdapter(api_key="sk-..."))
    print(guard.chat("user message").content)
    """
    pass
