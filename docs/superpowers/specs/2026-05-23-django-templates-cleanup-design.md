# Spécification de Nettoyage des Templates Django & Routage SPA - 23/05/2026

## 1. Objectif
Transitionner l'architecture de l'application Animetix vers un modèle 100% SPA (Single Page Application) géré par React sur le frontend, avec Django agissant uniquement comme API REST/GraphQL et serveur de webhooks. Cette étape consiste à éliminer la dette technique en supprimant les anciens templates HTML Django devenus inutiles et en adaptant le routage backend pour rediriger de manière transparente les requêtes non-API/non-admin vers le point d'entrée de la SPA React (`index.html`).

## 2. Portée du Nettoyage

### 2.1 Suppression des Fichiers HTML Obsolètes (Dossier `templates/`)
L'intégralité des dossiers et fichiers de templates legacy Django sous `backend/api/animetix/templates/animetix/` sera supprimée, à l'exception de l'administration.

**Dossiers à supprimer sous `backend/api/animetix/templates/animetix/` :**
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
* `partials/` (contenant `sidebar.html`, `navbar.html`, etc.)
* `social/`
* `undercover/`
* `vision/`

**Fichiers individuels à supprimer sous `backend/api/animetix/templates/animetix/` :**
* `base.html` (layout principal legacy Django)
* `index.html` (page d'accueil legacy Django)

**Éléments à CONSERVER :**
* `backend/api/animetix/templates/index.html` : Ce fichier à la racine du dossier templates sert de point d'entrée unique pour la SPA React (chargé par `spa_view`).
* `backend/api/animetix/templates/animetix/admin/` : Contient les templates personnalisés pour la partie administration (ex: `ai_eval.html`, `health.html`, `gold_curation.html`).

---

### 2.2 Nettoyage et Simplification des URLs Backend
Les fichiers de routage d'anciennes pages HTML Django vont être supprimés, et `urls/__init__.py` sera simplifié.

**Fichiers de routage à supprimer (`backend/api/animetix/urls/`) :**
* `audio.py` (les fonctionnalités audio-lab sont migrées sur l'API)
* `emoji.py` (les fonctionnalités emoji-decode sont migrées sur l'API)
* `games.py` (les fonctionnalités de jeux legacy sont migrées sur l'API)
* `social.py` (toutes les pages profils et notifications sont migrées sur l'API)

**Fichiers à modifier :**
* `backend/api/animetix/urls/donation.py` : Retirer la route de la page HTML `transparency/` car cette dernière est gérée par React. Conserver la route `webhook/` qui est un endpoint API pur.
* `backend/api/animetix/urls/mlops.py` : Conserver uniquement la route POST `feedback/submit/`.
* `backend/api/animetix/urls/__init__.py` :
  * Supprimer les imports et inclusions obsolètes (`games`, `social`, `audio`, `emoji`).
  * Rediriger la route racine (`path('', views.index)`) vers `spa_view` pour que l'accueil pointe directement sur la SPA.
  * Conserver l'inclusion de `animetix.urls.api` (`path('api/v1/', ...)`).
  * Conserver la règle catch-all `spa-fallback` pour que toutes les requêtes directes (ex: `/games/classic/`) soient prises en charge par React Router sur le client.

---

### 2.3 Nettoyage des Vues Backend (Python)
Les fonctions de vues renvoyant des réponses HTML legacy vont être supprimées dans `backend/api/animetix/views/base.py` et autres fichiers associés.

**Vues à supprimer dans `views/base.py` :**
* `index`
* `start_daily_challenge`
* `custom_config_view`
* `save_custom_config`
* `switch_mode`
* `switch_language`
* `switch_difficulty`

---

## 3. Plan de Vérification

### 3.1 Tests Automatisés
Nous exécuterons la suite de tests Django existante pour s'assurer que les changements de routage n'introduisent pas de régressions ou d'erreurs d'importation dans les modules Python :
```bash
python backend/api/manage.py test
```

### 3.2 Vérification Manuelle
1. **Lancement du serveur backend :** S'assurer que le serveur Django démarre sans erreurs d'import ou d'URLs circulaires.
2. **Accès Root :** Visiter `http://localhost:8000/` et vérifier que `spa_view` charge l'application React.
3. **Fallback Catch-All :** Visiter une route directe comme `http://localhost:8000/leaderboard/` et vérifier qu'elle charge la SPA React sans erreur Django 404, et que React Router prend le relais.
