import os
import requests
import numpy as np
from typing import List, Dict, Optional
from core.ports.inference_port import InferencePort

class AdvancedVisionService:
    def __init__(self, inference_engine: InferencePort):
        self.inference_engine = inference_engine
        # Modèles spécialisés
        self.clip_anime_model = "dudcjs2779/anime-style-tag-clip"
        self.face_reid_model = "deepghs/ccip"
        self.owl_vit_model = "google/owlvit-base-patch32" # Open-World Object Detection
        
        # Adaptateur LoRA spécifique (ex: Makoto Shinkai Style)
        self.style_adapters = {
            "shinkai": "MissawB/clip-shinkai-lora" # Simulation d'un adaptateur LoRA
        }

    def get_unified_embedding(self, data: bytes, is_image: bool = True) -> List[float]:
        """
        Espace Latent Unifié : Projette texte ou image dans le même espace vectoriel.
        Permet la recherche Image-to-Text et Text-to-Image.
        """
        if is_image:
            return self.inference_engine.get_image_embedding(data, model_id=self.clip_anime_model)
        else:
            # Pour le texte, on utilise l'encodeur de texte de CLIP (via generate ou méthode spécifique)
            # Ici on simule l'appel à l'encodeur de texte CLIP
            return [] 

    def detect_visual_attributes(self, image_data: bytes) -> List[str]:
        """
        Détection d'attributs via OWL-ViT ou YOLOv8-World.
        Transforme le contenu visuel en tags pour le graphe (ex: "katana", "mecha").
        """
        candidate_queries = ["katana", "school uniform", "robot", "magical girl wand", "dragon", "cyberpunk city"]
        detections = self.inference_engine.detect_objects(
            image_data, 
            candidate_queries=candidate_queries, 
            model_id=self.owl_vit_model
        )
        
        # On ne garde que les tags avec un score de confiance > 0.5
        return [d['label'] for d in detections if d['score'] > 0.5]

    def get_style_embedding_with_lora(self, image_data: bytes, artist_key: str = "shinkai") -> List[float]:
        """
        Extrait un embedding de style en utilisant un adaptateur LoRA spécifique.
        """
        adapter_id = self.style_adapters.get(artist_key)
        return self.inference_engine.get_image_embedding(image_data, model_id=adapter_id or self.clip_anime_model)

    def identify_artist_style(self, image_data: bytes) -> str:
        """Identifie le style artistique via classification zero-shot."""
        styles = ["Studio MAPPA", "Ufotable", "Kyoto Animation", "Shaft", "Studio Ghibli", "Wit Studio", "Madhouse", "Bones"]
        scores = self.inference_engine.classify_image(image_data, candidate_labels=styles, model_id=self.clip_anime_model)
        return max(scores, key=scores.get) if scores else "Inconnu"

    def get_character_face_embedding(self, image_data: bytes) -> List[float]:
        return self.inference_engine.get_image_embedding(image_data, model_id=self.face_reid_model)

    def calculate_visual_resemblance(self, image_a: bytes, image_b: bytes) -> float:
        """Calcule la similarité cosinus entre deux images."""
        emb_a = self.get_unified_embedding(image_a)
        emb_b = self.get_unified_embedding(image_b)
        if not emb_a or not emb_b: return 0.0
        
        # Similarité cosinus simple
        a = np.array(emb_a)
        b = np.array(emb_b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def vlm_rerank(self, query: str, candidate_items: List[Dict]) -> List[Dict]:
        """
        Reranking Visuel Direct (VLM-as-a-Reranker).
        Demande au modèle de 'regarder' les posters et de choisir le meilleur.
        """
        image_urls = [item.get('image') for item in candidate_items if item.get('image')]
        if not image_urls: return candidate_items

        ranked_indices = self.inference_engine.visual_rerank(query, image_urls)
        
        # Reconstruction de la liste ordonnée
        reranked = []
        try:
            for idx in ranked_indices:
                if 0 <= idx < len(candidate_items):
                    reranked.append(candidate_items[idx])
            
            # Ajout des items restants (si le VLM en a oublié)
            for item in candidate_items:
                if item not in reranked:
                    reranked.append(item)
                    
            return reranked
        except:
            return candidate_items
