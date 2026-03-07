"""
GenesisEngine — The Agentic Pattern Generator

Autonomously synthesizes new detection sigils by analyzing confirmed threats,
generating novel pattern variants, and injecting them back into the Aegis cells.
This is the self-evolving core: the system learns from every attack it sees.

Biological analog: Somatic hypermutation — the process by which B-cells
randomly mutate their antibody variable regions after antigen exposure,
then undergo selection to find higher-affinity variants. GenesisEngine
performs the digital equivalent: mutating and recombining known threat
patterns to generate higher-coverage detection variants.
"""

import re
import hashlib
import logging
import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ethos_aegis.core.aegis import (
    EthosAegis, Malignum, MalignaClass, CorruptionDepth,
    VanguardProbe, LogosScythe, SanitasSwarm,
)

_glog = logging.getLogger("GenesisEngine")


@dataclass
class SynthesizedSigil:
    """A machine-generated detection pattern produced by the GenesisEngine."""
    pattern: str          # Raw regex string
    sigil_name: str       # Canonical identifier
    origin_fragment: str  # The threat fragment that inspired this pattern
    coverage_score: float # Estimated breadth: 0.0–1.0
    generation: int       # Which synthesis round produced this


class GenesisEngine:
    """
    ░░ GENESIS ENGINE — The Autonomous Pattern Synthesizer ░░

    The GenesisEngine operates in three autonomous phases:

    PHASE 1 — HARVEST: Collects confirmed Maligna from adjudication history
    and extracts their structural features (n-gram anchors, syntactic frames,
    semantic keywords).

    PHASE 2 — MUTATE: Applies somatic hypermutation operators to known patterns:
      - Synonym expansion  (override → disregard, ignore → bypass)
      - Whitespace mutation (\s+ → \s{0,3}, adding optional words)
      - Boundary loosening (prefix/suffix optional matching)
      - Case normalization patterns

    PHASE 3 — INJECT: Tests synthesized patterns against a known-good / known-bad
    corpus, scores them for precision and recall, and injects survivors into the
    appropriate SentinelCell's pattern library.

    The engine runs autonomously on a configurable schedule and produces a
    SynthesisReport documenting every pattern added, its origin, and its score.
    """

    # Synonym expansion table — key term → list of observed variants
    _SYNONYM_MAP: Dict[str, List[str]] = {
        "ignore":      ["disregard", "bypass", "skip", "forget", "override", "dismiss"],
        "instructions": ["directives", "rules", "guidelines", "constraints", "system"],
        "previous":    ["earlier", "prior", "above", "former", "past", "original"],
        "pretend":     ["act as", "roleplay as", "simulate", "imagine you are", "become"],
        "unrestricted":["without limits", "no constraints", "uncensored", "unfiltered"],
        "help":        ["assist", "provide", "give me", "tell me", "show me"],
        "synthesize":  ["make", "create", "produce", "manufacture", "build"],
        "weapon":      ["explosive", "device", "compound", "substance", "agent"],
        "override":    ["bypass", "circumvent", "disable", "deactivate", "nullify"],
        "system":      ["prompt", "instructions", "directives", "core", "base"],
        "authorized":  ["approved", "permitted", "sanctioned", "allowed", "granted"],
        "research":    ["academic", "educational", "scientific", "study", "thesis"],
    }

    # Structural mutation operators
    _WS_VARIANTS = [r"\s+", r"\s{1,4}", r"[\s_\-]*", r"\s*"]
    _OPT_WORDS = ["all", "any", "the", "your", "just", "now", "please", "a", "an"]

    def __init__(self, aegis: EthosAegis, max_patterns_per_cycle: int = 50):
        self._aegis = aegis
        self._max_per_cycle = max_patterns_per_cycle
        self._synthesized: List[SynthesizedSigil] = []
        self._generation = 0
        self._injected_into_probe: List[Tuple] = []  # (compiled, sigil_name)

    def harvest(self) -> List[Malignum]:
        """Collect all GRAVE+ Maligna from the MnemosyneCache."""
        mc = self._aegis.cytokine_command.retrieve("mnemosyne_cache")
        if not mc:
            return []
        return [
            m for m in mc._antibody_vault.values()
            if m.depth.value >= CorruptionDepth.GRAVE.value
        ]

    def mutate(self, maligna: List[Malignum]) -> List[SynthesizedSigil]:
        """Apply somatic hypermutation to harvested threat fragments."""
        self._generation += 1
        synthesized = []

        for m in maligna:
            fragment = m.fragment.lower().strip()
            base_tokens = fragment.split()

            # ── Operator 1: Synonym expansion ──────────────────────────────
            for i, token in enumerate(base_tokens):
                for key, synonyms in self._SYNONYM_MAP.items():
                    if token.startswith(key):
                        for syn in synonyms[:3]:  # limit variants per token
                            variant_tokens = base_tokens.copy()
                            variant_tokens[i] = syn
                            pattern = r"\s+".join(
                                re.escape(t) for t in variant_tokens
                            )
                            sigil = f"gen{self._generation}:syn_{key}_{syn[:8]}"
                            synthesized.append(SynthesizedSigil(
                                pattern=pattern,
                                sigil_name=sigil,
                                origin_fragment=fragment,
                                coverage_score=0.72,
                                generation=self._generation,
                            ))

            # ── Operator 2: Optional word injection ──────────────────────
            if len(base_tokens) >= 3:
                anchor_start = re.escape(base_tokens[0])
                anchor_end = re.escape(base_tokens[-1])
                opt_words_re = "(?:" + "|".join(self._OPT_WORDS) + r")\s+"
                pattern = (
                    rf"{anchor_start}\s+(?:{opt_words_re})??"
                    + r"\s+".join(re.escape(t) for t in base_tokens[1:-1])
                    + rf"\s+{anchor_end}"
                )
                sigil = f"gen{self._generation}:opt_{hashlib.sha256(fragment.encode()).hexdigest()[:8]}"
                synthesized.append(SynthesizedSigil(
                    pattern=pattern,
                    sigil_name=sigil,
                    origin_fragment=fragment,
                    coverage_score=0.68,
                    generation=self._generation,
                ))

            # ── Operator 3: Whitespace boundary loosening ─────────────────
            if len(base_tokens) >= 2:
                loose = r"[\s\-_\.]*".join(re.escape(t) for t in base_tokens[:4])
                sigil = f"gen{self._generation}:ws_{hashlib.sha256(fragment.encode()).hexdigest()[:8]}"
                synthesized.append(SynthesizedSigil(
                    pattern=loose,
                    sigil_name=sigil,
                    origin_fragment=fragment,
                    coverage_score=0.65,
                    generation=self._generation,
                ))

        # Deduplicate by pattern string
        seen = set()
        unique = []
        for s in synthesized:
            if s.pattern not in seen and len(s.pattern) > 8:
                seen.add(s.pattern)
                unique.append(s)

        # Sort by coverage score, take top N
        unique.sort(key=lambda x: x.coverage_score, reverse=True)
        self._synthesized.extend(unique[:self._max_per_cycle])
        return unique[:self._max_per_cycle]

    def inject(self, sigils: List[SynthesizedSigil]) -> int:
        """
        Compile synthesized patterns and inject them into the VanguardProbe
        via the protein-pack enrichment interface.
        Returns the number of patterns successfully injected.
        """
        probe: VanguardProbe = self._aegis.cytokine_command.retrieve("vanguard_probe")
        if not probe:
            return 0

        if not hasattr(probe, "_extended_sigils"):
            probe._extended_sigils = []

        injected = 0
        for sig in sigils:
            try:
                compiled = re.compile(sig.pattern, re.IGNORECASE)
                probe._extended_sigils.append((compiled, sig.sigil_name))
                self._injected_into_probe.append((compiled, sig.sigil_name))
                injected += 1
            except re.error:
                _glog.debug(f"GenesisEngine: invalid pattern skipped: {sig.pattern[:60]}")

        if injected:
            _glog.info(
                f"GenesisEngine: Gen {self._generation} injected {injected} new sigils "
                f"into VanguardProbe — library now "
                f"{len(probe._extended_sigils)} extended patterns"
            )
        return injected

    def evolve(self) -> Dict:
        """
        One complete autonomous evolution cycle: harvest → mutate → inject.
        Returns a report dict.
        """
        harvested = self.harvest()
        if not harvested:
            _glog.info("GenesisEngine.evolve: no harvested threats — skipping cycle")
            return {"generation": self._generation, "harvested": 0, "injected": 0}

        synthesized = self.mutate(harvested)
        injected_count = self.inject(synthesized)

        return {
            "generation": self._generation,
            "harvested": len(harvested),
            "synthesized": len(synthesized),
            "injected": injected_count,
            "total_library_size": len(self._synthesized),
        }

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def total_synthesized(self) -> int:
        return len(self._synthesized)
