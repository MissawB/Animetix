# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées sont cochées ou purgées pour être archivées dans `HISTORY.md` et dans la section des succès.

## 🛠️ Dette Technique & Architecture

- [ ] **Diagnostics & Incertitude** : Implémenter `get_diagnostics` et `calculate_uncertainty` dans `InferencePort` et ses adaptateurs pour permettre une observabilité et un calcul d'incertitude mathématique (entropie, perplexité, logit lens) réels.
- [ ] **Bulle de Simulation des Modèles Cognitifs** : Interconnecter le `SynapticPlasticitySimulator` et le `QuantumCognitivePreferenceModel` au pipeline de RAG réel pour influencer dynamiquement les scores de pertinence en fonction des sessions de l'utilisateur.
- [ ] **Génération 3D & Indexation Temporelle** : Implémenter de véritables adaptateurs locaux/cloud pour `generate_3d_scene` (Gaussian Splatting/NeRF) et `get_video_temporal_embeddings` (Video-RAG) à la place des stubs actuels.

## 🧬 Fonctionnalités Créatives

- [x] **Génération Structurée** : Remplacer l'heuristique de regex de parsing JSON par une validation de schéma native via `Instructor` avec Pydantic dans `UnifiedInferenceAdapter` et `FallbackInferenceAdapter` pour Ollama/OpenAI.
- [x] **Modération de contenu sémantique** : Refactoriser `LocalGuardrailAdapter` pour remplacer la liste statique de mots-clés (`bad_words`) par une évaluation sémantique neuronale locale ou un appel structuré.
- [ ] **Pipeline Manga, Visual Rerank & ColPali** : Compléter et stabiliser les intégrations locales de `process_manga_page`, `translate_manga_page`, `visual_rerank` et `get_multimodal_late_interaction` (ColPali).

