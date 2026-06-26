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

## Snyk report of 2026-06-26 (second, up-to-date scan)

A later Snyk scan reflects the **current** dependency tree (it correctly shows
`django@5.2.14`). Triage and decisions below.

> Dependency-version changes go in **`requirements.in`** (the source);
> `requirements.txt` is regenerated with
> `pip-compile --allow-unsafe --output-file=requirements.txt --strip-extras requirements.in`.
> Never hand-edit `requirements.txt`.

### Applied — safe quick-win bumps

- **PyJWT 2.12.0 → 2.13.0** — fixes Improper Authentication (CWE-287, CVSS 8.8)
  + 4 more. Direct dep; pure-python; verified (auth/JWT tests green).
- **bleach 6.1.0 → 6.4.0** — fixes XSS (CWE-79). Direct dep; pure-python;
  verified (security/sanitization tests green).

### Deferred — blocked or high-risk

- **diffusers 0.37.0 → 0.38.0** (code injection CWE-94, TOCTOU): **blocked** —
  diffusers 0.38 enforces `peft>=0.17.0` at import, but the project pins
  `peft==0.13.2`; bumping peft cascades into transformers/torch. Defer to the
  torch/transformers chantier.
- **cryptography 47.0.0 → 48.0.1** (OOB read CWE-125, CVSS 8.7): **blocked** —
  transitive, and `apache-beam==2.74.0` pins `cryptography<48.0.0`. Same gate as
  jsonpickle. Revisit when apache-beam allows cryptography 48.
- **torch 2.5.1 → 2.6.0+** (Deserialization CWE-502, CVSS 9.3) and
  **transformers 4.57.6 → 5.x**: the single biggest item — most "transitive"
  findings (accelerate, peft, sentence-transformers, torchvision, ultralytics,
  trl, bitsandbytes, manga-ocr, coqui-tts) are just "torch is old". Bumping torch
  risks breaking the entire pinned ML stack (CUDA/compat matrix). **Needs a
  dedicated chantier with full ML-path testing** — not a quick win.

### Accepted / out of app scope

- **OS Debian packages** (zlib, openssl, util-linux, gnutls, sqlite3, krb5,
  gnupg2, pam, perl): come from the `python:3.12-slim-bookworm` base image; many
  are "no fix" in Debian stable. Mitigated by rebuilding on an updated base, not
  by app code.
- **Snyk Code (SAST) likely false positives / accepted:** DOM-XSS on
  `<img src={...}>` fed from our own API; `csrf_exempt` on machine-to-machine
  webhooks (own auth); "hardcoded credentials" in test fixtures
  (`password="password"`).
- **Snyk Code (SAST) worth real follow-up (not in this batch):** reflected XSS in
  `backend/api/animetix/api/core.py` (Suwayomi proxy echoes remote content),
  open-redirect in `frontend/src/pages/auth/LoginPage.tsx` (`navigate(from)`),
  possible hardcoded secret in `scripts/deploy/deploy_jobs.py`.
