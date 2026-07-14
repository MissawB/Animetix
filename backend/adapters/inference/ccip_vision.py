"""CCIP — l'identité visuelle d'un personnage d'anime.

`deepghs/ccip` (Contrastive Anime Character Image Pre-training, ~240 000 images
de 3 982 personnages) répond à « est-ce le MÊME personnage ? ». Un CLIP
généraliste répond à « est-ce que ça se ressemble ? » — sur cette question, ce
n'est pas la même chose, et la deuxième réponse a l'air juste sans l'être.

On charge le graphe ONNX publié à la main, sans `dghs-imgutils` : ce paquet
apportait 95 Mo à l'image de production (dont 69 Mo d'`opencv-contrib-python`,
retiré volontairement du projet le 2026-07-11) et forçait `chardet` 7.4.3 ->
4.0.0, le tout pour une seule fonction. Seul `onnxruntime` (~17 Mo) reste.

Le prix de ce choix : le prétraitement ci-dessous est NOTRE code. Un
prétraitement subtilement faux produit des embeddings qui ONT L'AIR bons et
classent mal — exactement la panne silencieuse que ce projet existe pour tuer.
Il n'est donc pas deviné : il est repris trait pour trait de l'implémentation de
référence, celle qui a produit les métriques publiées sur le dépôt du modèle.

Source du prétraitement (lue, pas supposée) :
  https://github.com/deepghs/imgutils -> imgutils/metrics/ccip.py
  - `_preprocess_image()` appelle `load_image(img, mode='RGB',
    force_background='white')` -- un canal alpha est COMPOSITÉ SUR FOND BLANC
    avant la conversion RGB, jamais juste jeté. Un bare `.convert("RGB")`
    laisse les pixels transparents à leur valeur RGB sous-jacente (souvent
    noir sur un PNG détouré) : même forme de tenseur, valeurs différentes,
    embedding qui n'est plus celui que les métriques publiées mesurent. Puis
    `resize((384, 384), resample=Image.BILINEAR)`,
    `np.array(img).transpose(2, 0, 1).astype(np.float32) / 255.0`, puis
    `_normalize()`.
  - `_normalize()` : mean = (0.48145466, 0.4578275, 0.40821073),
    std = (0.26862954, 0.26130258, 0.27577711)  (les constantes de CLIP).
  - `ccip_batch_extract_features()` : `session.run(['output'], {'input': data})`
    sur un batch (N, 3, 384, 384) float32 -> sortie (N, 768) float32.
  - `_open_feat_model()` : `hf_hub_download('deepghs/ccip_onnx',
    f'{model}/model_feat.onnx')`, modèle par défaut
    `ccip-caformer-24-randaug-pruned`.

Le dépôt `deepghs/ccip_onnx` ne publie PAS de `preprocess.json` : le code de
référence ci-dessus est la seule spécification qui existe (vérifié en listant
les fichiers du dépôt via l'API du Hub — il n'y a que les graphes, `metrics.json`
et `cluster.json`).
"""

from io import BytesIO
from typing import TYPE_CHECKING, Any, List

import numpy as np
from core.domain.exceptions import InferenceError

# Le NOM du modèle vit dans le core (`core.utils.model_registry`) : un service de
# domaine doit pouvoir nommer l'espace vectoriel qu'il interroge sans dépendre de
# cet adaptateur. On le ré-exporte ici pour les appelants historiques — une seule
# valeur, deux chemins d'import, jamais deux définitions.
from core.utils.model_registry import (  # noqa: F401  (ré-export)
    CCIP_MODEL_ID,
    CCIP_MODEL_NAME,
    CCIP_REPO_ID,
)
from huggingface_hub import hf_hub_download
from PIL import Image

CCIP_IMAGE_SIZE = 384
CCIP_MEAN = (0.48145466, 0.4578275, 0.40821073)
CCIP_STD = (0.26862954, 0.26130258, 0.27577711)

_SESSION_CACHE: dict = {}


