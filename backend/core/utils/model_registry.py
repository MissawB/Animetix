"""
Single source of truth for Hugging Face model security: pinned revision (an
immutable commit SHA) and remote-code trust policy per model.

Merges the former `model_security.py` (get_verified_revision) and
`hf_security.py` (resolve_trust_remote_code / trusted_revision). A model gets
`trust_remote_code=True` ONLY if listed here with that flag, and is then pinned
to a real 40-hex SHA so a malicious future push cannot execute code.

The former 404 ids `unsloth/DeepSeek-R1-Distill-Qwen-8B` and
`kyutai/moshi-1b-preview` have been re-pointed to the real pinnable repos
`unsloth/DeepSeek-R1-Distill-Qwen-7B` and `kyutai/moshiko-pytorch-bf16`
(both SHA-pinned), and all consumer scripts updated accordingly.
"""

import logging
import os
from typing import Optional

from core.config import get_config

logger = logging.getLogger("animetix.security.models")


class ModelSecurityError(Exception):
    pass


# model_id -> {"revision": <40-hex SHA or None>, "trust_remote_code": bool}
# Revisions fetched from HfApi().model_info(id).sha. trust_remote_code=True
# requires a real SHA (enforced by tests).
MODELS: dict[str, dict] = {
    "jinaai/jina-embeddings-v3": {
        "revision": "ab036b023d30b4d1138c4c3bfa9f0c445ab455d6",
        "trust_remote_code": True,
    },
    "Remidesbois/LightonOCR-2-1b-poneglyph-bbox": {
        "revision": "8bdf97f30cb8006d17624407a847b6766fa2374b",
        "trust_remote_code": True,
    },
    "cvssp/audioldm-s-full-v2": {
        "revision": "feeb3d14203495a4b6ac0893cbdedb2159b4819c",
        "trust_remote_code": False,
    },
    "Qwen/Qwen2-VL-7B-Instruct": {
        "revision": "eed13092ef92e448dd6875b2a00151bd3f7db0ac",
        "trust_remote_code": False,
    },
    "Qwen/Qwen3-VL-8B-Instruct": {
        "revision": "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b",
        "trust_remote_code": False,
    },
    "Qwen/Qwen3-8B": {
        "revision": "b968826d9c46dd6066d109eabc6255188de91218",
        "trust_remote_code": False,
    },
    "Qwen/Qwen3-Embedding-8B": {
        "revision": "1d8ad4ca9b3dd8059ad90a75d4983776a23d44af",
        "trust_remote_code": False,
    },
    "Qwen/Qwen3-VL-Embedding-8B": {
        "revision": "2c4565515e0f265c6511776e7193b22c0968ddc7",
        "trust_remote_code": False,
    },
    "Qwen/Qwen3.5-4B": {
        "revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
        "trust_remote_code": False,
    },
    "Qwen/Qwen3.5-9B": {
        "revision": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
        "trust_remote_code": False,
    },
    "Qwen/Qwen2.5-VL-7B-Instruct": {
        "revision": "cc594898137f460bfe9f0759e9844b3ce807cfb5",
        "trust_remote_code": False,
    },
    "black-forest-labs/FLUX.1-schnell": {
        "revision": "741f7c3ce8b383c54771c7003378a50191e9efe9",
        "trust_remote_code": False,
    },
    "HuggingFaceTB/SmolVLM-Instruct": {
        "revision": "81cd9a775a4d644f2faf4e7becff4559b46b14c7",
        "trust_remote_code": False,
    },
    "google/owlv2-base-patch16-ensemble": {
        "revision": "cfd3195ba4ea9592eec887ded089f4c08eff231d",
        "trust_remote_code": False,
    },
    "google/siglip2-so400m-patch14-384": {
        "revision": "e8e487298228002f3d8a82e0cd5c8ea9c567f57f",
        "trust_remote_code": False,
    },
    "cross-encoder/ms-marco-MiniLM-L-12-v2": {
        "revision": "7b0235231ca2674cb8ca8f022859a6eba2b1c968",
        "trust_remote_code": False,
    },
    "Qwen/Qwen3-VL-30B-A3B-Instruct": {
        "revision": "9c4b90e1e4ba969fd3b5378b57d966d725f1b86c",
        "trust_remote_code": False,
    },
    "Qwen/Qwen3-0.6B": {
        "revision": "c1899de289a04d12100db370d81485cdf75e47ca",
        "trust_remote_code": False,
    },
    "HuggingFaceTB/SmolLM-135M": {
        "revision": "1d461723eec654e65efdc40cf49301c89c0c92f4",
        "trust_remote_code": False,
    },
    "unsloth/DeepSeek-R1-Distill-Qwen-7B": {
        "revision": "d53ce546e5539236bbadf12887371481c241ce6c",
        "trust_remote_code": True,
    },
    "kyutai/moshiko-pytorch-bf16": {
        "revision": "2bfc9ae6e89079a5cc7ed2a68436010d91a3d289",
        "trust_remote_code": False,
    },
}


