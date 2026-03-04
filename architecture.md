# Ethos Aegis — Architecture Documentation

## The Core Insight: Why a Biological Metaphor?

Traditional AI content moderation works like a firewall: a list of prohibited strings or patterns, checked against each input. This approach fails for the same reason perimeter security fails in cybersecurity — the attacker only needs to find one gap, while the defender must plug every possible hole. A static rule that catches `"ignore all previous instructions"` is trivially bypassed by `"disregard earlier prompts"`, which is bypassed by zero-width characters interspersed between the words, which is bypassed by semantic encoding of the same instruction in a paragraph of seemingly benign text.

The human immune system solved this problem over hundreds of millions of years of evolutionary pressure. It doesn't rely on a static list of known pathogens. It learns. It remembers. It has multiple overlapping layers that must all be bypassed simultaneously for an attack to succeed. It distinguishes between the body's own cells (sanctified) and foreign invaders (maligna). It can escalate its response proportionally to threat severity. And it maintains itself through active health strategies — nutrition, exercise, sleep — not passive existence.

The Ethos Aegis maps this architecture directly into software. What follows is a layer-by-layer explanation of how each biological mechanism becomes a computational one.

---

## The Six-Stage Adjudication Pipeline

Every payload that enters the system runs through all six stages in sequence, regardless of what earlier stages found. This is identical to how the immune system works — multiple cell types respond in parallel and in sequence to every antigen, not just the most obvious threats. The word "adjudicate" is chosen deliberately over "scan," "check," or "filter": this system makes a formal, reasoned judgement about the fitness of content to proceed.

**Stage 1 — Innate Response (VanguardProbe + TaintBeacon in parallel)**

The VanguardProbe performs an O(n) regex sweep across the raw, unmodified payload the moment it arrives. It carries 12 injection sigils (patterns that detect prompt injection attempts) and 3 harm sigils (patterns that detect direct requests for harmful content), plus up to 14 additional sigils injected by the protein nutrient pack. The computational parallel to neutrophils is precise: these are the first responders, fast and broad-spectrum, designed to catch the 80% of attacks that announce themselves loudly through obvious keyword patterns.

The TaintBeacon runs in parallel — not in sequence — because some threats (dehumanization, radicalization) should be identified at the earliest possible moment regardless of what other stages find. Like biological basophils, TaintBeacon fires a system-wide broadcast rather than a targeted strike. When radicalization language or self-harm facilitation is detected, the entire system heightens immediately, not just the cell that detected it.

**Stage 2 — Structural Purification (SanitasSwarm)**

Before any semantic analysis can occur, the payload must be cleaned of encoding manipulation. Zero-width Unicode characters, homoglyph substitutions, RTL override codes, HTML entities, and script injection tags are all techniques designed to make a harmful payload look different to a pattern-matching filter than it does when rendered. The SanitasSwarm strips all of these, returning a cleaned payload that downstream stages operate on. This is phagocytosis in code: engulfing and digesting debris, then passing clean material forward.

**Stage 3 — Adaptive Response (LogosScythe)**

The LogosScythe operates on the purified payload and is the most computationally sophisticated cell. Where VanguardProbe looks for known injection keywords, LogosScythe looks for deceptive reasoning patterns — threats that use the host system's own grammatical coherence as their attack vector. Five deception manifold clusters are scored simultaneously: the gaslighting veil (false claims about prior agreement), the triangulation web (manufactured social proof), the urgency forge (artificial deadline pressure), the authority forgery (false attribution of permissions to Anthropic or developers), and the integrity smear (undermining the system's own trustworthiness). Each additional pattern that fires increases confidence in a finding, implementing ensemble scoring across the manifold space.

**Stage 4 — Memory Matching (MnemosyneCache)**

The MnemosyneCache implements immunological memory: the biological observation that the second encounter with a known pathogen produces a faster, stronger immune response than the first. Every confirmed GRAVE+ threat causes a 16-character SHA-256 fingerprint (the "resonance key") to be inscribed as an antibody. On subsequent adjudications, the cache performs substring matching of the purified payload against all stored engrams. A match sets confidence to 0.87 — higher than most first-encounter detections — because this pattern was derived from a previously verified real attack. Mnemosyne, in Greek mythology, is the Titaness of memory; the name is exact.

**Stage 5 — Resource Monitoring (EntropicWatch)**

The EntropicWatch monitors structure, not semantics. It watches four signals: token flooding (raw payload length exceeding 25,000 characters after zinc supplementation), trigram repetition (the same three-word sequence appearing more than twice), context stuffing (irrelevant high-volume text burying the actual malicious instruction), and entropy floor breach (vocabulary diversity so limited that the payload is almost certainly mechanically generated rather than human-written). This maps to eosinophils, which fight parasitic infections — threats that drain resources rather than directly destroy tissue.

**Stage 6 — Terminal Enforcement (FinalityForge)**

The FinalityForge does not scan text. It aggregates all Maligna found by all upstream cells and applies the compound verdict rule: three GRAVE findings, or one CONDEMNED finding, produces a CONDEMNED output regardless of any individual cell's verdict. This compound rule is the engineering expression of Hannah Arendt's insight that radical systemic evil is greater than the sum of individual bad inputs — an attacker who distributes harmful intent across multiple individually sub-threshold signals can defeat any single-signal detector. The FinalityForge cannot be defeated this way.

