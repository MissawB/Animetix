# API Specification – InferencePort

Ce document recense toutes les méthodes exposées par `InferencePort` et leur statut d'implémentation par adaptateur.

> [!NOTE]
> Les méthodes marquées ❌ lèvent `InferenceNotImplementedError`. Les méthodes marquées ⚠️ ont une implémentation partielle (fallback ou simplifiée).

## Méthodes Texte

| Méthode | Fallback | BrainAPI | VLLM | GGUF | LocalText | Langchain |
|---------|----------|----------|------|------|-----------|-----------|
| `generate` | ✅ (chaîné) | ✅ | ✅ | ✅ | ✅ | ✅ |
| `stream_generate` | ✅ (chaîné) | ✅ | ✅ | ✅ | ❌ | ❌ |
| `generate_structured` | ✅ (chaîné) | ✅ | ✅ | ⚠️ (via JSON parsing) | ⚠️ | ❌ |
| `rerank_documents` | ✅ (chaîné) | ❌ | ❌ | ✅ (CrossEncoder) | ❌ | ❌ |
| `moderate_content` | ✅ (chaîné) | ❌ | ❌ | ⚠️ (mots-clés) | ❌ | ❌ |
| `get_diagnostics` | ✅ (chaîné) | ❌ | ❌ | ❌ | ❌ | ❌ |
| `calculate_uncertainty` | ✅ (chaîné) | ❌ | ❌ | ❌ | ❌ | ❌ |

## Méthodes Vision (Images)

| Méthode | Fallback | VisionTF | Diffusers | GGUF | Moondream |
|---------|----------|----------|-----------|------|-----------|
| `generate_image` | ✅ (chaîné) | ❌ | ✅ | ❌ | ❌ |
| `generate_sprite` | ✅ (via generate_image) | ❌ | ✅ | ❌ | ❌ |
| `generate_image_description` | ✅ (chaîné) | ✅ (Moondream2) | ❌ | ⚠️ (Llava) | ✅ |
| `get_image_embedding` | ✅ (chaîné) | ✅ (CLIP) | ❌ | ❌ | ❌ |
| `classify_image` | ✅ (chaîné) | ✅ (CLIP) | ❌ | ❌ | ❌ |
| `detect_objects` | ✅ (chaîné) | ✅ (OWL-ViT) | ❌ | ❌ | ❌ |
| `calculate_visual_similarity` | ✅ (chaîné) | ✅ (CLIP) | ❌ | ❌ | ❌ |
| `visual_rerank` | ✅ (chaîné) | ✅ (CLIP) | ❌ | ❌ | ❌ |
| `get_multimodal_late_interaction` | ✅ (chaîné) | ✅ (ColPali) | ❌ | ❌ | ❌ |
| `transform_image_to_anime` | ✅ (chaîné) | ❌ | ✅ (Img2Img) | ❌ | ❌ |
| `estimate_depth` | ✅ (chaîné) | ✅ (DepthAnything) | ✅ (DepthAnything) | ❌ | ❌ |
| `generate_3d_scene` | ✅ (chaîné) | ✅ (Point Cloud) | ❌ | ✅ (Point Cloud) | ❌ |

## Méthodes Vidéo

| Méthode | Fallback | VisionTF | Diffusers | GGUF |
|---------|----------|----------|-----------|------|
| `get_video_temporal_embeddings` | ✅ (chaîné) | ✅ (Qwen2-VL) | ❌ | ❌ |
| `localize_video_actions` | ✅ (chaîné) | ✅ (Qwen2-VL) | ❌ | ✅ (Llava frame-by-frame) |
| `generate_video_description` | ✅ (chaîné) | ✅ (Qwen2-VL) | ❌ | ❌ |
| `transform_video_to_anime` | ✅ (chaîné) | ❌ | ✅ (Img2Img séquentiel) | ❌ |

## Méthodes Audio

| Méthode | Fallback | AudioTF | XTTS |
|---------|----------|---------|------|
| `generate_soundscape` | ✅ (chaîné) | ❌ | ❌ |
| `clone_voice` | ✅ (chaîné) | ❌ | ❌ |
| `speech_to_speech` | ✅ (chaîné) | ❌ | ❌ |

## Méthodes Manga

| Méthode | Fallback | VisionTF | Diffusers | MangaOCR |
|---------|----------|----------|-----------|----------|
| `process_manga_page` | ✅ (chaîné) | ✅ (TrOCR) | ❌ | ✅ |
| `translate_manga_page` | ✅ (chaîné) | ❌ | ❌ | ❌ |
| `inpaint_text_bubbles` | ✅ (chaîné) | ❌ | ✅ (Inpainting) | ❌ |

---

## Légende
- ✅ = Implémentation complète et fonctionnelle
- ⚠️ = Implémentation partielle ou simplifiée
- ❌ = Non implémenté (lève `InferenceNotImplementedError` ou délègue au port par défaut)
- ✅ (chaîné) = Le `FallbackInferenceAdapter` tente chaque adaptateur enregistré dans l'ordre
