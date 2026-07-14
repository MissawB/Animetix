"""Le SEUL test qui charge vraiment les poids d'`anime-style-tag-clip`.

Il existe parce que tout le reste de la suite est simulé — et c'est précisément
ce qui a laissé passer la panne : `_load_open_clip` construisait
`open_clip.create_model_and_transforms("hf-hub:dudcjs2779/anime-style-tag-clip")`,
ce qui ne peut PAS marcher (le dépôt ne publie ni `open_clip_config.json` ni
tokenizer), et pas un seul test unitaire n'a bronché. Un mock ne vérifie que ce
qu'on a pensé à lui demander ; ici on demande au vrai modèle.

Skippé — jamais échoué — quand `open_clip` n'est pas installé ou quand les poids
ne sont pas déjà dans le cache HF local (CI). Il ne télécharge RIEN : si le
fichier n'est pas là, il passe son tour.

Volontairement PAS marqué `@pytest.mark.integration` : ce marqueur est skippé
d'office par `tests/conftest.py` dès qu'`ollama` est injoignable (il sert aux
tests qui exigent un LLM live). Ce test-ci ne dépend d'aucun service — le
skipper parce qu'ollama dort le rendrait muet exactement chez la personne qui a
les poids. On suit donc l'idiome du dépôt pour les dépendances lourdes
optionnelles : `pytest.importorskip` (cf. `test_creative_inference.py`,
`test_vertex_pipelines.py`), plus un skip sur l'absence des poids en cache.
"""

from io import BytesIO

import pytest
from core.utils.model_registry import ANIME_CLIP_MODEL_ID, OPEN_CLIP_MODELS

pytest.importorskip("open_clip", reason="open_clip_torch non installé")

from huggingface_hub import try_to_load_from_cache  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

_WEIGHTS_FILE = OPEN_CLIP_MODELS[ANIME_CLIP_MODEL_ID]["weights_file"]
_cached = try_to_load_from_cache(ANIME_CLIP_MODEL_ID, _WEIGHTS_FILE)

pytestmark = pytest.mark.skipif(
    not isinstance(_cached, str),
    reason=(
        f"poids de {ANIME_CLIP_MODEL_ID} absents du cache HF local — "
        "on ne télécharge pas depuis les tests"
    ),
)

CLIP_DIM = 512  # EVA02-B-16 : espace joint image+texte en 512 dimensions


def _adapter():
    from adapters.inference.clip_vision import ClipVisionMixin

    class _Engine(ClipVisionMixin):
        def _log_usage(self, **kwargs):
            pass

    return _Engine()


def _png(draw_fn) -> bytes:
    """Une jaquette de synthèse : un dessin, pas une photo."""
    img = Image.new("RGB", (224, 224), (250, 245, 235))
    draw_fn(ImageDraw.Draw(img))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _red_square_cover() -> bytes:
    return _png(lambda d: d.rectangle([40, 40, 184, 184], fill=(220, 30, 40)))


@pytest.fixture(scope="module")
def adapter():
    return _adapter()


def test_the_real_model_loads_and_both_towers_are_512_dimensional(adapter):
    """Les deux tours chargent et vivent dans le MÊME espace."""
    image_vector = adapter.get_image_embedding(
        _red_square_cover(), model_id=ANIME_CLIP_MODEL_ID
    )
    text_vector = adapter.get_text_embedding_clip(
        "a bright red square", ANIME_CLIP_MODEL_ID
    )

    assert len(image_vector) == CLIP_DIM
    assert len(text_vector) == CLIP_DIM
    assert all(isinstance(x, float) for x in image_vector)
    # Deux vecteurs de dimensions différentes = deux espaces : la moyenne
    # image+texte de `deep_multimodal_search` n'aurait aucun sens.
    assert len(image_vector) == len(text_vector)


def test_image_and_text_are_comparable_in_the_joint_space(adapter):
    """Le test qui compte : une phrase qui DÉCRIT l'image doit la classer devant
    une phrase qui n'a rien à voir. Des vecteurs de la bonne taille mais d'un
    prétraitement faux passeraient le test précédent et échoueraient ici."""
    cover = _red_square_cover()
    image_vector = adapter.get_image_embedding(cover, model_id=ANIME_CLIP_MODEL_ID)

    related = adapter.get_text_embedding_clip(
        "a big red square on a plain background", ANIME_CLIP_MODEL_ID
    )
    unrelated = adapter.get_text_embedding_clip(
        "a photograph of a snowy mountain range at night", ANIME_CLIP_MODEL_ID
    )

    def cosine(a, b):
        # Les deux tours rendent déjà des vecteurs normalisés L2 -> produit
        # scalaire = cosinus. On divise quand même : si un jour la
        # normalisation saute, ce test ne doit pas mentir pour autant.
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(x * x for x in b) ** 0.5
        return dot / (na * nb)

    sim_related = cosine(image_vector, related)
    sim_unrelated = cosine(image_vector, unrelated)

    assert sim_related > sim_unrelated, (
        f"la phrase liée ({sim_related:.4f}) ne classe pas devant la phrase "
        f"sans rapport ({sim_unrelated:.4f}) — espace joint cassé ou "
        f"prétraitement faux"
    )
