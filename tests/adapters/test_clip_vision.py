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
    """Un `open_clip` factice au point d'import : la CI ne charge aucun poids.

    `monkeypatch.setitem` retire le stub ensuite — un faux module laissé dans
    `sys.modules` contaminerait tout le reste de la suite. `hf_hub_download` est
    endormi de la même façon : un test unitaire ne télécharge rien.
    """
    module = MagicMock()
    module.create_model_and_transforms.side_effect = lambda arch, pretrained=None: (
        MagicMock(name=f"model:{arch}"),
        None,
        MagicMock(name=f"preprocess:{arch}"),
    )
    module.get_tokenizer.side_effect = lambda arch: MagicMock(name=f"tok:{arch}")
    monkeypatch.setitem(sys.modules, "open_clip", module)

    download = MagicMock(return_value="/hf-cache/model.safetensors")
    monkeypatch.setattr("huggingface_hub.hf_hub_download", download)
    module.hf_hub_download = download  # exposé pour les assertions
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
    # Le modèle OpenCLIP se charge par ARCHITECTURE + POIDS, jamais par
    # `hf-hub:<id>` : le dépôt ne publie pas d'`open_clip_config.json`.
    fake_open_clip.create_model_and_transforms.assert_called_once_with(
        "EVA02-B-16", pretrained="/hf-cache/model.safetensors"
    )
    fake_open_clip.hf_hub_download.assert_called_once_with(
        "dudcjs2779/anime-style-tag-clip", "model.safetensors"
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
    """Un modèle OpenCLIP : c'est le tokenizer de SON architecture, et sa tour
    texte, qu'on utilise — pas un encodeur de phrases générique."""
    import torch

    adapter = _adapter()
    model = MagicMock(name="eva02")
    model.encode_text.return_value = torch.tensor([[3.0, 4.0]])
    fake_open_clip.create_model_and_transforms.side_effect = None
    fake_open_clip.create_model_and_transforms.return_value = (model, None, MagicMock())

    vector = adapter.get_text_embedding_clip(
        "cheveux roses", "dudcjs2779/anime-style-tag-clip"
    )

    # Le tokenizer est celui de l'ARCHITECTURE, pas de `hf-hub:<id>`.
    fake_open_clip.get_tokenizer.assert_called_once_with("EVA02-B-16")
    model.encode_text.assert_called_once()
    # normalisé L2 : (3,4)/5 == (0.6, 0.8)
    assert vector == pytest.approx([0.6, 0.8])


def test_the_image_transform_is_open_clips_own_preprocess(fake_open_clip):
    """Le prétraitement doit être CELUI que rend `create_model_and_transforms`.

    Un redimensionnement fait main produit des vecteurs qui ont l'air bons et
    classent mal : la panne est invisible jusqu'à ce qu'on lise les résultats.
    """
    import torch

    adapter = _adapter()
    model = MagicMock(name="eva02")
    model.encode_image.return_value = torch.tensor([[3.0, 4.0]])
    preprocess = MagicMock(name="preprocess", return_value=torch.zeros(3, 224, 224))
    fake_open_clip.create_model_and_transforms.side_effect = None
    fake_open_clip.create_model_and_transforms.return_value = (model, None, preprocess)

    adapter.get_image_embedding(PNG, model_id="dudcjs2779/anime-style-tag-clip")

    # L'image décodée passe par le transform d'open_clip, et c'est SA sortie
    # (unsqueeze -> batch de 1) qui entre dans la tour image.
    preprocess.assert_called_once()
    assert preprocess.call_args[0][0].mode == "RGB"  # une PIL.Image, pas des bytes
    model.encode_image.assert_called_once()
    assert model.encode_image.call_args[0][0].shape == (1, 3, 224, 224)


def test_an_id_absent_from_the_registry_is_not_an_open_clip_model(fake_open_clip):
    """Le routage se fait sur le REGISTRE, pas sur la présence d'un `/`.

    L'ancienne version envoyait chez `hf-hub:` tout id contenant un slash — et
    le seul modèle OpenCLIP de la branche ne s'y chargeait pas.
    """
    from adapters.inference.clip_vision import _load_open_clip

    with patch("sentence_transformers.SentenceTransformer") as st:
        st.return_value = MagicMock(name="st-instance")
        _load_open_clip("sentence-transformers/clip-ViT-L-14")

    st.assert_called_once_with("sentence-transformers/clip-ViT-L-14")
    fake_open_clip.create_model_and_transforms.assert_not_called()


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
