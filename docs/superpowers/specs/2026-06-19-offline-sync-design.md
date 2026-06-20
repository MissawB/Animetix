# Conception - Centre de Synchronisation Hors-ligne (sync_offline_data)

Date : 2026-06-19
Auteur : Antigravity AI

## 1. Contexte & Problématique

Le **Centre de Synchronisation de Données** permet aux utilisateurs de visualiser les sessions de jeu effectuées hors-ligne et de forcer manuellement leur réconciliation avec le serveur via l'API `sync_offline_data`. 

Actuellement :
- L'interface React (`OfflineSyncPage.tsx`) appelle l'URL erronée `/api/sync/offline/` au lieu de `/api/v1/sync/offline/`.
- La suite de tests du backend Django (`tests/api/test_sync.py`) échoue en raison du décorateur de rate limiting (`django-ratelimit`) qui bloque les requêtes successives avec une erreur 403.

## 2. Objectifs

1. Corriger l'URI de l'API de synchronisation dans le frontend.
2. Désactiver le rate limiting dans la configuration de tests Django (`test_settings.py`) afin d'assurer la stabilité et le succès de l'exécution du banc de tests.
3. Valider le fonctionnement des tests unitaires backend.

## 3. Changements Proposés

### Frontend

Dans [OfflineSyncPage.tsx](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/src/pages/social/OfflineSyncPage.tsx) :
- Remplacer l'URL `/api/sync/offline/` par `/api/v1/sync/offline/`.

### Backend

Dans [test_settings.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/api/animetix_project/test_settings.py) :
- Ajouter `RATELIMIT_ENABLE = False` pour désactiver le rate-limiting globalement en mode test.

## 4. Plan de Validation

### Tests Automatisés
- Exécuter la commande `pytest tests/api/test_sync.py` et s'assurer que les 6 tests passent avec succès.