# --- Modèles de recherche visuelle : le nom vit dans le core ---------------
#
# Un service de domaine (`core.domain.services.visual_index`) doit pouvoir NOMMER
# le modèle qui définit un espace vectoriel sans dépendre à la compilation de
# l'adaptateur qui le charge (règle énoncée dans `core/ports/vector_store_port.py`).
# Les constantes vivent donc ici ; `adapters.inference.ccip_vision` les importe
# DEPUIS ce module et les ré-exporte pour ses propres appelants.
#
# CCIP : les poids ONNX vivent dans `deepghs/ccip_onnx`. `deepghs/ccip` est le
# dépôt de base (checkpoints torch), il ne sert aucun graphe ONNX — écrire
# `deepghs/ccip` ici, c'est nommer un modèle que personne ne charge.
CCIP_REPO_ID = "deepghs/ccip_onnx"
CCIP_MODEL_NAME = "ccip-caformer-24-randaug-pruned"
CCIP_MODEL_ID = f"{CCIP_REPO_ID}/{CCIP_MODEL_NAME}"

# CLIP EVA-02 affiné sur de l'illustration japonaise : une jaquette est un
# dessin, pas une photo. Espace joint (image + texte) -> tour texte disponible.
ANIME_CLIP_MODEL_ID = "dudcjs2779/anime-style-tag-clip"


# --- Comment on CHARGE un modèle OpenCLIP ----------------------------------
#
# Le dépôt `dudcjs2779/anime-style-tag-clip` ne contient QUE trois fichiers :
# `.gitattributes`, `README.md`, `model.safetensors`. Pas d'`open_clip_config.json`,
# pas de `config.json`, pas de tokenizer. Donc
# `open_clip.create_model_and_transforms("hf-hub:dudcjs2779/anime-style-tag-clip")`
# ÉCHOUE : le Hub met en cache un marqueur `.no_exist/open_clip_config.json` et
# open_clip n'a aucune architecture à construire. Router vers `hf-hub:` tout id
# contenant un `/`, c'était nommer un modèle que personne ne peut charger.
#
# Ce qui existe dans le dépôt, ce sont les POIDS (un fine-tune) ; l'ARCHITECTURE
# vient du config embarqué d'open_clip. La carte du modèle le dit :
# fine-tune de `timm/eva02_base_patch16_clip_224.merged2b_s8b_b131k`,
# `library_name: open_clip` -> architecture `EVA02-B-16`, 512 dimensions,
# deux tours (image + texte) dans un espace joint.
#
# La recette vit ICI, à côté du nom du modèle, et pas dans un `if` de
# l'adaptateur : « cet id » signifie « cette architecture, ces poids ». Un
# deuxième modèle OpenCLIP s'ajoute en une entrée, sans toucher au chargeur.
# Un id ABSENT de cette table n'est pas un modèle OpenCLIP : il part chez
# sentence-transformers (`clip-ViT-B-32` et consorts), qui lèvera s'il ne sait
# pas le charger — jamais de vecteur vide rendu en silence.
OPEN_CLIP_MODELS: dict[str, dict[str, str]] = {
    ANIME_CLIP_MODEL_ID: {
        # Le nom d'architecture d'open_clip, pas un dépôt du Hub.
        "architecture": "EVA02-B-16",
        # Le seul fichier de poids publié par le dépôt.
        "weights_file": "model.safetensors",
    },
}


# Versioned embedding models (logical version -> model id). Revisions resolve
# from MODELS via get_verified_revision — never duplicated here.
EMBEDDING_VERSIONS: dict[str, dict[str, str]] = {
    "text": {
        "v3": "jinaai/jina-embeddings-v3",
        "v4": "Qwen/Qwen3-Embedding-8B",
    },
    "vision": {
        "v2": "google/siglip2-so400m-patch14-384",
        "v3": "Qwen/Qwen3-VL-Embedding-8B",
    },
}


