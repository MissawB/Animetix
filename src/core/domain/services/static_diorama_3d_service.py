# -*- coding: utf-8 -*-
"""
Static Diorama 3D Service (SGS - Static Gaussian Splatting) for Animetix.
Reconstructs a static 3D volumetric scene from a single 2D image.
"""

import logging
from typing import Dict, Any, Optional
from core.ports.inference_port import InferencePort

logger = logging.getLogger('animetix.spatial.static')

class StaticDiorama3DService:
    """
    Service de Calcul Spatial Statique (SGS - Static Gaussian Splatting).
    Permet la reconstruction volumétrique 3D d'une image fixe unique (ex: poster de La Forge).
    """
    def __init__(self, inference_engine: Optional[InferencePort] = None, vision_service: Optional[Any] = None, **kwargs):
        self.inference_engine = inference_engine or vision_service


    def reconstruct_static_diorama(self, image_data: bytes, title: str) -> Dict[str, Any]:
        """
        Pipeline complet 2D fixe -> Estimation de Profondeur -> Diorama Spatial 3D.
        """
        logger.info(f"🌌 SGS Spatial: Starting Static 3D reconstruction for '{title}'...")
        
        # 1. Estimation de profondeur monoculaire
        logger.info("📏 Estimating Monocular Depth Map...")
        depth_map = self.inference_engine.estimate_depth(image_data)
        
        if not depth_map:
            logger.error("❌ Depth estimation failed. Aborting SGS reconstruction.")
            return {"status": "error", "message": "Failed to generate depth map."}

        # 2. Génération du diorama 3D par Gaussian Splatting
        logger.info("🪄 Generating 3D Static Diorama via Gaussian Splatting (with 3D in-painting)...")
        scene_data = self.inference_engine.generate_3d_scene(image_data, depth_map)
        
        if not scene_data or "model_url" not in scene_data:
            logger.error("❌ 3D Diorama generation failed.")
            return {"status": "error", "message": "Failed to generate 3D model."}

        logger.info(f"✅ SGS Static 3D Diorama generated for '{title}'. Ready for VR exploration.")
        
        return {
            "status": "success",
            "model_url": scene_data["model_url"],
            "viewer_type": "static_gaussian_diorama",
            "metadata": {
                "title": title,
                "navigable": True,
                "mode": "SGS_Static_Diorama_3D",
                "in_painted_areas": scene_data.get("in_painted", True)
            }
        }
