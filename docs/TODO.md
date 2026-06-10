# Task List (TODO) - Animetix

Ce document liste toutes les tâches techniques, architecturales et fonctionnelles restant à implémenter ou à corriger.

---

## 🛠️ Dette Technique & Architecture (Prioritaire)

### 🧪 Suite de Tests & Régressions
- [ ] **Réparer l'import et l'initialisation d'AgenticRAGService** :
  - Mettre à jour les tests unitaires et d'intégration ([test_cognitive_rag.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/tests/core/test_cognitive_rag.py), [test_chronicler_theories.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/tests/core/test_chronicler_theories.py), [test_agent_observability_gateway.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/tests/core/test_agent_observability_gateway.py)) suite à la suppression de `RAGWorkflowManager`.
  - Remplacer l'injection du paramètre obsolète `workflow_manager` par `workflow_orchestrator`.
  - Adapter les appels directs aux méthodes privées (ex: `_handle_research`) devenues des processeurs indépendants.
- [ ] **Corriger les Mocks & Contrats dans les Tests** :
  - **CoVe Oracle** : Ajuster [test_cove_oracle_service.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/tests/core/test_cove_oracle_service.py) pour renvoyer des instances de type `InferenceResponse` avec un attribut `.text` plutôt que des chaînes brutes (`AttributeError: 'str' object has no attribute 'text'`).
  - **Local Guardrail** : Mettre à jour [test_semantic_guardrail.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/tests/adapters/test_semantic_guardrail.py) pour mocker la méthode `moderate_content` de l'engine d'inférence plutôt que `generate_structured`.
  - **Spatial Inference** : Mettre à jour [test_spatial_inference.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/tests/adapters/test_spatial_inference.py) afin de ne pas appeler `estimate_depth` sur `DiffusersAdapter` (qui n'est plus supporté).
- [ ] **Mettre à jour le test d'API Voice Cloning** :
  - Modifier [test_voice_cloning_api.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/tests/api/test_voice_cloning_api.py) pour injecter une entête audio WAV valide (magic numbers binaire `RIFF/WAVE`) afin de passer la validation de sécurité MIME type.
- [ ] **Résoudre les conflits de noms de modules dans Pytest** :
  - Supprimer ou renommer les fichiers de tests dupliqués (`test_local_text_adapter.py` et `test_explore.py`) ou ajouter des `__init__.py` manquants pour éviter les erreurs `import file mismatch` lors de la collecte globale de Pytest.

### 🔌 Intégration Fonctionnelle
- [ ] **Brancher la boucle cognitive en production** :
  - Connecter l'appel à `update_cognitive_state` de [AdvancedRAGService](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/core/domain/services/advanced_rag_service.py) dans les vues de recherche ou de gameplay afin que les retours (plasticité synaptique et état quantique de l'utilisateur) soient appliqués et persistés en temps réel.

---

## 🎨 Qualité de Code & Accessibilité Frontend

### 🧹 Nettoyage des erreurs ESLint
- [ ] **Résoudre les 607 problèmes du linter frontend** :
  - Remplacer l'utilisation abusive du type `any` par des types/interfaces TypeScript adéquats.
  - Corriger la mise à jour synchrone d'état React dans l'effet de [CustomConfigPage.tsx](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/src/pages/utils/CustomConfigPage.tsx) pour éviter les rendus en cascade.
  - Corriger les caractères d'espacement irréguliers dans le fichier de typages généré [api.d.ts](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/src/types/api.d.ts).

### ♿ Accessibilité (a11y)
- [ ] **Exécuter le plan de nettoyage a11y** ([2026-06-09-frontend-a11y-cleanup.md](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/docs/superpowers/plans/2026-06-09-frontend-a11y-cleanup.md)) :
  - Associer correctement les labels et contrôles de formulaires sur les pages d'authentification, de support et de social.
  - Ajouter les écouteurs d'événements clavier (`onKeyDown`) et les rôles ARIA sur les composants interactifs non natifs (ex: cartes cliquables, éléments de Navbar).
  - Ajouter des pistes de sous-titres (`<track>`) sur les lecteurs de média.

---

## 📈 Suivi & Performance (Ops)

- [ ] **Mise en place de métriques de performance granulaires** :
  - Collecter en temps réel le temps d'exécution des requêtes de base de données vectorielles (pgvector) et sémantiques (Neo4j).
  - Enregistrer les temps de réponse de l'API RAG.
- [ ] **Alertes de dégradation de performance** :
  - Configurer un système de notifications/alertes en cas de pic de latence d'inférence ou de dérive sémantique importante des profils d'archetypes utilisateur.

---

## 📚 Documentation Updates Required

### 🏛️ Architecture (ARCHITECTURE.md)
- [ ] Clarify Django's role in the Hexagon diagram (explicit "API Port" or driving adapters note).
- [ ] Explain the omission of `MlopsPort` from the main architectural diagram.
- [ ] Add a brief explanation of why Dependency-Injector is used.

### 📖 Full Guide (FULL_GUIDE.md)
- [ ] Add Local Development Setup guide.
- [ ] Include API Usage Examples.
- [ ] Add Contribution Guidelines.
- [ ] Create a Glossary of Terms.
- [ ] Add Troubleshooting section.
- [ ] Add Hardware Requirements recommendations.
- [ ] Explicitly define "SLM" (Small Language Model).
- [ ] Clarify or expand upon the "Anime Archetype Engine" concept.

### 🗺️ Roadmap (ROADMAP.md)
- [ ] Fix the Gantt chart timeline (currently all marked `:done` despite future dates).
- [ ] Synchronize `ROADMAP.md` initiatives with those listed in `TODO.md`.
- [ ] Add a "Next Steps" section to separate completed foundational AI work from future updates.