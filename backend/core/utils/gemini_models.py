"""
Single source of truth for the Gemini model ids used across Animetix.

Three canonical roles, each env-overridable. Centralizing here prevents the
version drift that scattered string literals caused (1.5 / 2.0-exp / 2.5 / 3.5
/ 3-preview). Pure module — only `os`.
"""

import os

GEMINI_FLASH = os.getenv("ANIMETIX_GEMINI_MODEL", "gemini-3.5-flash")
GEMINI_LIVE = os.getenv(
    "ANIMETIX_GEMINI_LIVE_MODEL", "gemini-live-2.5-flash-native-audio"
)
GEMINI_EMBEDDING = os.getenv("ANIMETIX_GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")
