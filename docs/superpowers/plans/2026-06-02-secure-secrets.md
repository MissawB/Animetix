# Suppression des Secrets par Défaut - Plan d'Exécution

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sécuriser le projet en supprimant les valeurs par défaut des clés API et en imposant leur configuration via l'environnement.

**Architecture:** Centralisation de la validation dans `settings.py`, injection via le container de dépendances, et blocage du démarrage du service Brain API si la clé est absente.

**Tech Stack:** Python, Django, FastAPI, Environment Variables.

---

### Task 1: Génération et Configuration des Clés

**Files:**
- Modify: `.env`
- Modify: `.env.example`

- [ ] **Step 1: Générer une clé sécurisée**

Générer une chaîne aléatoire (ex: via `openssl rand -hex 32` ou un utilitaire Python).

- [ ] **Step 2: Mettre à jour .env**

Ajouter ou modifier `BRAIN_API_KEY` dans le fichier `.env` avec la nouvelle clé.

- [ ] **Step 3: Mettre à jour .env.example**

Remplacer les valeurs d'exemple par des placeholders clairs comme `REQUIRED_IN_PROD`.

### Task 2: Durcissement de la Configuration Django

**Files:**
- Modify: `backend/api/animetix_project/settings.py`

- [ ] **Step 1: Ajouter la validation de BRAIN_API_KEY**

```python
BRAIN_API_KEY = env('BRAIN_API_KEY', default='dev-insecure-key-2026')

if IS_PRODUCTION:
    if not BRAIN_API_KEY or BRAIN_API_KEY == 'dev-insecure-key-2026':
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("BRAIN_API_KEY est obligatoire et doit être sécurisée en production.")
```

### Task 3: Refactorisation de l'Adaptateur et du Container

**Files:**
- Modify: `backend/adapters/inference/brain_api_adapter.py`
- Modify: `backend/api/animetix/containers/inference.py`

- [ ] **Step 1: Modifier BrainAPIAdapter.__init__**

Retirer `os.getenv` du constructeur et ajouter un paramètre obligatoire `brain_api_key`.

- [ ] **Step 2: Mettre à jour le container d'injection**

Passer `settings.BRAIN_API_KEY` lors de l'instanciation de `brain_api_adapter`.

### Task 4: Sécurisation du Service FastAPI (Brain API)

**Files:**
- Modify: `backend/adapters/inference/brain_api.py`

- [ ] **Step 1: Imposer la clé au démarrage**

Modifier `EXPECTED_API_KEY` pour lever une erreur critique et arrêter le processus si la variable d'environnement est absente ou égale à la valeur de dev.

### Task 5: Validation et Tests

- [ ] **Step 1: Vérifier le démarrage de Django en DEV**
- [ ] **Step 2: Simuler la PROD pour vérifier que l'erreur est bien levée**
- [ ] **Step 3: Vérifier le démarrage de la Brain API**
- [ ] **Step 4: Commit des changements**
