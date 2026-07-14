# tests/adapters/test_fallback_capability_delegation.py
import pytest
from adapters.inference.capability_registry import CapabilityRegistry
from adapters.inference.fallback_adapter import FallbackInferenceAdapter
from core.domain.exceptions import InferenceError
from core.ports.inference_port import InferencePort


class _Base(InferencePort):
    def generate(self, *a, **k):
        return None

    def stream_generate(self, *a, **k):
        yield None

    def get_text_embedding(self, *a, **k):
        return []

    def health_check(self):
        return {"status": "offline"}


class _A(_Base):
    pass


class _B(_Base):
    pass


class _VisionCapable(_Base):
    """Ce que porte réellement `UnifiedInferenceAdapter` via ses deux mixins."""

    def get_text_embedding_clip(self, text, model_id):
        return [0.2] * 512

    def get_character_embedding(self, image_data):
        return [0.3] * 768


def test_adapter_exposes_capability_registry():
    fb = FallbackInferenceAdapter([_A(), _B()])
    assert isinstance(fb._capabilities, CapabilityRegistry)
    assert not hasattr(fb, "_capability_cache")
    assert not hasattr(fb, "_build_capability_cache")
    assert not hasattr(fb, "_is_method_overridden")


def test_generate_capability_routed_via_registry():
    a, b = _A(), _B()
    fb = FallbackInferenceAdapter([a, b])
    capable = fb._capabilities.for_method("generate")
    assert a in capable and b in capable


def test_set_primary_adapter_rebuilds_capabilities():
    a, b = _A(), _B()
    fb = FallbackInferenceAdapter([a, b])
    assert fb._capabilities.for_method("generate") == [a, b]
    assert fb.set_primary_adapter(1) is True
    assert fb._capabilities.for_method("generate") == [b, a]


# --------------------------------------------------------------------------
# Les deux tours de la recherche visuelle.
#
# Le FallbackInferenceAdapter délègue une liste EXPLICITE de méthodes : il n'a
# pas de `__getattr__` fourre-tout. Une méthode absente de cette liste n'est pas
# "transmise quand même" — elle n'existe tout simplement pas sur le moteur que le
# conteneur injecte, et l'appelant se prend un AttributeError en production.
# --------------------------------------------------------------------------


def test_the_clip_text_tower_is_delegated_to_an_adapter_that_has_it():
    vision = _VisionCapable()
    fb = FallbackInferenceAdapter([_A(), vision])

    assert (
        fb.get_text_embedding_clip("une fille aux cheveux blancs", "m") == [0.2] * 512
    )


def test_the_character_encoder_is_delegated_to_an_adapter_that_has_it():
    vision = _VisionCapable()
    fb = FallbackInferenceAdapter([_A(), vision])

    assert fb.get_character_embedding(b"png") == [0.3] * 768


def test_a_chain_that_cannot_serve_clip_text_raises_instead_of_returning_empty():
    """Dans le conteneur web, la chaîne est [BrainAPI, Gemini] : ni l'un ni l'autre
    ne porte CLIP. Rendre `[]` ici, c'est chercher avec un vecteur vide — un
    résultat qui a l'air d'en être un."""
    fb = FallbackInferenceAdapter([_A(), _B()])

    with pytest.raises(InferenceError):
        fb.get_text_embedding_clip("texte", "m")


def test_a_chain_that_cannot_serve_ccip_raises_instead_of_returning_empty():
    fb = FallbackInferenceAdapter([_A(), _B()])

    with pytest.raises(InferenceError):
        fb.get_character_embedding(b"png")


def test_an_adapter_that_crashes_falls_through_to_one_that_works():
    class _Broken(_Base):
        def get_character_embedding(self, image_data):
            raise RuntimeError("le GPU est parti")

    fb = FallbackInferenceAdapter([_Broken(), _VisionCapable()])

    assert fb.get_character_embedding(b"png") == [0.3] * 768
