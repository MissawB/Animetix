# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées sont cochées ou purgées pour être archivées dans `HISTORY.md`.

## 🛠️ Dette Technique & Architecture

- [X] **Standardisation de la validation API (Django Forms)** : Finaliser la refactorisation des vues dans `backend/api/animetix/views/api.py` pour utiliser systématiquement les Django Forms. (Actuellement : plusieurs accès directs à `request.GET/POST` persistent).
- [X] **Complétude de l'InferencePort** : Supprimer les stubs restants dans `backend/core/ports/inference_port.py`. (Plusieurs méthodes lèvent encore `InferenceNotImplementedError` sans implémentation réelle).
- [X] **Refactorisation de `App.tsx`** : Découper ce fichier monolithique (21 KB) en composants atomiques et services dédiés.
- [X] **Modularisation Frontend** : Créer un répertoire `src/pages/` pour isoler les vues des composants de fonctionnalités (`features/`).
- [ ] **Cohérence du Routage & Navigation** :
    - [X] Corriger la route World Boss (`/game/world-boss/active/` vs `/game/world-boss/`).
    - [X] Refactoriser `SocialRoutes.tsx` pour déplacer les pages non-sociales (Pricing, Support, Explore) dans leurs domaines respectifs.
- [X] **Intégration réelle du `SelfEvolvingCompiler`** : Remplacer les `NotImplementedError` dans le proxy d'évolution LLM par une intégration effective.
- [X] **Amélioration des diagnostics IA** : Migrer de la simulation `gpt2` dans `UnifiedInferenceAdapter` vers des mécanismes de diagnostics natifs aux modèles de production.
- [x] **Optimisation du Chargement IA (Lazy Loading)** : Garantir que tous les adaptateurs et modèles lourds sont chargés uniquement lors de leur première utilisation pour accélérer le démarrage du container. Refactorisation de `FallbackInferenceAdapter` (cache et health lazy) et `GoogleGenAIAdapter` (client lazy).

## 🔗 Désorphelinisation & Raccordement Backend

- [ ] **Réactivation des Laboratoires (Ghost Labs)** : Décommenter et tester les endpoints backend pour :
    - [ ] **Manga Lab** (Nettoyage & Traduction).
    - [ ] **Video Lab** (Transfert de style FateZero).
    - [ ] **Spatial Lab** (Estimation de profondeur & 3D).
    - [ ] **Soundscape & Speech-to-Speech** (Génération sonore et voix E2E).
- [ ] **Rétablissement du Nexus Companion** : Connecter l'interface de chat à l'endpoint `companion/interact/`.
- [ ] **Finalisation des Outils d'Admin** : Raccorder les pages de monitoring (`Admin DPO`, `SOTA Benchmarks`, `Graph Debugger`) aux services backend correspondants.
- [ ] **Activation des Services Cognitifs** : Déployer les endpoints pour `Archetype Nexus`, `Neuro Memory` et `AIDebate Arena`.

## 🚀 Intégrations & Pages Manquantes (Frontend)

- [X] **Page "Plans & Tarifs" (`/pricing/`)** : Créer une interface pour comparer les offres (Explorateur vs Premium) et gérer les abonnements.
- [X] **Visualisation "Tree of Thoughts" (Expert)** : Créer une page de visualisation d'arbre (MCTS) pour explorer les branches de réflexion du `TreeOfThoughtsSearchService`.
- [X] **Monitoring "Dynamic Budget TTC"** : Dashboard d'administration pour suivre l'allocation du budget de pensée en temps réel.
- [X] **Galerie des Multivers** : Interface de type "catalogue" pour parcourir les segments de multivers synthétiques générés par la communauté.
- [X] **Centre d'Aide & Support** : Implémenter une page pour le support technique connectée au `dpo_feedback_loop.py`.
- [X] **Finalisation Intégration Explorer** : Désorpheliniser la page `/explore/` en l'intégrant plus profondément dans les flux de recommandation et de navigation contextuelle.
- [ ] **Interface "Voice Cloning" (RVC)** : Créer un laboratoire dédié pour le clonage de voix zero-shot.
- [ ] **Dashboard "Neural Diagnostics"** : Interface pour visualiser l'incertitude (entropie) et les activations internes (Logit Lens) des générations.

## 🛡️ Sécurité & Résilience

- [ ] **Signature des modèles IA** : Mettre en place une procédure de vérification des signatures pour les modèles chargés depuis Hugging Face.
- [x] **Audit des paramètres CSRF (SameSite)** : Réévaluer `CSRF_COOKIE_SAMESITE = 'None'`. Passer à `'Lax'` si possible.
- [x] **Migration complète vers `nh3`** : Finaliser le remplacement de `bleach` pour la sanitisation HTML.
- [x] **Quotas de Budget de Pensée (TDoS)** : Implémenter des limites strictes sur le coût des réflexions par utilisateur/session.
- [x] **Audit SSRF & `allow_internal=True`** : Réduire drastiquement l'usage de `allow_internal=True` dans les adaptateurs d'inférence. Mettre en place une segmentation réseau stricte (VPC/Firewalls) pour isoler les services internes. (Complété le 2026-06-05)
- [x] **Renforcement OIDC/Authentification Webhooks** : Auditer tous les endpoints `@csrf_exempt` (Tasks, Eventarc, Billing). Garantir que l'audience OIDC est une valeur statique, non modifiable, et spécifique au endpoint. Éviter `request.build_absolute_uri()`. (Complété le 2026-06-05)
- [x] **Sanitisation des données ingestées (Prompt Injection)** : Étendre `sanitize_for_prompt` pour protéger les données avant insertion dans ChromaDB ou Neo4j (protection contre l'injection indirecte). (Complété le 2026-06-05)
- [x] **Scan de dépendances (Supply Chain)** : Intégrer un outil de scan de vulnérabilités (ex: `safety` ou `snyk`) dans le pipeline CI (`.github/workflows/security_audit.yml`). (Complété le 2026-06-05)

## ☁️ Déploiement & Intégration Google Cloud (GCP)

- [ ] **Google Identity Platform** : Migration de l'authentification vers le service géré GCP.
- [ ] **Cloud KMS** : Chiffrement CMEK pour les images et voix générées.
