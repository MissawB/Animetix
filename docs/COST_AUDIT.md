# 📊 Audit des Coûts & Stratégie Économique - Animetix

Ce document présente un audit détaillé des coûts opérationnels de la plateforme **Animetix** et définit la viabilité du modèle économique basé sur les **Bx** (Bx).

---

## 1. Intelligence Artificielle & Inférence (Coûts Variables)

Animetix utilise une architecture d'inférence hybride pour équilibrer performance "SOTA" et rentabilité. Les coûts sont calculés par le `PricingService` interne.

### 1.1. Modèles de Langage (LLM)
*Coût moyen pour 1 million de tokens (Entrée + Sortie).*

| Moteur IA | Usage | Coût (USD/1M tokens) |
| :--- | :--- | :--- |
| **GPT-4o / Claude 3 Sonnet** | RAG complexe, Scénarios VN | **10.00$ à 18.00$** |
| **Brain API (Custom)** | Logique métier neuronale | **1.50$ à 3.00$** |
| **Llama-3-8B / Qwen-2.5** | Chat standard, Akinetix RL | **~0.10$** (si API tiers) |
| **Local LLM (Ollama)** | Chat de base, NPC | **0.00$** (Coût infra uniquement) |

### 1.2. Modèles Génératifs (Unitaires)
*Coût par requête unique.*

| Modèle | Action | Coût (USD/unité) |
| :--- | :--- | :--- |
| **SDXL Turbo** | Génération d'image (Forge) | **0.01$** |
| **Coqui XTTS-v2** | Clonage vocal (Voice Lab) | **0.005$** |
| **Manga OCR** | Extraction de texte | **0.00$** (Calcul local) |

---

## 2. Infrastructure & Cloud (Coûts Fixes)

Estimation basée sur un déploiement de production sur **Google Cloud Platform (GCP)** ou fournisseur GPU spécialisé (RunPod/Lambda).

| Ressource | Service | Coût Mensuel Est. | Rôle |
| :--- | :--- | :--- | :--- |
| **Compute Engine (GPU)** | Instances L4 / A100 | **450$ - 1200$** | Inférence des Ghost Labs & SLMs |
| **Cloud Run / GKE** | Backend Django | **40$ - 150$** | API, Workers Celery, Websockets |
| **Bases de Données** | Cloud SQL + Neo4j Aura | **80$ - 200$** | Persistance relationnelle et Graphe |
| **Vector Store** | ChromaDB (Self-hosted) | **30$ - 60$** | Moteur RAG (Lore & Sémantique) |
| **Cloud Storage** | GCS Buckets | **15$ - 50$** | Assets média, Planches de manga |

**Total Infrastructure estimé : ~600$ à 1600$ / mois.**

---

## 3. Services Tiers & Observabilité

| Service | Coût Mensuel | Rôle |
| :--- | :--- | :--- |
| **Firebase Auth** | Gratuit (tier standard) | Authentification & Sécurité |
| **Sentry / PostHog** | **50$ - 100$** | Monitoring d'erreurs et Product Analytics |
| **Stripe** | 2.9% + 0.30$ / trans. | Gestion des achats de Bx |

---

## 4. Analyse de Rentabilité : Le Modèle "Bx" (Marge Minimale)

Le système de jetons **Bx** a été recalibré le 13 juin 2026 pour passer d'un modèle profitable à un modèle **"Break-even" (Équilibre Social)**, minimisant les marges au profit de l'utilisateur.

### 4.1. Ratio Coût/Revenu (Publicité)
*   **Revenu moyen d'une Rewarded Ad (30s)** : ~0.015$ à 0.025$.
*   **Crédit utilisateur** : **+250 Bx** (Berrix).
*   **Coût d'un appel IA standard (5 Bx)** : ~0.00005$.
*   **Coût d'une Image Forge (50 Bx)** : ~0.0005$.

**Constat :** Une seule publicité vidéo finance désormais environ 400 à 500 appels IA simples ou 5 fusions créatives. Le surplus généré sert exclusivement à couvrir le maintien du cluster GPU (coût fixe).

### 4.2. Ratio Coût/Revenu (Achat Direct)
*   **Pack Initié (10 000 Bx pour 4.99€)** :
    *   Revenu net (après frais Stripe/Apple) : ~4.30$.
    *   Coût de service max (si tout est utilisé pour des images) : ~1.00$.
    *   **Marge Brute : ~75%** (Réinjectée dans les coûts fixes d'infrastructure).


---

## 5. Recommandations pour l'Optimisation

1.  **Priorité au Local** : Migrer systématiquement les tâches de chat vers des modèles **SLM (Small Language Models)** comme Qwen-2.5-1.5B hébergés sur nos propres instances pour réduire la dépendance aux APIs coûteuses (OpenAI/Anthropic).
2.  **Instances Spot** : Utiliser des instances GPU "Spot" (préemptibles) pour les workers Celery de la Forge afin de réduire les coûts serveur de 60-80%.
3.  **Caching Sémantique** : Implémenter un cache sémantique pour le RAG afin de ne pas payer deux fois pour la même question posée par différents utilisateurs.
4.  **Compression d'Images** : Utiliser WebP agressivement pour réduire les coûts de sortie de bande passante et de stockage GCS.

---
*Dernière mise à jour de l'audit : 13 juin 2026.*
