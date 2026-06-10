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
