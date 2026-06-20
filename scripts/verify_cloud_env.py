#!/usr/bin/env python3
"""Compare the env vars the Django app reads against a Cloud Run service.

Read-only: only runs `gcloud ... describe` / `gcloud secrets list`. It does not
change anything. Requires an authenticated `gcloud` for the cloud checks; without
it, the script still prints the variables the app expects.

Usage:
    python scripts/verify_cloud_env.py \
        --service web --region europe-west9 --project animetix

    # Just print what the app needs (no gcloud calls):
    python scripts/verify_cloud_env.py --offline

    # Also scan the whole backend (feature modules), not just settings.py:
    python scripts/verify_cloud_env.py --all --service web
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess  # nosec B404 - only fixed, read-only gcloud commands
import sys
from pathlib import Path

try:  # emojis render on Windows consoles too (no-op on UTF-8 terminals)
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

REPO = Path(__file__).resolve().parents[1]
SETTINGS = REPO / "backend" / "api" / "animetix_project" / "settings.py"

# env("NAME"...) / env.bool("NAME"...) / env.int(...) / env.list(...)
ENV_CALL = re.compile(r"""env(?:\.\w+)?\(\s*["']([A-Z][A-Z0-9_]{2,})["']([^)]*)\)""")
# os.getenv("NAME"...) / os.environ.get("NAME"...)
GETENV_CALL = re.compile(
    r"""os\.(?:getenv|environ\.get)\(\s*["']([A-Z][A-Z0-9_]{2,})["']([^)]*)\)"""
)
# os.environ["NAME"]  (hard requirement)
ENVIRON_INDEX = re.compile(r"""os\.environ\[\s*["']([A-Z][A-Z0-9_]{2,})["']\s*\]""")


def scan_file(path: Path) -> dict[str, bool]:
    """Return {VAR_NAME: required}. required=True when read without a default."""
    out: dict[str, bool] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return out

    def mark(name: str, required: bool) -> None:
        out[name] = out.get(name, False) or required

    for m in ENV_CALL.finditer(text):
        rest = m.group(2)
        # required only when there is no default at all (no extra positional/keyword arg)
        required = ("default" not in rest) and ("," not in rest)
        mark(m.group(1), required)
    for m in GETENV_CALL.finditer(text):
        rest = m.group(2)
        # os.getenv returns None instead of raising -> never a hard requirement
        mark(m.group(1), False)
    for m in ENVIRON_INDEX.finditer(text):
        mark(m.group(1), True)
    return out


def scan_vars(scan_all: bool) -> dict[str, bool]:
    found = scan_file(SETTINGS)
    if scan_all:
        for p in (REPO / "backend").rglob("*.py"):
            if "__pycache__" in p.parts or "tests" in p.parts:
                continue
            for name, req in scan_file(p).items():
                found[name] = found.get(name, False) or req
    return found


def _gcloud(args: list[str]) -> str | None:
    # On Windows gcloud ships as gcloud.cmd (a batch script); subprocess with a
    # list won't resolve a bare "gcloud" via PATHEXT, so locate it explicitly.
    exe = shutil.which("gcloud")
    if exe is None:
        print("⚠️  gcloud not found on PATH — skipping cloud checks.", file=sys.stderr)
        return None
    try:
        return subprocess.check_output(  # nosec B603 - fixed args, read-only
            [exe, *args], text=True, stderr=subprocess.STDOUT
        )
    except FileNotFoundError:
        print("⚠️  gcloud not found on PATH — skipping cloud checks.", file=sys.stderr)
        return None
    except subprocess.CalledProcessError as e:
        print(f"⚠️  gcloud failed: {e.output.strip()[:400]}", file=sys.stderr)
        return None


def cloud_run_env(service: str, region: str, project: str) -> tuple[set[str], set[str]]:
    """Return (plain_env_names, secret_backed_env_names) for the service."""
    raw = _gcloud(
        [
            "run",
            "services",
            "describe",
            service,
            "--region",
            region,
            "--project",
            project,
            "--format",
            "json",
        ]
    )
    if not raw:
        return set(), set()
    data = json.loads(raw)
    plain: set[str] = set()
    secret: set[str] = set()
    containers = (
        data.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
    )
    for c in containers:
        for e in c.get("env", []):
            name = e.get("name")
            if not name:
                continue
            if "valueFrom" in e:  # secret-backed
                secret.add(name)
            else:
                plain.add(name)
    return plain, secret


def secret_manager(project: str) -> set[str]:
    raw = _gcloud(["secrets", "list", "--project", project, "--format", "value(name)"])
    if not raw:
        return set()
    return {line.strip().rsplit("/", 1)[-1] for line in raw.split() if line.strip()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--service", default="animetix-web", help="Cloud Run service name")
    ap.add_argument("--region", default="europe-west9")
    ap.add_argument("--project", default="animetix")
    ap.add_argument(
        "--all",
        action="store_true",
        help="scan the whole backend, not just settings.py",
    )
    ap.add_argument(
        "--offline", action="store_true", help="don't call gcloud, just list needs"
    )
    args = ap.parse_args()

    needed = scan_vars(args.all)
    required = sorted(n for n, req in needed.items() if req)
    optional = sorted(n for n, req in needed.items() if not req)

    print(
        f"📋 App reads {len(needed)} env vars from "
        f"{'backend/**' if args.all else 'settings.py'} "
        f"({len(required)} required, {len(optional)} optional).\n"
    )

    if args.offline:
        print("REQUIRED:\n  " + "\n  ".join(required))
        print("\nOPTIONAL:\n  " + "\n  ".join(optional))
        return 0

    plain, secret = cloud_run_env(args.service, args.region, args.project)
    configured = plain | secret
    available_secrets = secret_manager(args.project)

    if not configured:
        print("⚠️  Could not read the Cloud Run service env (see warnings above).")
        print("    Re-run authenticated, or use --offline to just see the needs.\n")

    def status(name: str) -> str:
        if name in secret:
            return "✅ (secret)"
        if name in plain:
            return "✅"
        return "❌ MISSING"

    print("== REQUIRED ==")
    missing_required = []
    for n in required:
        s = status(n)
        if s.startswith("❌"):
            missing_required.append(n)
        print(f"  {s:14} {n}")

    print("\n== OPTIONAL ==")
    for n in optional:
        print(f"  {status(n):14} {n}")

    if available_secrets:
        print(f"\n== Secret Manager ({len(available_secrets)} secrets) ==")
        print("  " + ", ".join(sorted(available_secrets)))

    print()
    if missing_required:
        print(
            f"❌ {len(missing_required)} REQUIRED var(s) NOT set on the service: "
            + ", ".join(missing_required)
        )
        return 1
    if configured:
        print("✅ All required vars are present on the Cloud Run service.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
