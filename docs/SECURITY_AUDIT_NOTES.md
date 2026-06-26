# Security Audit Notes — Dependency Vulnerabilities

This file records reviewed dependency-security findings and the decisions taken,
so future audits don't re-investigate the same items from scratch.

## Snyk report of 2026-06-26 — stale snapshot

A Snyk dashboard report flagged 13 Python packages (Django, Pillow, protobuf,
urllib3, setuptools, sqlparse, zipp, requests, DRF, numpy, idna, pyasn1,
jsonpickle). **The report was scanning a stale snapshot** (it saw `django@3.2.25`,
`pillow@9.5.0`, `setuptools@40.5.0` — versions from an old `requirements.txt`).

Cross-checked every flagged package against the **current** `requirements.txt`
(the manifest actually installed by `deploy/Dockerfile`): **12 of 13 are already
patched well beyond Snyk's recommended fix** — e.g. Django **5.2.14** (Snyk wanted
4.2.x), Pillow **12.2.0** (wanted 10.2.0), urllib3 **2.7.0**, setuptools **82.0.1**,
sqlparse **0.5.5**, requests **2.34.2**, DRF **3.17.1**, numpy **1.26.4**,
idna **3.18**, pyasn1 **0.6.3**, protobuf **6.33.6**, zipp **4.1.0**. Applying the
Snyk suggestions verbatim would have **downgraded** these and broken the app.

**Action:** re-scan Snyk against the current `main`. Note the Snyk CI step in
`.github/workflows/security_audit.yml` is currently **disabled** (needs
`SNYK_TOKEN`); the dashboard finding came from Snyk's hosted GitHub integration
on an old import.

## Accepted finding — `jsonpickle@3.4.2` (CWE-502, CVSS 8.6)

The only Snyk finding still valid against the current manifest.

- **Transitive only**, pulled in `via apache-beam` (pip-compile annotation in
  `requirements.txt`). **Not imported anywhere in application code** (`grep`
  confirms no `jsonpickle` usage in `backend/`).
- The deserialization risk is exploitable only if apache-beam itself
  deserializes untrusted data through jsonpickle — not a path this project's
  pipeline code exercises with untrusted input → **low practical exposure**.
- Snyk recommends `jsonpickle>=4.0.2`, but **apache-beam==2.74.0 pins
  `jsonpickle<4.0.0,>=3.0.0`** (verified via package metadata). Forcing
  `jsonpickle==4.0.2` would break dependency resolution / apache-beam. It is
  not directly editable anyway (`requirements.txt` is pip-compile generated).

**Decision (2026-06-26): ACCEPT the risk, documented.** Do not pin jsonpickle 4.
**Revisit when** apache-beam relaxes its `jsonpickle<4` constraint (then a
`pip-compile` refresh picks up the patched version), or sooner if the pipeline
starts deserializing untrusted input via beam. Suggested review date:
**2026-09-26**.

If the team wants the finding suppressed in the Snyk dashboard, ignore it there
(or in a committed `.snyk`) with the reason: *"Transitive via apache-beam (pinned
`jsonpickle<4`); not imported by app code; low exposure; revisit when beam
supports jsonpickle>=4."* — use the exact `SNYK-PYTHON-JSONPICKLE-*` issue id
from the dashboard.
