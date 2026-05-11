# 📋 Guide des Commandes : Animetix

Ce guide répertorie toutes les commandes nécessaires pour faire tourner, mettre à jour et évaluer le projet Animetix.

---

## 🛠 1. Lancement de l'Infrastructure (Docker)
Utilisez Docker pour lancer tous les services (Postgres, Redis, Neo4j, ChromaDB) en une fois.

| Commande | Explication |
| :--- | :--- |
| `docker-compose up -d --build` | Lance toute l'infrastructure en arrière-plan. |
| `docker-compose stop` | Arrête tous les services sans supprimer les données. |
| `docker-compose logs -f web` | Affiche les logs en temps réel du serveur Django. |

---

## 📊 2. Pipeline de Données (Data Engineering)
Pour peupler la base de données sémantique et graphique.

| Commande | Explication |
| :--- | :--- |
| `python run_pipeline.py` | Exécute la pipeline complète (Ingestion -> Filtrage -> Vectorisation -> Mapping). |
| `dagster-webserver -f pipeline/dagster_app.py` | Lance l'interface visuelle de Dagster (port 3000) pour gérer les assets. |

---

## 🧠 3. Intelligence Artificielle & Inférence
Commandes pour lancer le "cerveau" et les tâches asynchrones.

| Commande | Explication |
| :--- | :--- |
| `uvicorn brain:app --host 127.0.0.1 --port 7860` | Lance l'API d'inférence FastAPI (nécessaire pour la génération). |
| `cd backend; celery -A animetix_project worker --loglevel=info` | Lance le worker Celery pour traiter les images et synopsis en arrière-plan. |

---

## 🌐 4. Backend Django (Serveur Web)
Gestion du site web et de la base de données relationnelle.

| Commande | Explication |
| :--- | :--- |
| `python backend/manage.py runserver` | Lance le serveur de développement (port 8000). |
| `python backend/manage.py makemigrations` | Prépare les changements de structure de la base de données. |
| `python backend/manage.py migrate` | Applique les changements à la base de données (Postgres ou SQLite). |
| `python backend/manage.py createsuperuser` | Crée un compte administrateur pour `/admin`. |

---

## 🧪 5. MLOps & Évaluation
Mesurer la performance de votre IA.

| Commande | Explication |
| :--- | :--- |
| `python pipeline/mlops/evaluation_metrics.py` | Calcule les scores Hit Rate et MRR sur le Gold Dataset. |
| `python pipeline/mlops/latent_space_viz.py` | Génère les coordonnées 3D pour la visualisation de l'espace latent. |

---

## 🧹 6. Maintenance & Nettoyage

| Commande | Explication |
| :--- | :--- |
| `powershell -Command "Remove-Item data/artifacts/*.npy"` | Supprime les anciens vecteurs NumPy (obsolètes avec ChromaDB). |
| `pip install -r requirements.txt` | Met à jour toutes les bibliothèques Python. |

---
*Note : La plupart des commandes de développement doivent être lancées depuis la racine du projet avec l'environnement virtuel (`.venv`) activé.*