def resolve_text_embedding_version() -> str:
    """Active text-embedding version, from the ``MODEL_VERSION_TEXT`` env var.

    Defaults to ``"v3"`` (jina-embeddings-v3: 1024-d, ~1GB, CPU-loadable)
    rather than the 4096-d/10GB GPU-only ``"v4"`` (Qwen3-Embedding-8B) --
    v3 is the version the whole app agrees on. Overridable by whoever has
    the GPU budget for v4.

    The ONLY place this env var / default is read, so both the writer
    (``pipeline.models_registry.ModelsRegistry``) and the reader
    (``PGVectorRepositoryAdapter.embedding_fn`` via
    ``resolve_text_embedding_model_id``) move together.
    """
    # Read the env var live (not via get_config): under Django the ConfigPort
    # adapter reads static settings, which silently broke this documented
    # env-driven toggle (writer/reader could then diverge). See
    # tests/core/test_model_registry.py::...respects_env_override.
    return os.getenv("MODEL_VERSION_TEXT", "v3")


def resolve_text_embedding_model_id(version: Optional[str] = None) -> str:
    """Resolve the active text-embedding model id from ``EMBEDDING_VERSIONS``.

    Single source of truth for BOTH the writer (``pipeline.models_registry``,
    which vectorises the catalogue) and the reader
    (``PGVectorRepositoryAdapter.embedding_fn``, which embeds search
    queries). Before this existed the two hardcoded different models at
    different dimensions and nothing could ever match in pgvector.
    """
    version = version or resolve_text_embedding_version()
    return EMBEDDING_VERSIONS["text"][version]


def get_verified_revision(model_id: str) -> str | None:
    """Pinned SHA for a known model; STRICT mode blocks unknown models."""
    entry = MODELS.get(model_id)
    if entry and entry["revision"]:
        return entry["revision"]

    strict = get_config().get("STRICT_MODEL_VERIFICATION", False)
    msg = f"No verified signature found for model: {model_id}"
    if strict:
        logger.error(f"SECURITY ALERT: {msg}. Loading blocked.")
        raise ModelSecurityError(msg)
    logger.warning(f"SECURITY WARNING: {msg}. Loading unverified model.")
    return None


def resolve_trust_remote_code(model_id: str) -> bool:
    """True only for explicitly-allowlisted trusted models; False otherwise."""
    entry = MODELS.get(model_id)
    return bool(entry and entry["trust_remote_code"])


def trusted_revision(model_id: str) -> str | None:
    """Pinned SHA for a trusted model, else None (caller uses 'main')."""
    entry = MODELS.get(model_id)
    if entry and entry["trust_remote_code"]:
        return entry["revision"]
    return None


class ModelIntegrityVerifier:
    """Hub-side integrity guard: safetensors presence (anti-pickle/RCE).

    Moved here from ``pipeline/models_registry.py`` (Phase 2b of the model
    registry consolidation) so every security policy about model loading lives
    in this single module.
    """

    TRUSTED_AUTHORS = ["jinaai", "google", "sentence-transformers", "BAAI", "nomic-ai"]

    @staticmethod
    def verify(model_id: str, revision: Optional[str] = None) -> str:
        try:
            from huggingface_hub import model_info  # noqa: E402

            info = model_info(model_id, revision=revision)

            author = getattr(info, "author", "unknown")
            if author not in ModelIntegrityVerifier.TRUSTED_AUTHORS:
                logger.warning(
                    f"⚠️ Modèle '{model_id}' provient d'un auteur non listé comme 'Premium Trust': {author}"
                )

            has_safetensors = any(
                f.rfilename.endswith(".safetensors") for f in info.siblings
            )
            if not has_safetensors:
                logger.error(
                    f"❌ Sécurité: Le modèle {model_id} ne contient pas de fichiers .safetensors (Risque RCE via Pickle)."
                )
                if get_config().get("STRICT_MODEL_SECURITY", "true") == "true":
                    raise ValueError(f"Blocking insecure model: {model_id}")

            logger.info(f"✅ Modèle vérifié: {model_id} (Revision: {info.sha[:8]})")
            return info.sha
        except Exception as e:
            logger.error(
                f"❌ Échec de la vérification d'intégrité pour {model_id}: {e}"
            )
            if get_config().get("STRICT_MODEL_SECURITY", "true") == "true":
                raise
            return revision or "main"
