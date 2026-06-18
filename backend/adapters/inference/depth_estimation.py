"""Depth estimation and 3D scene generation mixin for VisionTransformersAdapter."""

import logging  # noqa: E402
import struct  # noqa: E402
from typing import Any, Dict  # noqa: E402

from core.domain.exceptions import InferenceError  # noqa: E402
from core.utils.lazy_import import lazy_import  # noqa: E402

torch = lazy_import("torch")
transformers = lazy_import("transformers")
pipeline = transformers.pipeline

logger = logging.getLogger("animetix.inference.depth")


class DepthEstimationMixin:
    """Provides depth estimation and 3D point cloud generation."""

    def estimate_depth(self, image_data: bytes) -> bytes:
        """Estime la profondeur d'une image en utilisant Depth-Anything."""
        try:
            from io import BytesIO  # noqa: E402

            from PIL import Image  # noqa: E402

            img = Image.open(BytesIO(image_data)).convert("RGB")

            model_id = "LiheYoung/depth-anything-small-hf"
            if not hasattr(self, "_depth_pipeline"):
                logger.info(f"🏗️ Loading {model_id}...")
                self._depth_pipeline = pipeline(
                    "depth-estimation",
                    model=model_id,
                    device=0 if torch.cuda.is_available() else -1,
                )

            result = self._depth_pipeline(img)
            depth_img = result["depth"]

            self._log_usage(engine=f"transformers:{model_id}", units=1)

            buf = BytesIO()
            depth_img.save(buf, format="PNG")
            return buf.getvalue()
        except Exception as e:
            logger.error(f"❌ Depth estimation failed: {e}")
            raise InferenceError(f"Depth estimation failed: {str(e)}")

    def generate_3d_scene(
        self, image_data: bytes, depth_map: bytes, mode: str = "point_cloud"
    ) -> Dict[str, Any]:
        """
        Génère une scène 3D.
        Modes supportés: 'point_cloud' (Standard) ou 'gaussian_splatting' (SOTA).
        """
        if mode == "gaussian_splatting":
            return self.generate_3d_splats(image_data, depth_map)
        return self._generate_point_cloud(image_data, depth_map)

    def _generate_point_cloud(
        self, image_data: bytes, depth_map: bytes
    ) -> Dict[str, Any]:
        """Génère un nuage de points PLY binaire (Legacy)."""
        try:
            import base64  # noqa: E402
            from io import BytesIO  # noqa: E402

            import numpy as np  # noqa: E402
            from core.constants import DEFAULT_DEPTH_RESIZE  # noqa: E402
            from core.constants import (
                DEFAULT_DEPTH_THRESHOLD,
                DEFAULT_FOCAL_LENGTH,
                PLY_HEADER_TEMPLATE,
            )
            from PIL import Image  # noqa: E402

            resize = DEFAULT_DEPTH_RESIZE
            rgb = Image.open(BytesIO(image_data)).convert("RGB").resize(resize)
            depth = Image.open(BytesIO(depth_map)).convert("L").resize(resize)
            rgb_arr, depth_arr = np.array(rgb), np.array(depth)

            h, w = depth_arr.shape
            points = []
            fx = fy = DEFAULT_FOCAL_LENGTH
            cx, cy = w / 2, h / 2

            for y in range(h):
                for x in range(w):
                    z = float(depth_arr[y, x]) / 255.0
                    if z <= DEFAULT_DEPTH_THRESHOLD:
                        continue
                    X = (x - cx) * z / fx
                    Y = (y - cy) * z / fy
                    Z = z
                    r, g, b = rgb_arr[y, x]
                    points.append((X, Y, Z, r, g, b))

            header = PLY_HEADER_TEMPLATE.format(vertex_count=len(points))
            ply_data = header.encode("ascii")
            for p in points:
                ply_data += struct.pack("<fffBBB", *p)

            self._log_usage(engine="vision:3d_point_cloud", units=1)

            return {
                "status": "success",
                "model_url": f"data:application/octet-stream;base64,{base64.b64encode(ply_data).decode('utf-8')}",
                "point_count": len(points),
                "format": "point_cloud",
                "metadata": {"original_size": len(image_data)},
            }
        except Exception as e:
            logger.error(f"❌ Point cloud generation failed: {e}")
            raise InferenceError(f"Point cloud generation failed: {str(e)}")

    def generate_3d_splats(self, image_data: bytes, depth_map: bytes) -> Dict[str, Any]:
        """
        Génère des Gaussian Splats (SOTA 2026) à partir d'une image RGB-D.
        Chaque pixel devient une gaussienne avec SH, opacité, échelle et rotation.
        """
        try:
            import base64  # noqa: E402
            from io import BytesIO  # noqa: E402

            import numpy as np  # noqa: E402
            from core.constants import DEFAULT_DEPTH_RESIZE  # noqa: E402
            from core.constants import (
                DEFAULT_DEPTH_THRESHOLD,
                DEFAULT_FOCAL_LENGTH,
                DEFAULT_GAUSSIAN_OPACITY,
                GAUSSIAN_PLY_HEADER,
                GAUSSIAN_SCALE_FACTOR,
                SH_C0,
            )
            from PIL import Image  # noqa: E402

            resize = DEFAULT_DEPTH_RESIZE
            rgb = Image.open(BytesIO(image_data)).convert("RGB").resize(resize)
            depth = Image.open(BytesIO(depth_map)).convert("L").resize(resize)
            rgb_arr, depth_arr = np.array(rgb) / 255.0, np.array(depth) / 255.0

            h, w = depth_arr.shape
            fx = fy = DEFAULT_FOCAL_LENGTH
            cx, cy = w / 2, h / 2

            gaussians = []

            for y in range(h):
                for x in range(w):
                    z = depth_arr[y, x]
                    if z <= DEFAULT_DEPTH_THRESHOLD:
                        continue

                    # Position 3D
                    X = (x - cx) * z / fx
                    Y = (y - cy) * z / fy
                    Z = z

                    # Normal (pointant vers la caméra par défaut pour une projection 2D)
                    nx, ny, nz = 0.0, 0.0, -1.0

                    # Couleurs SH (Harmoniques sphériques base dc)
                    # Formule simplifiée : (color - 0.5) / SH_C0
                    r, g, b = rgb_arr[y, x]
                    f_dc_0 = (r - 0.5) / SH_C0
                    f_dc_1 = (g - 0.5) / SH_C0
                    f_dc_2 = (b - 0.5) / SH_C0

                    opacity = DEFAULT_GAUSSIAN_OPACITY  # Pleine opacité pour les surfaces franches

                    # Échelle (adaptée à la densité de la grille)
                    scale_0 = scale_1 = scale_2 = np.log(GAUSSIAN_SCALE_FACTOR * z)

                    # Rotation (quaternion identité : [1, 0, 0, 0])
                    rot_0, rot_1, rot_2, rot_3 = 1.0, 0.0, 0.0, 0.0

                    gaussians.append(
                        (
                            X,
                            Y,
                            Z,
                            nx,
                            ny,
                            nz,
                            f_dc_0,
                            f_dc_1,
                            f_dc_2,
                            opacity,
                            scale_0,
                            scale_1,
                            scale_2,
                            rot_0,
                            rot_1,
                            rot_2,
                            rot_3,
                        )
                    )

            header = GAUSSIAN_PLY_HEADER.format(vertex_count=len(gaussians))
            ply_data = header.encode("ascii")
            for g in gaussians:
                # 17 floats: x,y,z, nx,ny,nz, f_dc_0,1,2, opacity, scale_0,1,2, rot_0,1,2,3
                ply_data += struct.pack("<17f", *g)

            self._log_usage(engine="vision:gaussian_splatting", units=1)

            return {
                "status": "success",
                "model_url": f"data:application/octet-stream;base64,{base64.b64encode(ply_data).decode('utf-8')}",
                "point_count": len(gaussians),
                "format": "gaussian_splatting",
                "metadata": {"sota_version": "2026.1"},
            }
        except Exception as e:
            logger.error(f"❌ Gaussian Splatting generation failed: {e}")
            raise InferenceError(f"Gaussian Splatting generation failed: {str(e)}")
