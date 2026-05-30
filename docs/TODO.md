# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées sont cochées ou purgées pour être archivées dans `HISTORY.md`.

## 🛠️ Dette Technique & Architecture (Inférence)

- [ ] **Diagnostics & Incertitude Avancés** : Migrer les calculs d'incertitude (entropie, perplexité) basés sur le texte vers une exploitation réelle des `logprobs` si exposés par les adaptateurs (BrainAPI/Ollama).
- [ ] **Nettoyage des Bouchons (UnifiedInferenceAdapter)** : Finaliser le remplacement de toutes les méthodes levant encore `InferenceNotImplementedError` par de véritables délégations vers les mixins de vision ou d'audio.
- [ ] **Modération de contenu (Guardrails)** : Étendre la modération sémantique native à tous les adaptateurs de texte pour garantir une sécurité homogène sur tout le cluster.

## 🧬 Fonctionnalités SOTA & Innovations

- [x] **Simulations Cognitives** : Interconnecter le `SynapticPlasticitySimulator` (Heure de Hebb/STDP) et le `QuantumCognitivePreferenceModel` au pipeline de RAG réel. L'historique conceptuel de l'utilisateur doit influencer dynamiquement les scores de pertinence du reranker. (FAIT, modèles interconnectés via AdvancedRAGService et mis à jour par RAGWorkflowManager).
- [ ] **Génération 3D & Dioramas** : Remplacer les stubs par une intégration réelle de **Gaussian Splatting** ou de reconstruction volumétrique pour transformer des images d'anime en scènes 3D immersives.
- [ ] **Vidéo-RAG (Embeddings Temporels)** : Implémenter l'extraction d'embeddings temporels via Qwen2-VL pour permettre une recherche sémantique précise à l'intérieur de clips vidéo.

