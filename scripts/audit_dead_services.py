#!/usr/bin/env python3
"""Audit dead-code des services du domaine (core/domain/services).

Pour chaque module, on cherche des références ailleurs dans le backend :
- imports Python (`import bar`, `from ... import`, chemins pointés) ;
- chaînes du conteneur DI (`LazyClass("core.domain.services...bar", "Klass")`) ;
- usages des noms de classes définis dans le module.

Classement : PROD (référencé hors tests), TEST-ONLY (seulement dans tests/),
MORT (aucune référence). Heuristique — vérifier les candidats à la main.
"""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
SERVICES = os.path.join(BACKEND, "core", "domain", "services")
TESTS = os.path.join(ROOT, "tests")


def py_files(base):
    for dp, _, fns in os.walk(base):
        if "__pycache__" in dp:
            continue
        for fn in fns:
            if fn.endswith(".py"):
                yield os.path.join(dp, fn)


# Index : tout le code source (hors tests) et les tests, en texte.
src_files = [f for f in py_files(BACKEND)]
test_files = list(py_files(TESTS))

src_text = {f: open(f, encoding="utf-8", errors="ignore").read() for f in src_files}
test_text = {f: open(f, encoding="utf-8", errors="ignore").read() for f in test_files}


def classes_in(path):
    txt = src_text[path]
    return re.findall(r"^class\s+([A-Z]\w+)", txt, re.M)


def is_referenced(needles, corpus, exclude):
    """needles: patterns regex ; corpus: dict path->text ; exclude: set de paths."""
    for path, txt in corpus.items():
        if path in exclude:
            continue
        for pat in needles:
            if re.search(pat, txt):
                return True
    return False


results = {"PROD": [], "TEST-ONLY": [], "DEAD": []}

for path in sorted(py_files(SERVICES)):
    if os.path.basename(path) == "__init__.py":
        continue
    base = os.path.basename(path)[:-3]  # sans .py
    klasses = classes_in(path)
    # Patterns de référence : nom de module (importé/pointé/chaîne) + noms de classes
    needles = [
        rf"(?:import|\.|['\"]){re.escape(base)}\b",  # import bar / .bar / "..bar"
    ]
    needles += [rf"\b{re.escape(k)}\b" for k in klasses]
    exclude = {path}

    in_src = is_referenced(needles, src_text, exclude)
    in_test = is_referenced(needles, test_text, set())

    rel = os.path.relpath(path, BACKEND)
    label = f"{rel}  [{', '.join(klasses) or 'no-class'}]"
    if in_src:
        results["PROD"].append(label)
    elif in_test:
        results["TEST-ONLY"].append(label)
    else:
        results["DEAD"].append(label)

for cat in ("DEAD", "TEST-ONLY", "PROD"):
    print(f"\n===== {cat} ({len(results[cat])}) =====")
    for line in results[cat]:
        print(" ", line)
