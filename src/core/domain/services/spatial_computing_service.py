# -*- coding: utf-8 -*-
"""
Service de Spatial Computing & Génération 3D.
Permet la reconstruction de scènes 3D à partir d'images 2D.
"""

import logging
import base64
import struct
from io import BytesIO
from typing import Dict, Any, Optional
from PIL import Image
import numpy as np
from core.ports.inference_port import InferencePort

logger = logging.getLogger('animetix.spatial')

class SpatialComputingService:
    def __init__(self, inference_engine: InferencePort):
        """
        Initialise le service de spatial computing.
        :param inference_engine: Adaptateur d'inférence sémantique/profondeur.
        """
        self.inference_engine = inference_engine

    def generate_3d_scene(self, image_data: bytes, depth_map: bytes) -> Dict[str, Any]:
        """
        Génère une scène 3D sous forme de nuage de points PLY à partir d'une image RGB et d'une carte de profondeur.
        Transféré depuis les adaptateurs d'inférence pour centraliser la géométrie 3D dans le domaine.
        """
        try:
            rgb = Image.open(BytesIO(image_data)).convert("RGB").resize((256, 256))
            depth = Image.open(BytesIO(depth_map)).convert("L").resize((256, 256))
            rgb_arr, depth_arr = np.array(rgb), np.array(depth)
            h, w = depth_arr.shape
            points = []
            fx, fy = 200.0, 200.0
            cx, cy = w / 2, h / 2
            
            for y in range(h):
                for x in range(w):
                    z = float(depth_arr[y, x]) / 255.0
                    if z <= 0.05:
                        continue
                    X, Y, Z = (x - cx) * z / fx, (y - cy) * z / fy, z
                    r, g, b = rgb_arr[y, x]
                    points.append((X, Y, Z, r, g, b))
                    
            header = (
                "ply\n"
                "format binary_little_endian 1.0\n"
                f"element vertex {len(points)}\n"
                "property float x\n"
                "property float y\n"
                "property float z\n"
                "property uint8 red\n"
                "property uint8 green\n"
                "property uint8 blue\n"
                "end_header\n"
            )
            ply_data = header.encode('ascii')
            for p in points:
                ply_data += struct.pack("<fffBBB", *p)
                
            return {
                "status": "success",
                "model_url": f"data:application/octet-stream;base64,{base64.b64encode(ply_data).decode('utf-8')}",
                "viewer_type": "point_cloud",
                "point_count": len(points)
            }
        except Exception as e:
            logger.error(f"❌ 3D Scene generation failed: {e}")
            return {"status": "error", "message": str(e)}

    def reconstruct_3d_scene(self, image_data: bytes, title: str) -> Dict[str, Any]:
        """
        Pipeline complet : 2D -> Estimation de Profondeur -> 3D Gaussian Splatting (Point Cloud PLY).
        """
        logger.info(f"🌌 Spatial Computing: Starting 3D reconstruction for '{title}'...")
        
        # 1. Estimation de profondeur monoculaire
        logger.info("📏 Estimating Monocular Depth Map...")
        depth_map = self.inference_engine.estimate_depth(image_data)
        
        if not depth_map:
            logger.error("❌ Depth estimation failed. Aborting 3D reconstruction.")
            return {"status": "error", "message": "Failed to generate depth map."}

        # 2. Génération de la scène 3D
        logger.info("🪄 Generating 3D Scene Point Cloud...")
        scene_data = self.generate_3d_scene(image_data, depth_map)
        
        if not scene_data or "model_url" not in scene_data:
            logger.error("❌ 3D Scene generation failed.")
            return {"status": "error", "message": "Failed to generate 3D model."}

        logger.info(f"✅ 3D Scene successfully generated for '{title}'.")
        
        return {
            "status": "success",
            "model_url": scene_data["model_url"],
            "viewer_type": "gaussian_splatting",
            "metadata": {
                "title": title,
                "navigable": True,
                "in_painted_areas": scene_data.get("in_painted", True),
                "point_count": scene_data.get("point_count", 0)
            }
        }
