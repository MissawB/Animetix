"""L'adaptateur d'image doit charger le modèle qu'on lui demande.

Aujourd'hui il ignore `model_id` et charge toujours `clip-ViT-B-32` — donc
choisir un modèle ne sert à rien, et un index construit avec un autre modèle
serait interrogé avec le mauvais. Et un échec d'embedding rend `[]`, ce qui
devient un vecteur vide passé à la recherche : encore un zéro silencieux.
"""

from unittest.mock import MagicMock, patch

import pytest
from core.domain.exceptions import InferenceError


def _adapter():
    from adapters.inference.clip_vision import ClipVisionMixin

    class _Engine(ClipVisionMixin):
        def _log_usage(self, **kwargs):
            pass

    return _Engine()


PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
    b"\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01"
    b"\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_the_requested_model_is_the_model_loaded():
    with patch("adapters.inference.clip_vision._load_open_clip") as loader:
        loader.return_value = MagicMock(
            encode_image=MagicMock(return_value=[0.1] * 512)
        )
        _adapter().get_image_embedding(PNG, model_id="dudcjs2779/anime-style-tag-clip")

    loader.assert_called_once_with("dudcjs2779/anime-style-tag-clip")


def test_two_models_do_not_share_one_cached_instance():
    # Un seul `self._clip_model` pour deux modèles, et le second appel rendrait
    # les vecteurs du premier -- silencieusement.
    with patch("adapters.inference.clip_vision._load_open_clip") as loader:
        loader.side_effect = lambda name: MagicMock(
            encode_image=MagicMock(return_value=[0.1] * 512), name=name
        )
        adapter = _adapter()
        adapter.get_image_embedding(PNG, model_id="dudcjs2779/anime-style-tag-clip")
        adapter.get_image_embedding(PNG, model_id="clip-ViT-B-32")

    assert loader.call_count == 2


def test_a_failed_embedding_raises_instead_of_returning_an_empty_list():
    with patch("adapters.inference.clip_vision._load_open_clip") as loader:
        loader.side_effect = RuntimeError("model is gone")
        with pytest.raises(InferenceError):
            _adapter().get_image_embedding(PNG, model_id="clip-ViT-B-32")


def test_an_unreadable_image_raises():
    with pytest.raises(InferenceError):
        _adapter().get_image_embedding(b"not an image", model_id="clip-ViT-B-32")
