# TODO — Améliorations du projet Animetix

> Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

## 🔴 Critiques

_Aucun item ouvert._

## 🟠 Élevés

- [/] **Fine-tune otaku — dataset assaini ✅ (PR #87) ; reste le réentraînement (bloqué GPU)** _(2026-07-13→17 ; détail cf. HISTORY 2026-07-17)_
  - **Reste** : réentraîner sur le dataset propre (`MissawB/otaku-expert-dataset`) **dès qu'un GPU est dispo** (cf. dette GPU), puis re-servir via `LLM_MODEL_NAME=otaku-qwen:7b` (déjà baké, aucun rebuild).

- [/] **Index visuel : phase 2 — `character_ccip_space` partiel, run GPU différé (mode économie)** _(phase 1 2026-07-14 ; run tenté 2026-07-17 ; facturation rétablie 2026-07-22, cf. HISTORY)_
  - Facturation GCP **rétablie le 2026-07-22**, mais le run GPU est **différé volontairement** : période de réduction des frais pendant la validation AdSense (sensors en pause, Redis migré Upstash, connecteur VPC retiré — cf. HISTORY 2026-07-22). Les ~3,5 h de vecteurs déjà écrits sont préservés (job reprenable).
  - **Reste (quand le mode économie sera levé)** : 1) vérifier/relever le plafond de budget (50 € conseillé) ; 2) Brain `/health` = 200 ; 3) re-exécuter **par chunks** (`--limit N`) jusqu'aux ~35 000 ; 4) recherche perso ne renvoie plus 503.

## 🟡 Moyens

- [x] **Deps — Tailwind un major de retard (v3 → v4) — fait (2026-07-24)** _(audit dette 2026-07-22)_
  - Preuve : `frontend/package.json:93` `tailwindcss ^3.4.19` — migration de config/moteur non triviale à planifier.
  - **Fait (2026-07-24)** : Migration vers `tailwindcss` v4.0.0 avec le plugin officiel `@tailwindcss/vite`. Directives CSS `@import "tailwindcss";` et `@config "../tailwind.config.js";` configurées. Suppression d'`autoprefixer` et de `postcss.config.js`. Build production Vite et 805/805 tests unitaires validés.

## 🟢 Faibles

_Aucun item ouvert._