def _flatten_onto_white(img: Image.Image) -> Image.Image:
    """`load_image(img, mode='RGB', force_background='white')` -- reproduit
    trait pour trait le comportement de la référence deepghs sur un canal
    alpha : composité sur un fond BLANC, jamais simplement jeté.

    Un `.convert("RGB")` nu retire l'alpha et laisse les pixels transparents
    à leur valeur RGB sous-jacente, souvent noir sur un PNG détouré. Les
    portraits de personnages détourés (fond transparent) sont courants ; sans
    ce compositing, ils partaient avec un fond NOIR au lieu du fond BLANC que
    la référence produit -- un embedding différent de celui que les
    métriques publiées mesurent, silencieusement.
    """
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        # Le canal alpha lui-même sert de masque de compositing : opaque garde
        # le pixel d'origine, transparent laisse le blanc, entre les deux mêle
        # les deux -- exactement ce que fait un compositing alpha standard.
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    return img.convert("RGB")


def _preprocess_ccip_image(img: Image.Image) -> np.ndarray:
    """Image PIL -> tenseur (1, 3, 384, 384) float32, prêt pour le graphe.

    Chaque étape est celle de la référence, dans cet ordre — voir l'en-tête du
    module. Toute divergence ici est invisible à l'œil et fatale au classement.
    """
    img = _flatten_onto_white(img)
    img = img.resize((CCIP_IMAGE_SIZE, CCIP_IMAGE_SIZE), resample=Image.BILINEAR)

    data = np.array(img).transpose(2, 0, 1).astype(np.float32) / 255.0

    mean = np.asarray(CCIP_MEAN, dtype=np.float32)
    std = np.asarray(CCIP_STD, dtype=np.float32)
    data = (data - mean[:, None, None]) / std[:, None, None]

    return data[None, ...].astype(np.float32)


def _load_ccip_session(model_name: str = CCIP_MODEL_NAME) -> Any:
    """Télécharge (une fois, puis cache HF) et ouvre le graphe de features.

    La session est mémorisée par nom de modèle : reconstruire une
    `InferenceSession` par portrait, ce serait 35 000 chargements de graphe.
    """
    if model_name in _SESSION_CACHE:
        return _SESSION_CACHE[model_name]

    # Import ONNX dans le corps de la fonction : tant que personne ne cherche
    # un personnage, la dépendance ne coûte rien à l'import du module.
    import onnxruntime  # noqa: E402

    path = hf_hub_download(CCIP_REPO_ID, f"{model_name}/model_feat.onnx")
    session = onnxruntime.InferenceSession(path, providers=["CPUExecutionProvider"])

    _SESSION_CACHE[model_name] = session
    return session


def _ccip_extract_feature(img: Image.Image) -> List[float]:
    """Le seul appel au graphe. Isolé pour rester moquable."""
    data = _preprocess_ccip_image(img)
    session = _load_ccip_session()
    (output,) = session.run(["output"], {"input": data})
    return [float(v) for v in np.asarray(output)[0]]


class CcipVisionMixin:
    if TYPE_CHECKING:
        # Fourni par l'adaptateur qui compose ce mixin (comme pour ClipVisionMixin).
        def _log_usage(
            self,
            engine: str,
            input_tokens: int = 0,
            output_tokens: int = 0,
            units: int = 0,
            allocated_budget: int = 0,
        ) -> None: ...

    def get_character_embedding(self, image_data: bytes) -> List[float]:
        try:
            img = Image.open(BytesIO(image_data))
            vector = _ccip_extract_feature(img)
        except Exception as e:
            # Jamais `[]` : un vecteur vide devient une recherche qui rend
            # n'importe quoi en ayant l'air d'avoir marché.
            raise InferenceError(f"CCIP embedding failed: {e}") from e

        if not vector or not np.any(np.asarray(vector)):
            # Le zéro silencieux : même maladie, autre déguisement. Un vecteur
            # nul ne remonte pas d'erreur, il remonte des voisins arbitraires.
            raise InferenceError(
                "CCIP returned a zero vector -- refusing to index a result "
                "that would rank arbitrarily."
            )

        self._log_usage(engine=f"ccip:{CCIP_MODEL_ID}:embedding", units=1)
        return vector
