from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class InferenceComponentContext:
    """Cross-cutting collaborators a composed inference component needs.

    Built by the host adapter from its own ``_log_usage`` and ``generate``.
    """

    log_usage: Callable[..., None]
    generate: Optional[Callable[..., Any]] = None
