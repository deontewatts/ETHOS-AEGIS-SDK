# Ethos Aegis — Security Log

This log records security events, vulnerability disclosures, patch history,
and sponsorship-related security audits. Maintained as a permanent append-only record.

---

## Format

Each entry follows:

```
## [YYYY-MM-DD] SEVERITY: TITLE
**Type**: CVE / Advisory / Audit / Dependency / Incident
**Status**: Open | Patched | Won't Fix | Informational
**Reporter**: Name / Handle (or "Internal")
**Advisory**: https://github.com/ethos-aegis/ethos-aegis/security/advisories/GHSA-XXXX
**CVE**: CVE-YYYY-NNNNN (if assigned)

Description and remediation notes.
```

---

## Log

### [2026-03-03] INFO: Initial security baseline established
**Type**: Audit  
**Status**: Informational  
**Reporter**: Internal  

Security baseline set at v1.0.0:
- Zero runtime dependencies (stdlib only) — eliminates supply chain risk
- HMAC-SHA256 verdict signing via `SessionSeal`
- SHA-256 hash-chained `AuditLedger` — tamper detection on all records
- Non-root Docker runtime (uid/gid 1001 `aegis`)
- `SecureVault` XOR+HMAC config encryption — no plaintext API keys
- `IntegrityVerifier` source fingerprinting — detects code tampering
- `ThreatArchive` NDJSON — persistent adversarial event log

---

## Dependency Security Tracking

Dependabot is configured to scan all package ecosystems weekly:

| Ecosystem | Config Location | Schedule |
|-----------|----------------|----------|
| pip | `/.github/dependabot.yml` | Monday 03:00 PST |
| npm | `/.github/dependabot.yml` | Monday 03:00 PST |
| gomod | `/.github/dependabot.yml` | Monday 03:00 PST |
| cargo | `/.github/dependabot.yml` | Monday 03:00 PST |
| docker | `/.github/dependabot.yml` | Tuesday 03:00 PST |
| github-actions | `/.github/dependabot.yml` | Tuesday 03:00 PST |

Dependabot alerts → https://github.com/ethos-aegis/ethos-aegis/security/dependabot

---

## GitHub Security Features Status

| Feature | Status | Link |
|---------|--------|------|
| Private vulnerability reporting | Enabled | https://github.com/ethos-aegis/ethos-aegis/security |
| Security advisories | Enabled | https://github.com/ethos-aegis/ethos-aegis/security/advisories |
| Dependabot alerts | Enabled | https://github.com/ethos-aegis/ethos-aegis/security/dependabot |
| Dependabot security updates | Enabled | (auto PRs) |
| CodeQL analysis | Enabled | https://github.com/ethos-aegis/ethos-aegis/security/code-scanning |
| Secret scanning | Enabled | https://github.com/ethos-aegis/ethos-aegis/security/secret-scanning |
| Push protection | Enabled | (blocks secret commits) |

Enable all features at: `https://github.com/ethos-aegis/ethos-aegis/settings/security_analysis`

---

## Sponsorship Log

New sponsorships, changes, and cancellations are tracked below.
GitHub Sponsors management: https://github.com/sponsors/ethos-aegis

| Date | Event | Tier | Notes |
|------|-------|------|-------|
| — | — | — | No sponsors yet — be the first: https://github.com/sponsors/ethos-aegis |

### Sponsorship Tiers (configure at https://github.com/sponsors/ethos-aegis/dashboard/tiers)

| Tier | Monthly | Benefits |
|------|---------|----------|
| Supporter | $5 | Name in CONTRIBUTORS.md |
| Patron | $25 | Priority issue response |
| Sustainer | $100 | Security advisory pre-notification |
| Corporate | $500+ | Logo in README, SLA support |

GitHub Sponsors payout settings: https://github.com/sponsors/ethos-aegis/dashboard
GitHub Sponsors activity: https://github.com/sponsors/ethos-aegis/activity

---

*This log is append-only. Do not modify or delete existing entries.*  
*All security advisories must also be filed at the GitHub Security Advisory link above.*
