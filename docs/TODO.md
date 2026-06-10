# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées sont cochées ou purgées pour être archivées dans `HISTORY.md`.

## 🛠️ Dette Technique & Architecture

### Backend & XAI
- [ ] **Nettoyage des URLs API** : Supprimer définitivement le code mort et les lignes commentées dans `backend/api/animetix/urls/api.py`.

## ☁️ Déploiement & Intégration Google Cloud (GCP)

- [ ] **Google Identity Platform** : Migration de l'authentification vers le service géré GCP.
- [ ] **Cloud KMS** : Chiffrement CMEK pour les images et voix générées.
- [ ] **AlloyDB AI** : Étudier la migration de pgvector vers AlloyDB pour des performances de recherche vectorielle accrues.
