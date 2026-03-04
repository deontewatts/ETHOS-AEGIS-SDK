# Security Policy — Ethos Aegis

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅        |

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

Report privately via:
1. **GitHub Private Security Advisory** (preferred):  
   `https://github.com/ethos-aegis/ethos-aegis/security/advisories/new`
2. **Email**: security@ethos-aegis.dev  
   GPG key fingerprint: (publish your key fingerprint here)

### What to include
- Affected module(s) and version
- Description of the vulnerability and its impact
- Reproduction steps or proof-of-concept
- Suggested fix (optional)

### Response timeline
| Stage | SLA |
|-------|-----|
| Acknowledgement | 48 hours |
| Initial assessment | 5 business days |
| Patch + CVE | 30 days (critical: 7 days) |
| Public disclosure | After patch release |

## Scope

In scope:
- Detection bypass (evading any SentinelCell without triggering CONDEMNED)
- Pattern injection into the GenesisEngine that produces false-negative patterns
- Cryptographic weaknesses in `ethos_aegis.security.vault`
- Dependency vulnerabilities with CVSS ≥ 7.0

Out of scope:
- Social engineering of maintainers
- Physical attacks
- Theoretical vulnerabilities without demonstrated impact

## Security Design Principles

1. **Zero external runtime dependencies** — core package runs on stdlib only
2. **HMAC-signed verdicts** — `SessionSeal` signs every `AegisVerdict`
3. **Append-only audit ledger** — SHA-256 hash chain detects tampering
4. **Non-root Docker** — runtime image runs as uid 1001 (aegis)
5. **Secrets never in code** — use `SecureVault` for API keys
