# Task List (TODO) - Animetix

This document tracks all remaining technical, architectural, and feature tasks to implement. Completed tasks are checked or archived into `HISTORY.md`.

## 🛠️ Technical Debt & Architecture

### Backend & XAI
- [ ] **API URL Cleanup**: Permanently remove dead code and commented lines from `backend/api/animetix/urls/api.py`.

## ☁️ Deployment & Google Cloud Platform (GCP) Integration

- [x] **Google Identity Platform**: Migrate authentication to managed GCP service.
- [x] **Cloud KMS**: CMEK encryption for generated images and cloned voices.
- [x] **AlloyDB AI**: Study the migration from pgvector to AlloyDB for high performance vector search.
- [x] **Vertex AI Vector Search 2.0 (Collections)**: Evaluate the migration to Vertex AI Collections to simplify RAG and manage native hybrid search.
- [x] **Gemini Enterprise Agent Platform & Agentic RAG**: Integrate Agent Gateway (prompt security) and Agent Observability (visual reasoning tracking).
- [x] **AlloyDB AI - Tools for Data Agents**: Implement native SQL `QueryData` (Text-to-SQL) functions to simplify and secure catalog access for Animetix agents.

## 💰 Monétisation & Financement des Serveurs (Ad-Supported)

- [ ] **Régies Publicitaires Réelles** : Intégrer le SDK Google IMA ou un wrapper de Header Bidding (ex: Prebid.js) dans `SponsorStreamModal.tsx` pour remplacer les vidéos de test Google par de vraies pubs vidéo rémunératrices (CPM/CPC).
- [ ] **Sponsoring & Partenariats Anime Directs** : Remplacer les fausses bannières de `SimulatedAdBanner.tsx` par des bannières publicitaires réelles et des liens d'affiliation négociés avec des diffuseurs (ex: Crunchyroll, ADN) ou des boutiques partenaires.
- [ ] **Offres Développeur Payantes (Expert API)** : Mettre en place un système de facturation à la consommation via Stripe Billing pour l'utilisation de l'API (tier `pro`), permettant aux développeurs d'utiliser le moteur RAG d'Animetix dans leurs applications.
- [ ] **Financement Participatif (Dons)** : Ajouter un bouton Ko-fi/Patreon dans l'Espace Sponsors pour permettre aux utilisateurs de soutenir le serveur, en débloquant des cosmétiques exclusifs sur leur profil.
