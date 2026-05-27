import pytest
import io
import base64
from PIL import Image
from adapters.inference.vision_transformers_adapter import VisionTransformersAdapter

def test_generate_3d_scene_returns_valid_ply():
    adapter = VisionTransformersAdapter()
    
    # Create dummy RGB and Depth data
    img = Image.new('RGB', (10, 10), color='red')
    img_buf = io.BytesIO(); img.save(img_buf, format="PNG")
    
    depth = Image.new('L', (10, 10), color=128)
    depth_buf = io.BytesIO(); depth.save(depth_buf, format="PNG")
    
    res = adapter.generate_3d_scene(img_buf.getvalue(), depth_buf.getvalue())
    
    assert res["status"] == "success"
    assert "data:application/octet-stream;base64," in res["model_url"]
    
    # Decode and check PLY header
    header_b64 = res["model_url"].split(",")[1]
    ply_data = base64.b64decode(header_b64)
    assert ply_data.startswith(b"ply")
    assert b"format binary_little_endian 1.0" in ply_data