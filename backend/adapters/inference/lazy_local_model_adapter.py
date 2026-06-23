import logging

from core.domain.exceptions import InferenceError
from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.inference.lazy_local")


class LazyLocalModelAdapter(InferencePort):
    """Base for adapters that lazily load a local model.

    Subclasses set ``ENGINE_NAME`` and implement ``_load_model_impl`` (the actual,
    unguarded load). The base provides the guarded lazy-load wrapper and the
    attribute-based ``health_check``. ``_is_loaded`` is the lazy-load guard;
    ``_is_ready`` is the (possibly broader) health signal.
    """

    ENGINE_NAME: str = "local"

    def _load_model(self) -> None:
        if self._is_loaded():
            return
        try:
            self._load_model_impl()
        except Exception as e:
            logger.error(f"❌ Failed to load {self.ENGINE_NAME} model: {e}")
            raise InferenceError(
                f"Critical failure during {self.ENGINE_NAME} model loading: {e}"
            )

    def _is_loaded(self) -> bool:
        return getattr(self, "model", None) is not None

    def _load_model_impl(self) -> None:
        raise NotImplementedError

    def _is_ready(self) -> bool:
        return self._is_loaded()

    def health_check(self) -> dict:
        return {
            "status": "online" if self._is_ready() else "offline",
            "engine": self.ENGINE_NAME,
        }
