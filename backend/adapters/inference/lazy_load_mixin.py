import logging
from typing import Any, Callable, Literal

from core.domain.exceptions import InferenceError

logger = logging.getLogger("animetix.inference.lazy_load")


class LazyLoadMixin:
    """Idempotent best-effort lazy-load helper for adapters/mixins that load
    several sub-models on demand (each into its own attribute).

    ``_lazy_load`` is a no-op when ``attr`` is already truthy; otherwise it runs
    ``loader`` (which sets ``self.<attr>``). On failure it logs and, by policy,
    either swallows (default) or wraps the error in ``InferenceError``.
    """

    def _lazy_load(
        self,
        attr: str,
        loader: Callable[[], Any],
        *,
        label: str,
        on_error: Literal["swallow", "raise"] = "swallow",
    ) -> None:
        if getattr(self, attr, None):
            return
        try:
            loader()
        except Exception as e:
            logger.error(f"❌ Failed to load {label}: {e}")
            if on_error == "raise":
                raise InferenceError(
                    f"Critical failure during {label} model loading: {e}"
                )
