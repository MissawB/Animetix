---
title: Animetix Project
emoji: 🎭
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# 🎭 Animetix Project

Animetix est une plateforme intelligente de découverte de médias (Anime, Manga, Films, Jeux Vidéo) utilisant l'IA pour le filtrage thématique et visuel.

## 🚀 Déploiement Hugging Face Spaces

Cette application tourne via Docker et utilise **Supervisor** pour orchestrer :
1. **Django** (Backend & API)
2. **Celery** (Traitement IA asynchrone)
3. **ChromaDB** (Recherche vectorielle)

### ⚙️ Configuration requise (Secrets)

Pour faire fonctionner ce Space, ajoutez les variables suivantes dans **Settings > Variables and secrets** :

| Nom du Secret | Description |
| :--- | :--- |
| `DJANGO_SECRET_KEY` | Une clé aléatoire longue |
| `DATABASE_URL` | URL de votre DB (ex: Neon.tech) |
| `REDIS_URL` | URL de votre Redis (ex: Upstash) |
| `BRAIN_API_URL` | URL de votre service LLM |

## 🛠️ Architecture
- **Vector Search** : ChromaDB
- **Knowledge Graph** : Neo4j
- **Task Queue** : Celery + Redis
- **Database** : PostgreSQL
