# Plan d'implémentation du Nettoyage des Templates Django & Simplification du Routage SPA

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Supprimer définitivement tous les templates Django legacy obsolètes et nettoyer le routage URL backend pour forcer le basculement exclusif de la navigation sur la SPA React (Pure API).

**Architecture:** Django gère uniquement les requêtes de l'API REST/GraphQL sous `/api/v1/` et `/graphql/`, l'interface d'administration Django `/admin/` standard, ainsi que les webhooks. Tout le reste du trafic web non-statique est redirigé via la vue catch-all `spa_view` vers la SPA React.

**Tech Stack:** Python 3.10, Django, React SPA, PowerShell/Command Line.

---

### Tâche 1 : Modification et Simplification des URLs du Root

**Files:**
- Modify: [__init__.py](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/src/backend/animetix/urls/__init__.py)

- [ ] **Étape 1 : Simplifier le fichier de routage central des URLs**
  Modifier `src/backend/animetix/urls/__init__.py` pour retirer toutes les inclusions de fichiers de routage d'anciennes pages HTML, rediriger la racine `/` vers `spa_view` et éliminer les configurations de session inutiles :
  ```python
  from django.urls import path, include, re_path
  from ..views.spa import spa_view

  urlpatterns = [
      path('', spa_view, name='index'),
      path('api/v1/', include('animetix.urls.api')),
      path('donation/', include('animetix.urls.donation')),
      path('mlops/', include('animetix.urls.mlops')),
      
      # Règle catch-all pour React SPA
      re_path(r'^(?!api/|static/|admin/).*$', spa_view, name='spa-fallback'),
  ]
  ```

- [ ] **Étape 2 : Commiter les changements de routage de base**
  Exécuter :
  ```powershell
  git add src/backend/animetix/urls/__init__.py
  git commit -m "refactor(backend): route root and fallback strictly to SPA view"
  ```

---

### Tâche 2 : Nettoyage des fichiers d'URLs secondaires

**Files:**
- Modify: [donation.py](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/src/backend/animetix/urls/donation.py)
- Delete: [audio.py](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/src/backend/animetix/urls/audio.py)
- Delete: [emoji.py](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/src/backend/animetix/urls/emoji.py)
- Delete: [games.py](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/src/backend/animetix/urls/games.py)
- Delete: [social.py](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/src/backend/animetix/urls/social.py)

- [ ] **Étape 1 : Retirer la page de transparence HTML de donation.py**
  Modifier `src/backend/animetix/urls/donation.py` pour retirer l'ancienne page HTML de transparence et ne conserver que le webhook :
  ```python
  from django.urls import path
  from .. import views

  urlpatterns = [
      path('webhook/', views.donation_webhook, name='donation_webhook'),
  ]
  ```

- [ ] **Étape 2 : Supprimer les fichiers d'URLs legacy devenus obsolètes**
  Supprimer physiquement les fichiers d'URLs suivants :
  * `src/backend/animetix/urls/audio.py`
  * `src/backend/animetix/urls/emoji.py`
  * `src/backend/animetix/urls/games.py`
  * `src/backend/animetix/urls/social.py`

- [ ] **Étape 3 : Commiter le nettoyage des fichiers d'URLs**
  Exécuter :
  ```powershell
  git rm src/backend/animetix/urls/audio.py src/backend/animetix/urls/emoji.py src/backend/animetix/urls/games.py src/backend/animetix/urls/social.py
  git add src/backend/animetix/urls/donation.py
  git commit -m "cleanup(backend): delete legacy Django URL configs"
  ```

---

### Tâche 3 : Nettoyage des Vues Backend (Python)

**Files:**
- Modify: [base.py](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/src/backend/animetix/views/base.py)

- [ ] **Étape 1 : Nettoyer `src/backend/animetix/views/base.py`**
  Retirer les fonctions de vues renvoyant des templates Django (`index`, `start_daily_challenge`, `custom_config_view`, `save_custom_config`, `switch_mode`, `switch_language`, `switch_difficulty`) :
  ```python
  import random
  import datetime
  import hashlib
  from django.shortcuts import render, redirect
  from django.conf import settings
  from django.http import JsonResponse
  from ..containers import get_container
  from .classic import start_game
  from ..session_manager import GameSessionManager
  from ..presenters import ArchetypistPresenter
  from ..models import DailyChallenge, ChallengeResult
  import logging

  logger = logging.getLogger('animetix')

  # Ne conserver que les constantes, logiques métiers internes ou fonctions non-HTML si nécessaires.
  # Les fonctions de rendu de template comme index() et start_daily_challenge() sont intégralement supprimées.
  ```

- [ ] **Étape 2 : Commiter le nettoyage des vues**
  Exécuter :
  ```powershell
  git add src/backend/animetix/views/base.py
  git commit -m "cleanup(backend): remove legacy Django view controllers"
  ```

---

### Tâche 4 : Suppression des Templates Physiques Obsolètes

**Files:**
- Delete: [templates/animetix](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/src/backend/animetix/templates/animetix) (except `admin/`)

- [ ] **Étape 1 : Supprimer les dossiers de templates et layouts legacy**
  Supprimer les répertoires physiques obsolètes sous `src/backend/animetix/templates/animetix/` :
  * `akinetix/`
  * `animinator/`
  * `archetypist/`
  * `audio/`
  * `blindtest/`
  * `boss/`
  * `classic/`
  * `codemanga/`
  * `emoji/`
  * `games/`
  * `manga/`
  * `mlops/`
  * `paradox/`
  * `partials/`
  * `social/`
  * `undercover/`
  * `vision/`
  * `base.html`
  * `index.html` (dans le sous-dossier `animetix/` uniquement)

- [ ] **Étape 2 : Confirmer la conservation d'index.html principal et admin/**
  S'assurer que :
  * `src/backend/animetix/templates/index.html` est bien présent et intact.
  * `src/backend/animetix/templates/animetix/admin/` est bien conservé.

- [ ] **Étape 3 : Commiter la suppression des templates**
  Exécuter :
  ```powershell
  git commit -a -m "cleanup(templates): remove all legacy Django templates and partials"
  ```

---

### Tâche 5 : Validation et Tests

- [ ] **Étape 1 : Lancer les tests unitaires du backend**
  Exécuter :
  ```powershell
  python src/backend/manage.py test
  ```
  S'assurer que tout compile et que le routeur Django n'émet aucune erreur d'import ou de nom d'URL manquant.

- [ ] **Étape 2 : Lancer le serveur Django localement pour vérification manuelle**
  Exécuter :
  ```powershell
  python src/backend/manage.py runserver
  ```
  Visiter `http://127.0.0.1:8000/` et une route comme `http://127.0.0.1:8000/social/dashboard/` pour valider le bon chargement de la SPA.
