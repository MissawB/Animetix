# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées sont cochées ou purgées pour être archivées dans `HISTORY.md`.

## 🛠️ Dette Technique & Architecture

### Backend & XAI
- [ ] **Nettoyage des URLs API** : Supprimer définitivement le code mort et les lignes commentées dans `backend/api/animetix/urls/api.py`.

## ☁️ Déploiement & Intégration Google Cloud (GCP)

- [x] **Google Identity Platform** : Migration de l'authentification vers le service géré GCP.
- [x] **Cloud KMS** : Chiffrement CMEK pour les images et voix générées.
- [x] **AlloyDB AI** : Étudier la migration de pgvector vers AlloyDB pour des performances de recherche vectorielle accrues.
- [x] **Vertex AI Vector Search 2.0 (Collections)** : Évaluer la migration vers les Collections de Vertex AI pour simplifier le RAG et gérer nativement la recherche hybride.
- [ ] **Gemini Enterprise Agent Platform & Agentic RAG** : Intégrer l'Agent Gateway (sécurisation des prompts) et l'Agent Observability (suivi visuel du raisonnement des agents).
- [ ] **AlloyDB AI - Tools for Data Agents** : Implémenter les fonctions SQL natives `QueryData` (Text-to-SQL) pour simplifier et sécuriser l'accès au catalogue par les agents d'Animetix.
