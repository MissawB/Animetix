# Migration des Tâches Complétées vers HISTORY.md

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Déplacer toutes les tâches marquées comme terminées (`[x]`) de `docs/TODO.md` vers `docs/HISTORY.md` et nettoyer `docs/TODO.md`.

**Architecture:** Extraction des items cochés, regroupement par thématique, ajout dans la session la plus récente de `HISTORY.md` (ou création d'une nouvelle section si nécessaire), puis suppression des items de `TODO.md`.

**Tech Stack:** Markdown manipulation.

---

### Task 1: Extraction et Préparation de HISTORY.md

**Files:**
- Modify: `docs/HISTORY.md`

- [ ] **Step 1: Ajouter les nouvelles entrées dans la session [2026-06-02]**

Ajouter les points suivants sous les sections appropriées ou en créer de nouvelles si nécessaire :
- **Tests & Qualité** : Automatisation des tests d'évaluation continue (Ragas) pour la fidélité et l'absence d'hallucinations.
- **Frontend & Interfaces** : 
    - Intégration du mode `VsBattle` (Arena Ultimatum), de l'accès World Boss et du Blindtest sur la Home.
    - Création de la page Cinematic Volumetric Reconstruction (3D dynamique).
    - Déploiement du Dashboard SOTA Benchmarking pour la visualisation des performances.
- **Innovation & Curation** :
    - Déploiement du Visual Graph Debugger pour la correction manuelle des conflits de lore Neo4j.
    - Implémentation de la page de gestion Neuro-Symbolique de la mémoire (règles Z3).
- **Sécurité & Infrastructure** :
    - Sécurisation de la Brain API via `X-API-Key`.
    - Renforcement du réseau Docker (isolation localhost pour les DB).
    - Mise en place de mitigations contre l'injection de prompts et affinage de la CSP (retrait de `'unsafe-eval'`).
    - Systématisation de la sanitisation des sorties IA (`sanitize_ai`/`bleach`).

### Task 2: Nettoyage de TODO.md

**Files:**
- Modify: `docs/TODO.md`

- [ ] **Step 1: Supprimer les items cochés**

Supprimer tous les items commençant par `- [x]` dans `docs/TODO.md`.

- [ ] **Step 2: Vérifier la structure restante**

S'assurer que les titres de sections vides ne restent pas ou sont conservés si pertinent pour le futur.

### Task 3: Validation Finale

- [ ] **Step 1: Vérifier la cohérence des deux fichiers**
- [ ] **Step 2: Commit des changements**

Run: `git add docs/TODO.md docs/HISTORY.md`
Run: `git commit -m "docs: archive completed tasks from TODO.md to HISTORY.md"`
