from io import BytesIO
from PIL import Image

def create_image_bytes(width: int = 256, height: int = 256, mode: str = "RGB", fmt: str = "JPEG") -> bytes:
    """Create an image of the given size/mode and return its bytes in the requested format.
    Used by test fixtures to provide realistic image data without touching the filesystem.
    """
    img = Image.new(mode, (width, height), color=(73, 109, 137))
    buf = BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()
