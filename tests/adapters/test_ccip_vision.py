"""CCIP mesure « c'est LA MÊME personne », pas « ça se ressemble ».

C'est la seule raison pour laquelle on ajoute une dépendance ONNX à l'image de
production : un CLIP généraliste répondrait « des personnages qui lui
ressemblent », ce qui a l'air d'une réponse et n'en est pas une.

On charge le graphe ONNX de `deepghs/ccip_onnx` nous-mêmes, sans `dghs-imgutils`
(qui traînait 95 Mo, dont 69 Mo d'OpenCV, pour une seule fonction). Le prix de
ce choix : le prétraitement est désormais NOTRE code, et un prétraitement
subtilement faux produit des embeddings qui ONT L'AIR bons et classent mal.
D'où ces tests : ils épinglent le tenseur (forme, dtype, plage, ordre des
canaux, moyenne/écart-type), pas seulement la plomberie.
"""

import sys
import types
from io import BytesIO
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from core.domain.exceptions import InferenceError
from PIL import Image

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
    b"\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01"
    b"\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
)

# Valeurs de référence recopiées depuis l'implémentation qui a produit les
# métriques publiées du dépôt (imgutils/metrics/ccip.py, `_normalize` et
# `_preprocess_image`). Si elles changent en amont, ces tests doivent casser.
MEAN = np.array([0.48145466, 0.4578275, 0.40821073])
STD = np.array([0.26862954, 0.26130258, 0.27577711])
SIZE = 384


