"""Centralized constants for the Anime-Archetype-Engine project.

Avoids hard-coded magic numbers scattered across adapter implementations.
"""

# --- Depth Estimation & 3D Scene Generation ---
DEFAULT_FOCAL_LENGTH = 150.0

DEFAULT_DEPTH_RESIZE = (128, 128)

DEFAULT_DEPTH_THRESHOLD = 0.1

# --- Video Processing ---
DEFAULT_MAX_FRAMES = 8
DEFAULT_VIDEO_FPS_FALLBACK = 24

# --- Local Inference ---
DEFAULT_MAX_TOKENS = 512

# --- Image Processing ---
DEFAULT_DETECTION_THRESHOLD = 0.05
DEFAULT_IMG2IMG_RESIZE = (512, 512)

# --- Media upload validation (size limits + MIME allow-lists) ---
# Centralized here so the API layer (core.py / labs.py) shares one source of truth.
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_AUDIO_SIZE = 15 * 1024 * 1024  # 15 MB

ALLOWED_IMAGE_MIMES = ["image/jpeg", "image/png", "image/webp", "image/gif"]
ALLOWED_VIDEO_MIMES = ["video/mp4", "video/webm", "video/x-msvideo"]
ALLOWED_AUDIO_MIMES = ["audio/mpeg", "audio/wav", "audio/ogg", "audio/x-wav"]

# --- PLY Format ---
PLY_HEADER_TEMPLATE = (
    "ply\n"
    "format binary_little_endian 1.0\n"
    "element vertex {vertex_count}\n"
    "property float x\n"
    "property float y\n"
    "property float z\n"
    "property uint8 red\n"
    "property uint8 green\n"
    "property uint8 blue\n"
    "end_header\n"
)

# 3D Gaussian Splatting Constants
SH_C0 = 0.28209479177387814
GAUSSIAN_SCALE_FACTOR = 0.01
DEFAULT_GAUSSIAN_OPACITY = 1.0

# 3D Gaussian Splatting Header (Simplified SOTA 2026 version)
# Includes SH (Spherical Harmonics) coefficients for view-dependent color
GAUSSIAN_PLY_HEADER = (
    "ply\n"
    "format binary_little_endian 1.0\n"
    "element vertex {vertex_count}\n"
    "property float x\n"
    "property float y\n"
    "property float z\n"
    "property float nx\n"
    "property float ny\n"
    "property float nz\n"
    "property float f_dc_0\n"
    "property float f_dc_1\n"
    "property float f_dc_2\n"
    "property float opacity\n"
    "property float scale_0\n"
    "property float scale_1\n"
    "property float scale_2\n"
    "property float rot_0\n"
    "property float rot_1\n"
    "property float rot_2\n"
    "property float rot_3\n"
    "end_header\n"
)