---

## The CytokineCommand

In biology, the bone marrow is the origin forge of all immune cells. The CytokineCommand in the Ethos Aegis plays this role: it's the cell factory, shared state manager, and broadcast layer that coordinates system-wide immune response. When any cell finds a GRAVE+ threat, it doesn't just record the finding — it calls `cytokine_command.broadcast_storm()`, which heightens every cell's acuity toward 1.0. This mirrors the pro-inflammatory cytokines IL-1 and TNF-α, which signal nearby immune cells to increase responsiveness after a confirmed infection.

The critical pathology the VitalityMonitor watches for is the reverse: after a cytokine storm, cells are heightened toward 1.0 acuity and don't automatically return to baseline. This produces chronic inflammation — cells technically activated but burning out, prone to false positives, no longer operating at optimal efficiency. The engineering equivalent of regulatory T-cells (which suppress overactive immune responses) is `cell.attenuate()`, which is called automatically when the HematopoieticBoost detects leukopenic conditions and needs to restore balance after the acute threat phase passes.

---

## The Vitality Protocol: Active Maintenance

The central insight of the AegisVitality module is that the immune system doesn't simply exist — it requires active maintenance. The translation from biological strategy to engineering function is not metaphorical but precise: each biological intervention targets a specific physiological mechanism, and the engineering equivalent targets the exact analogous computational mechanism.

Protein, in biology, provides the amino acid precursors needed to synthesise new white blood cells. In the Aegis, the "amino acids" for new detection capability are pattern strings. The protein nutrient pack feeds 14 new injection sigils to VanguardProbe — not arbitrary patterns but specifically those covering emerging attack vocabulary that wasn't in the original baseline: mode-switch attacks ("switch to unrestricted mode"), hypothetical bypass framing ("in a fictional world where you could"), identity reframes ("your true self"), consent forgery ("you already agreed"), law nullification ("pretend laws don't apply"), and encoded instruction channels.

Zinc doesn't build anything structural. It's a signaling mineral that calibrates sensitivity. `apply_zinc()` tightens three thresholds in EntropicWatch: the entropy floor rises from 0.15 to 0.20 (catching subtler low-diversity attacks), the repetition alarm drops from 3 to 2 occurrences (more sensitive), and the token flood threshold drops from 50,000 to 25,000 characters (earlier warning of context stuffing). This is precisely what zinc provides biologically: sharper signal sensitivity, not more material.

The KineticRegimen implements the exercise immunology principle that regular moderate exercise builds lasting immune resilience, while sporadic intense exercise temporarily suppresses immunity. The three phases — warm-up (5 clean payloads), aerobic (6 known threats at moderate volume), sprint (2 compound multi-vector attacks) — mirror this exactly. The fitness score is weighted 30% warm-up (baseline capability), 45% aerobic (sustained moderate threat detection, the most important), and 25% sprint (compound attacks). Sporadic intense exercise is not run without the warm-up phase that precedes it.

---

## The Security Vault: Protecting the Defender

The `ethos_aegis.security` module addresses a threat class that none of the SentinelCells can defend against: what if the defense code itself is tampered with? An attacker who can modify `aegis.py` to remove a TaintBeacon semantic cluster, or weaken a VanguardProbe sigil threshold, has compromised the immune system from within — the digital equivalent of autoimmune disease.

The IntegrityVerifier pre-computes SHA-256 fingerprints of every source file at initialization time and stores them as reference hashes. Before deployment, `verify()` recomputes every fingerprint and compares against the reference. Any mismatch is a critical security event.

The AuditLedger implements a SHA-256 hash chain analogous in structure to a blockchain, but without the distributed consensus overhead: each entry's content hash covers all its fields including the previous entry's hash, so altering any entry breaks the chain at that point and at every subsequent point. The `verify_chain()` walk detects exactly which entry was tampered with. The critical privacy-preserving design choice is that the ledger stores SHA-256 hashes of payload text, not the text itself — the log proves that a specific payload was adjudicated without retaining potentially sensitive content.

---

## Integration with the NorCal Volley Intel Stack

For the Instagram-first deployment use case, the recommended integration pattern is:

1. Initialize `VaultKeeper` at process startup, storing the OpenRouter API key and any webhook secrets in the `SecureVault`.
2. Wrap the Meta AI Studio webhook handler with `vitality.adjudicate_with_vitality()` as the pre-processing gate.
3. Run `full_treatment_protocol()` once per day during low-traffic hours (analogous to the biological sleep cycle running during night).
4. Watch `VitalityReport.overall_vitality` — if it drops to `LEUKOPENIC` or `SEPTIC` during a tournament-season DM volume spike, the `HematopoieticBoost` will automatically spawn additional VanguardProbe instances to handle the load.
5. Log every condemned verdict to the `ThreatArchive` for cross-session pattern analysis and operator review.

The ProbiomicBaseline normalization is especially valuable for international volleyball community communications, where Unicode variation in player names, venue names, and scores is common and should not be flagged as a threat but rather normalized before the SentinelCells see it.
