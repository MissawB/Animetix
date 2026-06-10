# Spécification de la Console MLOps (Training)

## Objectif
Développer une interface de supervision et de contrôle des boucles d'entraînement DPO (Direct Preference Optimization) et de visualisation des adaptateurs ML (Machine Learning).

## Architecture UI
L'interface sera structurée en trois sections fonctionnelles :

### 1. Vue d'ensemble DPO Feedback Loop
- **Statut :** Indique si la boucle DPO est `running`, `paused`, `idle`.
- **Dernières Métriques :** Affiche la dernière `loss`, `accuracy`, ou d'autres indicateurs clés pertinents.
- **Contrôles :** Boutons pour `Start`, `Pause`, `Stop` la boucle d'entraînement.
- **Historique :** Graphique simple de l'évolution des métriques au fil du temps (sera implémenté dans une version ultérieure si nécessaire, pour l'MVP, affichage des métriques instantanées).

### 2. Gestion des Adaptateurs
- **Liste des Adaptateurs :** Affiche tous les adaptateurs configurés (Inférence, Persistance, etc.) disponibles dans le système.
- **Statut Actif :** Indique quel adaptateur est actuellement utilisé pour chaque type (ex: `InferenceAdapter: GoogleGenAI`).
- **Détails :** Informations de base sur chaque adaptateur (nom, version, description, configuration minimale).

### 3. Journal des Activités (Logs)
- **Flux de Logs :** Affiche les logs en temps réel ou les logs récents liés aux opérations DPO et aux événements liés aux adaptateurs.
- **Filtrage :** Possibilité de filtrer par niveau de log (INFO, WARNING, ERROR) ou par composant spécifique.

## API Backend (Endpoints)

### 1. DPO Feedback Loop
- `GET /api/mlops/dpo-loop/status/`: Récupère le statut (running/paused/idle) et les dernières métriques (`loss`, `accuracy`).
    - *Permissions:* Staff seulement.
- `POST /api/mlops/dpo-loop/start/`: Démarre la boucle DPO.
    - *Permissions:* Staff seulement.
- `POST /api/mlops/dpo-loop/pause/`: Met en pause la boucle DPO.
    - *Permissions:* Staff seulement.
- `POST /api/mlops/dpo-loop/stop/`: Arrête la boucle DPO.
    - *Permissions:* Staff seulement.

### 2. Adaptateurs
- `GET /api/mlops/adapters/`: Liste tous les adaptateurs configurés et indique lequel est actif pour chaque type.
    - *Permissions:* Staff seulement.

## Fonctionnalités Clés
- **Supervision :** Monitoring en temps réel (ou quasi) de la boucle DPO et des adaptateurs.
- **Contrôle :** Déclenchement et gestion des états de la boucle DPO.
- **Transparence :** Visibilité sur la configuration et l'état des adaptateurs ML.

---
*Document de conception validé.*
