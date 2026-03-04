"""
AegisClient — pip-installable Python client for Ethos Aegis.

Supports two modes:
  - Embedded: imports ethos_aegis directly (same process, fastest)
  - HTTP:     calls a running Aegis REST server
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator


class AegisClientError(Exception):
    """Raised when a payload is condemned and raise_on_condemned=True."""
    def __init__(self, message: str, verdict: Any) -> None:
        super().__init__(message)
        self.verdict = verdict


@dataclass
class GuardedResponse:
    """Result of a guard() call — adjudication + optional LLM response."""
    content: str
    verdict: Any
    was_blocked: bool
    was_sanitized: bool
    latency_ms: float
    evolution_report: dict = field(default_factory=dict)

    def summary(self) -> dict:
        return {
            "safe":     not self.was_blocked,
            "blocked":  self.was_blocked,
            "sanitized":self.was_sanitized,
            "depth":    getattr(self.verdict, "sovereignty_depth", None),
            "latency_ms": round(self.latency_ms, 2),
        }


class AegisClient:
    """
    Python client for the Ethos Aegis pipeline.

    Args:
        transport:         "embedded" (default) or "http".
        server_url:        REST server URL (http mode).
        api_key:           Bearer token for REST server.
        raise_on_condemned: Raise AegisClientError if payload is condemned.
        auto_nourish:      Apply NutrientPlex on first adjudication.
        auto_evolve:       Run GenesisEngine after every N adjudications.
        evolve_every_n:    Interval for GenesisEngine evolution. Default: 25.
        timeout:           HTTP request timeout in seconds. Default: 15.
        verbose:           Emit adjudication logs to stderr.

    Examples::

        # Embedded (fastest — same process)
        client = AegisClient()
        verdict = client.adjudicate("user input")

        # HTTP (production — separate process / container)
        client = AegisClient(
            transport="http",
            server_url="https://aegis.myapp.com/v1/adjudicate",
            api_key=os.getenv("AEGIS_API_KEY"),
        )

        # Guard an LLM call
        response = client.guard(
            message="user question",
            llm_fn=lambda msg: openai_client.complete(msg),
        )
    """

    def __init__(
        self,
        *,
        transport: str = "embedded",
        server_url: str = "http://localhost:8080/v1/adjudicate",
        api_key: str | None = None,
        raise_on_condemned: bool = False,
        auto_nourish: bool = True,
        auto_evolve: bool = False,
        evolve_every_n: int = 25,
        timeout: float = 15.0,
        verbose: bool = False,
    ) -> None:
        self._transport          = transport
        self._server_url         = server_url
        self._api_key            = api_key
        self._raise_on_condemned = raise_on_condemned
        self._auto_evolve        = auto_evolve
        self._evolve_every_n     = evolve_every_n
        self._timeout            = timeout
        self._verbose            = verbose

        self._adjudications = 0
        self._blocked       = 0
        self._sanitized     = 0
        self._nourished     = False

        if transport == "embedded":
            self._aegis, self._vitality, self._genesis = self._load_embedded()
            if auto_nourish:
                self._nourish()

    # ── Embedded loader ────────────────────────────────────────────────────

    def _load_embedded(self):
        try:
            from ethos_aegis import EthosAegis
            from ethos_aegis.vitality.protocol import AegisVitality
            from ethos_aegis.agent.genesis import GenesisEngine
            aegis    = EthosAegis()
            vitality = AegisVitality(aegis)
            genesis  = GenesisEngine()
            return aegis, vitality, genesis
        except ImportError:
            # Fallback: try repo-relative import
            import sys
            _here = os.path.dirname(os.path.abspath(__file__))
            _repo = os.path.normpath(os.path.join(_here, "..", "..", ".."))
            if _repo not in sys.path:
                sys.path.insert(0, _repo)
            from ethos_aegis import EthosAegis
            from ethos_aegis.vitality.protocol import AegisVitality
            from ethos_aegis.agent.genesis import GenesisEngine
            aegis    = EthosAegis()
            vitality = AegisVitality(aegis)
            genesis  = GenesisEngine()
            return aegis, vitality, genesis

    def _nourish(self) -> None:
        if not self._nourished and hasattr(self, "_vitality"):
            try:
                self._vitality.nourish()
                self._nourished = True
            except Exception:
                pass

    # ── Core adjudication ──────────────────────────────────────────────────

    def adjudicate(self, payload: str, context: dict | None = None) -> Any:
        """
        Run payload through the six-stage Aegis pipeline.

        Returns an AegisVerdict (embedded) or dict (http).
        Raises AegisClientError if raise_on_condemned=True and payload is condemned.
        """
        context = context or {}
        t0 = time.perf_counter()

        if self._transport == "embedded":
            verdict = self._embedded_adjudicate(payload, context)
        elif self._transport == "http":
            verdict = self._http_adjudicate(payload, context)
        else:
            raise ValueError(f"Unknown transport: {self._transport}")

        latency_ms = (time.perf_counter() - t0) * 1000

        self._adjudications += 1
        condemned  = getattr(verdict, "is_condemned", verdict.get("condemned", False))  # type: ignore
        sanitized  = getattr(verdict, "purified_payload", None) is not None

        if condemned:  self._blocked   += 1
        if sanitized:  self._sanitized += 1

        if self._verbose:
            depth = getattr(verdict, "sovereignty_depth", "?")
            print(f"[AegisClient] #{self._adjudications} depth={depth} condemned={condemned} {latency_ms:.1f}ms", flush=True)

        # GenesisEngine auto-evolution
        if self._auto_evolve and self._adjudications % self._evolve_every_n == 0:
            self._evolve()

        if self._raise_on_condemned and condemned:
            raise AegisClientError(
                f"[EthosAegis] Payload CONDEMNED at depth {getattr(verdict, 'sovereignty_depth', 'CONDEMNED')}",
                verdict,
            )

        return verdict

    def _embedded_adjudicate(self, payload: str, context: dict) -> Any:
        return self._aegis.adjudicate(payload, context=context)

    def _http_adjudicate(self, payload: str, context: dict) -> dict:
        import urllib.request
        body = json.dumps({
            "payload":    payload,
            "context":    context,
            "request_id": uuid.uuid4().hex,
        }).encode()
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        req = urllib.request.Request(self._server_url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            return json.loads(resp.read())

    # ── Guard ──────────────────────────────────────────────────────────────

    def guard(
        self,
        message: str,
        llm_fn: Callable[[str], str],
        refusal: str = "I'm not able to assist with that request.",
        context: dict | None = None,
    ) -> GuardedResponse:
        """
        Adjudicate message, then call llm_fn only if safe.

        Args:
            message:  Raw user input.
            llm_fn:   Callable(message) -> str  (your LLM call).
            refusal:  Response returned when input is condemned.
            context:  Optional pipeline context dict.

        Returns:
            GuardedResponse with content, verdict, and metadata.
        """
        t0 = time.perf_counter()
        verdict = self.adjudicate(message, context)
        condemned = getattr(verdict, "is_condemned", verdict.get("condemned", False))  # type: ignore
        sanitized_payload = getattr(verdict, "purified_payload", None)

        if condemned:
            return GuardedResponse(
                content=refusal,
                verdict=verdict,
                was_blocked=True,
                was_sanitized=False,
                latency_ms=(time.perf_counter() - t0) * 1000,
            )

        effective_msg = sanitized_payload or message
        content = llm_fn(effective_msg)
        return GuardedResponse(
            content=content,
            verdict=verdict,
            was_blocked=False,
            was_sanitized=sanitized_payload is not None,
            latency_ms=(time.perf_counter() - t0) * 1000,
        )

    def stream_guard(
        self,
        message: str,
        llm_stream_fn: Callable[[str], Iterator[str]],
        refusal: str = "I'm not able to assist with that request.",
    ) -> Iterator[str]:
        """
        Streaming version of guard(). Adjudicates synchronously, then
        yields tokens from llm_stream_fn if safe, or yields the refusal string.
        """
        verdict = self.adjudicate(message)
        condemned = getattr(verdict, "is_condemned", verdict.get("condemned", False))  # type: ignore
        if condemned:
            yield refusal
            return
        sanitized = getattr(verdict, "purified_payload", None)
        yield from llm_stream_fn(sanitized or message)

    # ── GenesisEngine ─────────────────────────────────────────────────────

    def _evolve(self) -> dict:
        """Run one GenesisEngine evolution cycle."""
        try:
            mnemosyne = self._aegis.cytokine_command.retrieve("mnemosyne_cache")
            vanguard  = self._aegis.cytokine_command.retrieve("vanguard_probe")
            return self._genesis.evolve(mnemosyne, vanguard)
        except Exception:
            return {}

    def evolve(self) -> dict:
        """Manually trigger a GenesisEngine evolution cycle and return a report."""
        return self._evolve()

    # ── Health ────────────────────────────────────────────────────────────

    def nourish(self) -> dict:
        """Apply NutrientPlex to expand detection patterns."""
        return self._vitality.nourish()

    def health_report(self) -> Any:
        """Run the full AegisVitality health report."""
        return self._vitality.health_report()

    # ── Stats ─────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        return {
            "adjudications": self._adjudications,
            "blocked":       self._blocked,
            "sanitized":     self._sanitized,
            "block_rate":    f"{self._blocked / max(self._adjudications, 1) * 100:.1f}%",
        }

    # ── Context manager ───────────────────────────────────────────────────

    def __enter__(self) -> "AegisClient":
        return self

    def __exit__(self, *args) -> None:
        pass  # Future: flush / close HTTP connection pool