def _png_bytes(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def _clear_session_cache():
    from adapters.inference import ccip_vision

    ccip_vision._SESSION_CACHE.clear()
    yield
    ccip_vision._SESSION_CACHE.clear()


@pytest.fixture
def fake_onnx(monkeypatch):
    """`onnxruntime` n'est pas installé dans le venv : on injecte un stub.

    `monkeypatch.setitem` et jamais `sys.modules[...] = ...` — un stub laissé
    dans `sys.modules` contamine tout le reste de la suite.
    """
    session = MagicMock()
    session.run.return_value = [np.full((1, 768), 0.2, dtype=np.float32)]
    module = types.SimpleNamespace(
        InferenceSession=MagicMock(return_value=session),
        get_available_providers=MagicMock(return_value=["CPUExecutionProvider"]),
    )
    monkeypatch.setitem(sys.modules, "onnxruntime", module)
    return session


def _adapter():
    from adapters.inference.ccip_vision import CcipVisionMixin

    class _Engine(CcipVisionMixin):
        def _log_usage(self, **kwargs):
            pass

    return _Engine()


# --------------------------------------------------------------------------
# Le prétraitement — la partie qui casse en silence si on la rate.
# --------------------------------------------------------------------------


def test_the_tensor_has_the_shape_and_dtype_the_onnx_graph_expects():
    from adapters.inference.ccip_vision import _preprocess_ccip_image

    # Une image volontairement ni carrée ni à la bonne taille : c'est au
    # prétraitement de la ramener à 384x384, pas à l'appelant.
    data = _preprocess_ccip_image(Image.new("RGB", (57, 113), (10, 20, 30)))

    assert data.shape == (1, 3, SIZE, SIZE)
    assert data.dtype == np.float32


def test_the_channels_are_rgb_in_chw_order_not_bgr_and_not_hwc():
    """Un rouge pur doit allumer le canal 0, pas le canal 2.

    Une transposition oubliée ou un BGR (l'erreur classique quand on vient
    d'OpenCV) passe tous les tests de forme et détruit silencieusement le
    classement.
    """
    from adapters.inference.ccip_vision import _preprocess_ccip_image

    data = _preprocess_ccip_image(Image.new("RGB", (32, 32), (255, 0, 0)))

    lit = (1.0 - MEAN) / STD  # canal à 255
    dark = (0.0 - MEAN) / STD  # canal à 0

    assert data[0, 0].mean() == pytest.approx(lit[0], abs=1e-4)
    assert data[0, 1].mean() == pytest.approx(dark[1], abs=1e-4)
    assert data[0, 2].mean() == pytest.approx(dark[2], abs=1e-4)


def test_the_scaling_and_the_mean_std_normalization_are_ccips_own():
    """Blanc pur et noir pur épinglent à la fois le /255 et la normalisation.

    Sans le /255 les valeurs partiraient à ~950 ; sans la normalisation elles
    resteraient dans [0, 1]. Les deux erreurs donnent un vecteur d'apparence
    parfaitement normale.
    """
    from adapters.inference.ccip_vision import _preprocess_ccip_image

    white = _preprocess_ccip_image(Image.new("RGB", (16, 16), (255, 255, 255)))
    black = _preprocess_ccip_image(Image.new("RGB", (16, 16), (0, 0, 0)))

    for c in range(3):
        assert white[0, c].mean() == pytest.approx((1.0 - MEAN[c]) / STD[c], abs=1e-4)
        assert black[0, c].mean() == pytest.approx((0.0 - MEAN[c]) / STD[c], abs=1e-4)


def test_every_value_lands_in_the_range_the_normalization_implies():
    from adapters.inference.ccip_vision import _preprocess_ccip_image

    rng = np.random.default_rng(0)
    noise = rng.integers(0, 256, size=(48, 48, 3), dtype=np.uint8)
    data = _preprocess_ccip_image(Image.fromarray(noise, mode="RGB"))

    for c in range(3):
        lo, hi = (0.0 - MEAN[c]) / STD[c], (1.0 - MEAN[c]) / STD[c]
        assert data[0, c].min() >= lo - 1e-4
        assert data[0, c].max() <= hi + 1e-4

    # Un tenseur resté en [0, 255] (normalisation oubliée) ne peut pas passer.
    assert data.max() < 2.5


def test_a_greyscale_or_rgba_image_is_coerced_to_three_channels():
    from adapters.inference.ccip_vision import _preprocess_ccip_image

    grey = _preprocess_ccip_image(Image.new("L", (20, 20), 128))
    rgba = _preprocess_ccip_image(Image.new("RGBA", (20, 20), (1, 2, 3, 4)))

    assert grey.shape == (1, 3, SIZE, SIZE)
    assert rgba.shape == (1, 3, SIZE, SIZE)


# --------------------------------------------------------------------------
# La plomberie — le graphe, la session, le contrat.
# --------------------------------------------------------------------------


def test_it_encodes_a_portrait_with_ccip(fake_onnx):
    with patch("adapters.inference.ccip_vision.hf_hub_download") as dl:
        dl.return_value = "C:/fake/model_feat.onnx"
        vector = _adapter().get_character_embedding(PNG)

    assert len(vector) == 768
    assert all(isinstance(v, float) for v in vector[:8])

    # Le fichier demandé au Hub est bien le graphe de features de CCIP.
    repo, filename = dl.call_args[0][0], dl.call_args[0][1]
    assert repo == "deepghs/ccip_onnx"
    assert filename.endswith("/model_feat.onnx")

    # Et le tenseur réellement passé à ONNX est celui que le graphe attend.
    fake_onnx.run.assert_called_once()
    output_names, feeds = fake_onnx.run.call_args[0]
    assert output_names == ["output"]
    tensor = feeds["input"]
    assert tensor.shape == (1, 3, SIZE, SIZE)
    assert tensor.dtype == np.float32
    assert tensor.max() < 2.5  # normalisé, pas brut


def test_the_session_is_built_once_and_reused(fake_onnx):
    import onnxruntime

    adapter = _adapter()
    with patch("adapters.inference.ccip_vision.hf_hub_download") as dl:
        dl.return_value = "C:/fake/model_feat.onnx"
        adapter.get_character_embedding(PNG)
        adapter.get_character_embedding(PNG)

    # Reconstruire la session à chaque portrait, c'est 35 000 chargements.
    assert onnxruntime.InferenceSession.call_count == 1
    assert fake_onnx.run.call_count == 2


def test_a_failure_raises_instead_of_returning_an_empty_list(fake_onnx):
    fake_onnx.run.side_effect = RuntimeError("onnx runtime is unhappy")
    with patch("adapters.inference.ccip_vision.hf_hub_download") as dl:
        dl.return_value = "C:/fake/model_feat.onnx"
        with pytest.raises(InferenceError):
            _adapter().get_character_embedding(PNG)


def test_a_model_that_cannot_be_fetched_raises(fake_onnx):
    with patch("adapters.inference.ccip_vision.hf_hub_download") as dl:
        dl.side_effect = OSError("the hub is down")
        with pytest.raises(InferenceError):
            _adapter().get_character_embedding(PNG)


def test_an_unreadable_image_raises():
    with pytest.raises(InferenceError):
        _adapter().get_character_embedding(b"not an image")


def test_a_zero_vector_is_a_failure_not_a_result(fake_onnx):
    """Le zéro silencieux est la maladie récurrente du projet.

    Un vecteur nul ne remonte pas une erreur, il remonte des voisins
    arbitraires en ayant l'air d'avoir marché.
    """
    fake_onnx.run.return_value = [np.zeros((1, 768), dtype=np.float32)]
    with patch("adapters.inference.ccip_vision.hf_hub_download") as dl:
        dl.return_value = "C:/fake/model_feat.onnx"
        with pytest.raises(InferenceError):
            _adapter().get_character_embedding(PNG)
