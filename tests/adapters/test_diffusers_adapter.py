import pytest
from unittest.mock import MagicMock
from backend.adapters.inference.diffusers_adapter import DiffusersAdapter

def test_inpaint_text_bubbles_pillow_fallback_when_pipe_none():
    # Instancier DiffusersAdapter sans charger le pipeline neuronal (qui restera à None)
    adapter = DiffusersAdapter(model_id="stabilityai/sdxl-turbo", use_fp16=False)
    adapter._inpaint_pipe = None  # S'assurer qu'il est à None pour forcer le fallback
    
    # Créer de fausses données d'image 100x100 en bytes
    from PIL import Image
    from io import BytesIO
    img = Image.new("RGB", (100, 100), "black")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    image_bytes = buf.getvalue()
    
    # Exécuter inpaint_text_bubbles
    bubbles = [{"bbox": [10, 10, 90, 90], "text": "TEST"}]
    result = adapter.inpaint_text_bubbles(image_bytes, bubbles)
    
    # Vérifier que le résultat renvoie une URL base64 JPEG valide
    assert result.startswith("data:image/jpeg;base64,")
