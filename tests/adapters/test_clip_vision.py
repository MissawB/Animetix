"""L'adaptateur d'image doit charger le modèle qu'on lui demande.

Aujourd'hui il ignore `model_id` et charge toujours `clip-ViT-B-32` — donc
choisir un modèle ne sert à rien, et un index construit avec un autre modèle
serait interrogé avec le mauvais. Et un échec d'embedding rend `[]`, ce qui
devient un vecteur vide passé à la recherche : encore un zéro silencieux.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest
from core.domain.exceptions import InferenceError


@pytest.fixture(autouse=True)
def _clean_model_cache():
    """Le cache est un dict de module : sans ça il fuit d'un test à l'autre."""
    from adapters.inference import clip_vision

    clip_vision._MODEL_CACHE.clear()
    yield
    clip_vision._MODEL_CACHE.clear()


@pytest.fixture
def fake_open_clip(monkeypatch):
    """`open_clip` n'est pas installé dans le venv (il n'est que dans le lock).

    On injecte un module factice au point d'import, ce que `_load_open_clip`
    fera via `import open_clip`. `monkeypatch.setitem` le retire ensuite —
    un stub laissé dans `sys.modules` contaminerait tout le reste de la suite.
    """
    module = MagicMock()
    module.create_model_and_transforms.side_effect = lambda name: (
        MagicMock(name=f"model:{name}"),
        None,
        MagicMock(name=f"preprocess:{name}"),
    )
    module.get_tokenizer.side_effect = lambda name: MagicMock(name=f"tok:{name}")
    monkeypatch.setitem(sys.modules, "open_clip", module)
    return module


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


# --- Le VRAI `_load_open_clip` : c'est lui qui détient `_MODEL_CACHE` ---------
# Les tests ci-dessus le remplacent par un mock, donc ils ne prouvent rien du
# cache lui-même. Ici on n'endort que les chargeurs (sentence-transformers /
# open_clip) à leur point d'import, et on laisse tourner le vrai code.


def test_the_same_model_id_is_loaded_once_and_returns_the_identical_object():
    from adapters.inference.clip_vision import _MODEL_CACHE, _load_open_clip

    with patch("sentence_transformers.SentenceTransformer") as st:
        st.return_value = MagicMock(name="clip-ViT-B-32")

        first = _load_open_clip("clip-ViT-B-32")
        second = _load_open_clip("clip-ViT-B-32")

    # Un cache qui ne cache pas, c'est un modèle rechargé à chaque image.
    assert st.call_count == 1
    assert first is second
    assert _MODEL_CACHE["clip-ViT-B-32"] is first


def test_two_model_ids_are_two_distinct_simultaneous_entries(fake_open_clip):
    from adapters.inference.clip_vision import _MODEL_CACHE, _load_open_clip

    with patch("sentence_transformers.SentenceTransformer") as st:
        st.return_value = MagicMock(name="st-instance")

        hub = _load_open_clip("dudcjs2779/anime-style-tag-clip")  # -> open_clip
        legacy = _load_open_clip("clip-ViT-B-32")  # -> sentence-transformers

        # Et ils coexistent : redemander l'un ne doit pas rendre l'autre.
        assert _load_open_clip("dudcjs2779/anime-style-tag-clip") is hub
        assert _load_open_clip("clip-ViT-B-32") is legacy

    assert hub is not legacy
    # Un cache à une seule case rendrait le second modèle pour le premier id.
    assert set(_MODEL_CACHE) == {"dudcjs2779/anime-style-tag-clip", "clip-ViT-B-32"}
    assert _MODEL_CACHE["dudcjs2779/anime-style-tag-clip"] is hub
    assert _MODEL_CACHE["clip-ViT-B-32"] is legacy
    # Chacun n'a été chargé qu'une fois, par SON backend.
    assert st.call_count == 1
    st.assert_called_once_with("clip-ViT-B-32")
    fake_open_clip.create_model_and_transforms.assert_called_once_with(
        "hf-hub:dudcjs2779/anime-style-tag-clip"
    )


# --- La tour TEXTE ------------------------------------------------------------


def test_text_embedding_uses_the_text_tower_of_the_requested_model():
    """Le vecteur texte doit sortir du modèle DEMANDÉ, pas d'un autre."""
    adapter = _adapter()

    with patch("sentence_transformers.SentenceTransformer") as st:
        st.return_value = MagicMock(
            encode=MagicMock(return_value=MagicMock(tolist=lambda: [0.7] * 512))
        )

        vector = adapter.get_text_embedding_clip("un chat roux", "clip-ViT-B-32")

    st.assert_called_once_with("clip-ViT-B-32")
    st.return_value.encode.assert_called_once_with("un chat roux")
    assert vector == [0.7] * 512


def test_text_embedding_on_a_hub_model_goes_through_open_clip(fake_open_clip):
    """Un modèle OpenCLIP : c'est son tokenizer + sa tour texte qu'on utilise."""
    import torch

    adapter = _adapter()
    model, _, _ = fake_open_clip.create_model_and_transforms(
        "hf-hub:dudcjs2779/anime-style-tag-clip"
    )
    fake_open_clip.create_model_and_transforms.reset_mock()
    fake_open_clip.create_model_and_transforms.side_effect = None
    fake_open_clip.create_model_and_transforms.return_value = (model, None, MagicMock())
    model.encode_text.return_value = torch.tensor([[3.0, 4.0]])

    vector = adapter.get_text_embedding_clip(
        "cheveux roses", "dudcjs2779/anime-style-tag-clip"
    )

    fake_open_clip.get_tokenizer.assert_called_once_with(
        "hf-hub:dudcjs2779/anime-style-tag-clip"
    )
    model.encode_text.assert_called_once()
    # normalisé L2 : (3,4)/5 == (0.6, 0.8)
    assert vector == pytest.approx([0.6, 0.8])


def test_text_embedding_raises_when_the_model_has_no_text_tower():
    """Pas de `return []` : un vecteur vide se moyennerait au vecteur image et
    la recherche rendrait un score qui a l'air d'en être un."""
    no_text_tower = MagicMock(spec=["encode_image"])  # pas d'`encode_text`

    with patch(
        "adapters.inference.clip_vision._load_open_clip", return_value=no_text_tower
    ):
        with pytest.raises(InferenceError):
            _adapter().get_text_embedding_clip("un chat", "image-only-model")


def test_text_embedding_raises_when_the_model_cannot_be_loaded():
    with patch("adapters.inference.clip_vision._load_open_clip") as loader:
        loader.side_effect = RuntimeError("model is gone")
        with pytest.raises(InferenceError):
            _adapter().get_text_embedding_clip("un chat", "clip-ViT-B-32")
