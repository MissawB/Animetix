# Étage SLM pour la modération — plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** faire exécuter la modération d'entrée et de sortie du chat par un modèle 1,5B servi par le brain, au lieu de deux appels au 7B dont un précédé d'un appel mort.

**Architecture:** le brain accepte un `model` optionnel sur `/generate` et `/moderate`, restreint aux tags réellement registrés auprès d'Ollama, et garde un cache d'engines par modèle. Côté web, un `BrainAPIAdapter` épinglé sur le petit tag devient à la fois le `safety_engine` du guardrail et son `moderation_engine`. Les prompts de modération ne bougent pas : seul le moteur qui les exécute change.

**Tech Stack:** FastAPI + Pydantic (brain), `dependency_injector` (conteneurs web), Ollama 0.5.13 (GGUF Q4_K_M), pytest.

## Global Constraints

- **Ollama est épinglé en 0.5.13** (`deploy/Dockerfile.brain:146`) parce que Cloud Run fournit le driver NVIDIA 535 : tout tag ajouté doit être servable par ce build. La famille `qwen2.5` l'est déjà (le contrôle `qwen2.5:7b-instruct` est baké).
- **Le conteneur web a 4 GiB et n'a pas le droit de charger des poids en process** (`backend/core/utils/local_models.py` n'y est utilisé que pour nommer des rôles ; cf. `core/utils/inference_config.py:56-72`). Aucune tâche de ce plan ne charge un modèle côté web.
- **La CI ne reconstruit jamais l'image brain**, seulement le web. Toute tâche qui touche `deploy/Dockerfile.brain` n'a d'effet en production qu'après un rebuild (~90 min) et un déploiement manuel.
- **Le tag servi a une seule source de vérité** : les rôles de `backend/core/utils/local_models.py`. Ne jamais écrire un tag de modèle en dur ailleurs — `tests/security/test_no_hardcoded_local_model.py` le refuse, et `tests/deploy/test_brain_model_tag_is_baked.py` vérifie que le tag est réellement baké.
- **Formatage** : `black` et `ruff` sont les gardes de la CI, et les hooks pre-commit les exécutent. `black` et `mypy` ne tournent pas dans le venv local (conflit `pathspec`) : se fier aux hooks au commit, pas à une exécution manuelle.
- **Lancer les tests** avec le python du venv principal : `.venv\Scripts\python.exe -m pytest ...` depuis la racine du worktree.

---

## Structure des fichiers

| Fichier | Responsabilité | Tâche |
| --- | --- | --- |
| `backend/core/utils/local_models.py` | déclare le rôle logique `GUARDRAIL_OLLAMA_MODEL` | 1 |
| `deploy/Dockerfile.brain` | bake et préchauffe le tag du modérateur | 1 |
| `tests/deploy/test_brain_model_tag_is_baked.py` | interdit un rôle pointant sur un tag non baké | 1 |
| `backend/adapters/inference/brain_service.py` | sélection de modèle par requête, allowlist, cache d'engines | 2 |
| `tests/adapters/test_brain_service_model_selection.py` | couvre la sélection, le rejet et le cache | 2 |
| `backend/adapters/inference/brain_api_adapter.py` | transmet le modèle épinglé au brain | 3 |
| `tests/adapters/test_brain_api_adapter_extra.py` | couvre la transmission du modèle | 3 |
| `backend/api/animetix/containers/inference.py` | fournit `brain_guardrail_adapter`, recâble le `safety_engine` | 4 |
| `backend/api/animetix/containers/agentic.py` | injecte le `moderation_engine` | 5 |
| `backend/core/domain/services/guardrail_service.py` | exécute les prompts de modération sur le moteur dédié, avec repli | 5 |
| `tests/core/test_guardrail_moderation_engine.py` | couvre le moteur dédié et son repli | 5 |

---

### Task 1: Le rôle guardrail, son tag baké et son garde-fou

**Files:**
- Modify: `backend/core/utils/local_models.py:26-28`
- Modify: `deploy/Dockerfile.brain:151-193` (bake) et `:223` (préchauffage)
- Test: `tests/deploy/test_brain_model_tag_is_baked.py`

**Interfaces:**
- Consumes: rien.
- Produces: `core.utils.local_models.GUARDRAIL_OLLAMA_MODEL: str` (défaut `"qwen2.5:1.5b-instruct"`, surchargeable par `GUARDRAIL_MODEL_NAME`) ; l'ARG Docker `GUARDRAIL_MODEL` avec la même valeur par défaut.

- [ ] **Step 1: Étendre le garde-fou au nouveau rôle (test qui échoue)**

Dans `tests/deploy/test_brain_model_tag_is_baked.py`, ajouter `GUARDRAIL_MODEL` à la liste des ARG bakés et ajouter ce test :

```python
def test_guardrail_role_default_tag_is_baked():
    match = re.search(
        r'GUARDRAIL_OLLAMA_MODEL = os\.getenv\(\s*"GUARDRAIL_MODEL_NAME",\s*"(?P<tag>[^"]+)"',
        LOCAL_MODELS.read_text(encoding="utf-8"),
    )
    assert match, "GUARDRAIL_OLLAMA_MODEL is not declared in local_models.py"
    default = match.group("tag")
    assert default in _baked_tags(), (
        f"local_models.GUARDRAIL_OLLAMA_MODEL defaults to {default!r}, which "
        f"Dockerfile.brain does not bake (baked: {sorted(_baked_tags())})."
    )
```

Modifier aussi la constante existante :

```python
BAKED_ARGS = ("OLLAMA_MODEL", "CONTROL_MODEL", "GUARDRAIL_MODEL")
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `.venv\Scripts\python.exe -m pytest tests/deploy/test_brain_model_tag_is_baked.py -v`
Expected: FAIL — `AssertionError: ARG GUARDRAIL_MODEL vanished from Dockerfile.brain` (l'ARG n'existe pas encore).

- [ ] **Step 3: Déclarer le rôle**

Dans `backend/core/utils/local_models.py`, juste après `LLM_OLLAMA_MODEL` :

```python
# Modérateur du guardrail. Un rôle SÉPARÉ de LLM_OLLAMA_MODEL : la modération est
# une classification à sortie courte, pas de la synthèse, et la faire tourner sur
# le 7B coûtait deux appels au gros modèle par tour de chat. Doit nommer un tag que
# l'image brain registre (cf. tests/deploy/test_brain_model_tag_is_baked.py).
GUARDRAIL_OLLAMA_MODEL = os.getenv("GUARDRAIL_MODEL_NAME", "qwen2.5:1.5b-instruct")
```

- [ ] **Step 4: Baker le tag dans l'image brain**

Dans `deploy/Dockerfile.brain`, après le bloc `ARG CONTROL_MODEL` :

```dockerfile
# Modérateur du guardrail : une classification à sortie courte n'a pas besoin du 7B,
# et l'y faire tourner mettait deux appels au gros modèle sur le chemin critique du
# chat. Même famille et même registre que le contrôle, donc servable par l'Ollama
# 0.5.13 épinglé plus haut.
ARG GUARDRAIL_MODEL=qwen2.5:1.5b-instruct
ENV GUARDRAIL_MODEL=${GUARDRAIL_MODEL}
```

Puis, dans le `RUN` qui crée le modèle, ajouter le pull juste après celui du contrôle :

```dockerfile
    && ollama pull "$CONTROL_MODEL" \
    && ollama pull "$GUARDRAIL_MODEL" \
```

- [ ] **Step 5: Préchauffer le modérateur au démarrage**

Sans ça, la première modération après un réveil paie le chargement du modèle et le problème est déplacé, pas résolu. Dans le `CMD`, après la boucle de chauffe existante de `$OLLAMA_MODEL`, ajouter la même pour `$GUARDRAIL_MODEL` :

```sh
echo 'warming up $GUARDRAIL_MODEL...'; curl -s -X POST http://127.0.0.1:11434/api/generate -d "{\"model\":\"$GUARDRAIL_MODEL\",\"prompt\":\"hi\",\"stream\":false,\"options\":{\"num_predict\":1}}" >/dev/null;
```

- [ ] **Step 6: Supprimer l'assertion dupliquée**

`tests/deploy/test_brain_image_serves_a_model.py::test_the_model_the_code_asks_for_is_actually_in_the_image` couvre déjà « `LLM_OLLAMA_MODEL` est un tag baké ». Le `test_local_models_default_tag_is_baked` de `test_brain_model_tag_is_baked.py` le refait : le supprimer, et laisser dans ce fichier ce qui n'est couvert nulle part ailleurs — le manifeste `deployments.yaml` et le rôle guardrail. Compléter le docstring du module pour renvoyer à l'autre fichier.

- [ ] **Step 7: Lancer les tests pour vérifier qu'ils passent**

Run: `.venv\Scripts\python.exe -m pytest tests/deploy tests/core/test_local_models.py tests/security/test_no_hardcoded_local_model.py -v`
Expected: PASS (tous), et `test_the_model_the_code_asks_for_is_actually_in_the_image` reste vert — la couverture n'a pas disparu, elle a cessé d'être double.

- [ ] **Step 7: Commit**

```bash
git add backend/core/utils/local_models.py deploy/Dockerfile.brain tests/deploy/test_brain_model_tag_is_baked.py
git commit -m "feat(brain): bake a 1.5B moderator alongside the main model"
```

---

### Task 2: Sélection de modèle par requête sur le brain

**Files:**
- Modify: `backend/adapters/inference/brain_service.py:66-71` (engines), `:115-121` (`GenerateRequest`), `:235-237` (`ModerateRequest`), `:270-296` (`/generate`), `:504-508` (`/moderate`)
- Test: `tests/adapters/test_brain_service_model_selection.py` (créer)

**Interfaces:**
- Consumes: `GUARDRAIL_OLLAMA_MODEL` (Task 1) — seulement comme valeur possible du champ, le brain ne l'importe pas.
- Produces: `brain_service.engine_for(model: Optional[str]) -> UnifiedInferenceAdapter`, qui lève `HTTPException(400)` sur un tag non registré ; `GenerateRequest.model: Optional[str]` et `ModerateRequest.model: Optional[str]`.

- [ ] **Step 1: Écrire les tests qui échouent**

Créer `tests/adapters/test_brain_service_model_selection.py` :

```python
"""Le brain sert le modèle demandé, et seulement s'il le sert vraiment.

Un client qui choisit un modèle arbitraire pourrait faire télécharger n'importe
quoi à un service GPU ; un tag non registré, lui, part en 404 Ollama que rien ne
distingue d'une panne. Les deux se règlent en n'acceptant que les tags présents
dans /api/tags.
"""

import os
from unittest.mock import patch

import pytest
from fastapi import HTTPException

# brain_service.py appelle sys.exit(1) à l'import si BRAIN_API_KEY manque.
# `setdefault` n'écrase pas une vraie clé venue de l'environnement / des secrets CI.
# (Même préambule que tests/adapters/test_brain_service_routes.py.)
os.environ.setdefault("BRAIN_API_KEY", "test-env-key-12345")

import adapters.inference.brain_service as bs  # noqa: E402


@pytest.fixture
def svc():
    # Le cache et le registre d'engines sont des états de module : les remettre à
    # zéro entre les tests, sinon l'ordre d'exécution décide du résultat.
    bs._served_models_cache = None
    bs._engines = {bs.model_name: bs.brain_engine}
    return bs


def _health(models):
    return {"status": "online", "engine": "Ollama/Unified", "models": models}


def test_engine_for_none_returns_the_default_engine(svc):
    assert svc.engine_for(None) is svc.brain_engine


def test_engine_for_the_configured_model_returns_the_default_engine(svc):
    assert svc.engine_for(svc.model_name) is svc.brain_engine


def test_engine_for_a_served_model_builds_and_caches_one_engine(svc):
    with patch.object(
        svc.brain_engine,
        "health_check",
        return_value=_health([{"name": svc.model_name}, {"name": "small:1.5b"}]),
    ):
        first = svc.engine_for("small:1.5b")
        second = svc.engine_for("small:1.5b")
    assert first.model_name == "small:1.5b"
    assert first is second  # cached, not rebuilt per request


def test_engine_for_an_unserved_model_is_rejected_with_400(svc):
    with patch.object(
        svc.brain_engine,
        "health_check",
        return_value=_health([{"name": svc.model_name}]),
    ):
        with pytest.raises(HTTPException) as exc:
            svc.engine_for("not-baked:9b")
    assert exc.value.status_code == 400
    assert "not-baked:9b" in str(exc.value.detail)


def test_an_unreadable_model_list_is_not_cached(svc):
    # Ollama not up yet at first call: the empty answer must not poison the cache
    # for the life of the process.
    with patch.object(svc.brain_engine, "health_check", return_value=_health([])):
        with pytest.raises(HTTPException):
            svc.engine_for("small:1.5b")
    with patch.object(
        svc.brain_engine,
        "health_check",
        return_value=_health([{"name": "small:1.5b"}]),
    ):
        assert svc.engine_for("small:1.5b").model_name == "small:1.5b"
```

- [ ] **Step 2: Lancer les tests pour vérifier qu'ils échouent**

Run: `.venv\Scripts\python.exe -m pytest tests/adapters/test_brain_service_model_selection.py -v`
Expected: FAIL — `AttributeError: module 'adapters.inference.brain_service' has no attribute 'engine_for'`.

- [ ] **Step 3: Implémenter la sélection et le cache**

Dans `backend/adapters/inference/brain_service.py`, remplacer le bloc de construction de l'engine (actuellement trois lignes, `api_base` / `model_name` / `brain_engine`) par :

```python
# Configuration des moteurs d'inférence
api_base = os.getenv("LLM_API_BASE", "http://localhost:11434/v1")
model_name = LLM_OLLAMA_MODEL

# Initialisation de l'unité de calcul locale (Unified avec GPU)
brain_engine = UnifiedInferenceAdapter(api_base=api_base, model_name=model_name)

# Un engine par modèle servi, construit à la demande et conservé. Les modèles sont
# bakés dans l'image, donc la liste ne bouge pas de la vie du process.
_engines: dict[str, UnifiedInferenceAdapter] = {model_name: brain_engine}
_served_models_cache: Optional[set[str]] = None


def _served_models() -> set[str]:
    """Tags réellement registrés auprès d'Ollama, d'après la sonde /api/tags.

    Un résultat vide n'est PAS mis en cache : au tout début du démarrage Ollama
    peut ne pas encore répondre, et figer un ensemble vide condamnerait toute
    sélection de modèle pour la vie du process.
    """
    global _served_models_cache
    if _served_models_cache:
        return _served_models_cache
    probe = brain_engine.health_check()
    served = {
        m.get("name") for m in probe.get("models", []) if isinstance(m, dict)
    } - {None}
    if served:
        _served_models_cache = served
    return served


def engine_for(model: Optional[str]) -> UnifiedInferenceAdapter:
    """Engine servant `model`, ou l'engine par défaut si `model` est absent.

    Un client ne choisit pas un tag arbitraire : un tag inconnu part en 404 côté
    Ollama, que rien en aval ne distingue d'une panne du service. On le refuse
    explicitement, en 400.
    """
    if not model or model == model_name:
        return brain_engine
    if model not in _engines:
        if model not in _served_models():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model '{model}' is not served by this brain.",
            )
        _engines[model] = UnifiedInferenceAdapter(api_base=api_base, model_name=model)
    return _engines[model]
```

- [ ] **Step 4: Ouvrir le champ sur les deux requêtes**

Dans `GenerateRequest`, ajouter en dernier champ :

```python
    model: Optional[str] = None
```

Dans `ModerateRequest`, de même :

```python
    model: Optional[str] = None
```

Puis brancher les deux endpoints. Dans `/generate`, remplacer `brain_engine.generate(` par `engine_for(req.model).generate(`. Dans `/moderate`, remplacer la ligne d'appel par :

```python
    res = engine_for(req.model).moderate_content(req.text, req.categories or [])
```

Les deux endpoints comptent : `_llm_moderate` passe par `/generate` avec son prompt taillé, le `safety_engine` passe par `/moderate`. N'en équiper qu'un laisserait la moitié de la modération sur le 7B.

- [ ] **Step 5: Lancer les tests pour vérifier qu'ils passent**

Run: `.venv\Scripts\python.exe -m pytest tests/adapters/test_brain_service_model_selection.py -v`
Expected: PASS (5 tests).

- [ ] **Step 6: Vérifier la non-régression du service**

Run: `.venv\Scripts\python.exe -m pytest tests/adapters -q`
Expected: PASS — aucun test existant du brain ne casse (les appels sans `model` doivent continuer à passer par `brain_engine`).

- [ ] **Step 7: Commit**

```bash
git add backend/adapters/inference/brain_service.py tests/adapters/test_brain_service_model_selection.py
git commit -m "feat(brain): serve a per-request model, restricted to baked tags"
```

---

### Task 3: Le client web transmet le modèle épinglé

**Files:**
- Modify: `backend/adapters/inference/brain_api_adapter.py:27-38` (ctor), `:56-63` (payload de `generate`), `:644-655` (`moderate_content`)
- Test: `tests/adapters/test_brain_api_adapter_extra.py`

**Interfaces:**
- Consumes: `GenerateRequest.model` / `ModerateRequest.model` (Task 2).
- Produces: `BrainAPIAdapter(api_url=..., api_key=..., usage_port=..., model: Optional[str] = None)` ; l'attribut `self.model`.

- [ ] **Step 1: Écrire les tests qui échouent**

Ajouter à `tests/adapters/test_brain_api_adapter_extra.py`, dans la section des tests de `generate` :

```python
def test_generate_pins_the_configured_model_in_the_payload():
    a = BrainAPIAdapter(api_url="http://brain:5000", api_key="k", model="small:1.5b")
    with patch("adapters.inference.brain_api_adapter.safe_http_request") as req:
        req.return_value = MagicMock(json=MagicMock(return_value={"text": "ok"}))
        a.generate("Q")
    assert req.call_args.kwargs["json"]["model"] == "small:1.5b"


def test_generate_omits_the_model_when_none_is_pinned(adapter):
    with patch("adapters.inference.brain_api_adapter.safe_http_request") as req:
        req.return_value = MagicMock(json=MagicMock(return_value={"text": "ok"}))
        adapter.generate("Q")
    assert "model" not in req.call_args.kwargs["json"]


def test_moderate_content_pins_the_configured_model():
    a = BrainAPIAdapter(api_url="http://brain:5000", api_key="k", model="small:1.5b")
    with patch("adapters.inference.brain_api_adapter.safe_http_request") as req:
        req.return_value = MagicMock(
            json=MagicMock(return_value={"moderation": {"is_safe": True}})
        )
        out = a.moderate_content("texte", ["HATE_SPEECH"])
    assert req.call_args.kwargs["json"]["model"] == "small:1.5b"
    assert out == {"is_safe": True}
```

- [ ] **Step 2: Lancer les tests pour vérifier qu'ils échouent**

Run: `.venv\Scripts\python.exe -m pytest tests/adapters/test_brain_api_adapter_extra.py -k "pins_the_configured or omits_the_model" -v`
Expected: FAIL — `TypeError: __init__() got an unexpected keyword argument 'model'`.

- [ ] **Step 3: Ajouter le paramètre au constructeur**

Dans `BrainAPIAdapter.__init__`, ajouter le paramètre et l'attribut :

```python
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        usage_port: Optional[UsagePort] = None,
        model: Optional[str] = None,
    ):
        super().__init__(usage_port=usage_port)
        self.api_url = api_url or os.getenv("BRAIN_API_URL")
        config_error = check_brain_config(self.api_url)
        if config_error:
            raise ConfigurationError(config_error)
        self.api_key = api_key or os.getenv("BRAIN_API_KEY")
        # Tag servi par le brain pour CET adaptateur. None = le modèle par défaut du
        # brain. Permet d'épingler un rôle (modération) sur un modèle plus petit sans
        # dupliquer l'adaptateur ni router côté serveur.
        self.model = model
```

- [ ] **Step 4: Transmettre le modèle dans les deux payloads**

Dans `generate`, juste après la construction du `payload` (et avant le `try`) :

```python
        if self.model and "model" not in payload:
            payload["model"] = self.model
```

Dans `moderate_content`, remplacer le corps de la requête par :

```python
            body: Dict[str, Any] = {"text": text, "categories": categories}
            if self.model:
                body["model"] = self.model
            response = safe_http_request(
                "POST",
                f"{self.api_url}/moderate",
                json=body,
                headers=self._get_headers(),
            )
```

- [ ] **Step 5: Lancer les tests pour vérifier qu'ils passent**

Run: `.venv\Scripts\python.exe -m pytest tests/adapters/test_brain_api_adapter_extra.py -v`
Expected: PASS (toute la classe, anciens tests compris).

- [ ] **Step 6: Commit**

```bash
git add backend/adapters/inference/brain_api_adapter.py tests/adapters/test_brain_api_adapter_extra.py
git commit -m "feat(inference): let BrainAPIAdapter pin the model it asks the brain for"
```

---

### Task 4: Rebrancher le `safety_engine` sur le brain

C'est la tâche qui répare le bug : le premier étage de modération tape aujourd'hui `localhost:11434` depuis un conteneur web où rien n'écoute.

**Files:**
- Modify: `backend/api/animetix/containers/inference.py:9-14` (import), `:97-108` (providers)
- Test: `tests/adapters/test_inference_container_wiring.py` (créer)

**Interfaces:**
- Consumes: `BrainAPIAdapter(model=...)` (Task 3), `GUARDRAIL_OLLAMA_MODEL` (Task 1).
- Produces: le provider `InferenceContainer.brain_guardrail_adapter`.

- [ ] **Step 1: Écrire le test qui échoue**

Créer `tests/adapters/test_inference_container_wiring.py` :

```python
"""Le safety_engine du guardrail doit parler à un backend qui existe.

Il était câblé sur l'UnifiedInferenceAdapter, qui pointe sur localhost:11434 --
adresse où rien n'écoute dans le conteneur web (ni LLM_API_BASE ni LLM_MODEL_NAME
n'y sont définis). Chaque modération payait donc un appel voué à l'échec avant de
retomber sur le gros modèle.
"""

import re
from pathlib import Path

CONTAINER = (
    Path(__file__).resolve().parents[2]
    / "backend"
    / "api"
    / "animetix"
    / "containers"
    / "inference.py"
)


def _provider_block(name: str) -> str:
    source = CONTAINER.read_text(encoding="utf-8")
    match = re.search(rf"^    {name} = providers\.Singleton\((.*?)^    \)", source, re.M | re.S)
    assert match, f"provider {name} not found in inference.py"
    return match.group(1)


def test_local_guardrail_is_wired_to_the_brain_not_to_localhost():
    block = _provider_block("local_guardrail_adapter")
    assert "brain_guardrail_adapter" in block
    assert "unified_inference_adapter" not in block


def test_brain_guardrail_adapter_is_pinned_to_the_guardrail_role():
    block = _provider_block("brain_guardrail_adapter")
    assert "GUARDRAIL_OLLAMA_MODEL" in block
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `.venv\Scripts\python.exe -m pytest tests/adapters/test_inference_container_wiring.py -v`
Expected: FAIL — `assert "brain_guardrail_adapter" in block` (le provider n'existe pas et le câblage pointe encore sur `unified_inference_adapter`).

- [ ] **Step 3: Importer le rôle**

Dans `backend/api/animetix/containers/inference.py`, ajouter à l'import existant depuis `core.utils.local_models` (ordre alphabétique, `ruff` l'impose) :

```python
from core.utils.local_models import (
    COMPACT_REASONING_MODEL,
    GUARDRAIL_OLLAMA_MODEL,
    LLM_OLLAMA_MODEL,
    LOCAL_DIFFUSION_MODEL_ID,
    LOCAL_TEXT_MODEL,
)
```

- [ ] **Step 4: Déclarer le provider et recâbler**

Remplacer le bloc `local_guardrail_adapter` par ces deux providers, **dans cet ordre** (`dependency_injector` résout par nom à la définition de la classe, donc le nouveau provider doit précéder son consommateur) :

```python
    # Le même adaptateur brain que celui de la chaîne, épinglé sur le modérateur.
    # Séparé de `brain_api_adapter` pour que la modération n'occupe pas le 7B.
    brain_guardrail_adapter = providers.Singleton(
        LazyClass("adapters.inference.brain_api_adapter", "BrainAPIAdapter"),
        api_url=os.getenv("BRAIN_API_URL", ""),
        api_key=settings.BRAIN_API_KEY,
        model=GUARDRAIL_OLLAMA_MODEL,
    )

    local_guardrail_adapter = providers.Singleton(
        LazyClass(
            "adapters.inference.local_guardrail_adapter", "LocalGuardrailAdapter"
        ),
        inference_engine=brain_guardrail_adapter,
    )
```

- [ ] **Step 5: Lancer les tests pour vérifier qu'ils passent**

Run: `.venv\Scripts\python.exe -m pytest tests/adapters/test_inference_container_wiring.py tests/core/test_inference_adapters.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/api/animetix/containers/inference.py tests/adapters/test_inference_container_wiring.py
git commit -m "fix(guardrail): point the safety engine at the brain, not at a dead localhost"
```

---

### Task 5: Exécuter les prompts de modération sur le moteur dédié

**Files:**
- Modify: `backend/core/domain/services/guardrail_service.py:33-52` (ctor), `:335-352` (`_llm_moderate`)
- Modify: `backend/api/animetix/containers/agentic.py:259-266`
- Test: `tests/core/test_guardrail_moderation_engine.py` (créer)

**Interfaces:**
- Consumes: le provider `brain_guardrail_adapter` (Task 4).
- Produces: `GuardrailService(..., moderation_engine: Optional[InferencePort] = None)` ; l'attribut `self.moderation_engine`, qui vaut `inference_engine` quand rien n'est fourni.

- [ ] **Step 1: Écrire les tests qui échouent**

Créer `tests/core/test_guardrail_moderation_engine.py` :

```python
"""La modération tourne sur son propre moteur, avec repli sur le principal.

Le prompt taillé (`output_moderator`) ne bouge pas : seul le moteur qui l'exécute
change. Et si le petit modèle manque -- typiquement quand le web est déployé mais
que l'image brain n'a pas été reconstruite -- on retombe sur le moteur principal,
jamais en fail-open silencieux.
"""

import json
from unittest.mock import MagicMock

from core.domain.services.guardrail_service import GuardrailService


def _engine(text):
    engine = MagicMock()
    engine.generate.return_value = MagicMock(text=text)
    return engine


SAFE = json.dumps({"is_safe": True, "detected_categories": [], "reasoning": "ok"})


def test_moderation_defaults_to_the_main_engine():
    main = _engine(SAFE)
    svc = GuardrailService(inference_engine=main)
    svc._llm_moderate("texte", ["SPOILER"])
    main.generate.assert_called_once()


def test_moderation_uses_the_dedicated_engine_when_provided():
    main, moderator = _engine(SAFE), _engine(SAFE)
    svc = GuardrailService(inference_engine=main, moderation_engine=moderator)
    result = svc._llm_moderate("texte", ["SPOILER"])
    moderator.generate.assert_called_once()
    main.generate.assert_not_called()
    assert result["is_safe"] is True


def test_moderation_falls_back_to_the_main_engine_when_the_moderator_fails():
    main = _engine(SAFE)
    moderator = MagicMock()
    moderator.generate.side_effect = RuntimeError("model not served")
    svc = GuardrailService(inference_engine=main, moderation_engine=moderator)
    result = svc._llm_moderate("texte", ["SPOILER"])
    main.generate.assert_called_once()
    assert result["is_safe"] is True
```

- [ ] **Step 2: Lancer les tests pour vérifier qu'ils échouent**

Run: `.venv\Scripts\python.exe -m pytest tests/core/test_guardrail_moderation_engine.py -v`
Expected: FAIL — `TypeError: __init__() got an unexpected keyword argument 'moderation_engine'`.

- [ ] **Step 3: Ajouter le moteur dédié au constructeur**

Dans `GuardrailService.__init__`, ajouter le paramètre en dernier et l'attribut après `self.safety_engine` :

```python
        moderation_engine: Optional[InferencePort] = None,
```

```python
        # Moteur qui EXÉCUTE les prompts de modération. Séparé du moteur de synthèse :
        # une classification à sortie courte n'a pas besoin du 7B, et l'y faire tourner
        # mettait deux appels au gros modèle sur le chemin critique du chat. Par défaut
        # le moteur principal, donc rien ne change là où il n'est pas fourni.
        self.moderation_engine = moderation_engine or inference_engine
```

- [ ] **Step 4: Exécuter le prompt sur ce moteur, avec repli**

Dans `_llm_moderate`, remplacer la ligne d'appel :

```python
            inference_res = self.inference_engine.generate(prompt, system_prompt=system)
```

par :

```python
            try:
                inference_res = self.moderation_engine.generate(
                    prompt, system_prompt=system
                )
            except Exception as moderation_error:
                # Le petit modèle peut manquer là où le principal répond : le web se
                # déploie sans l'image brain, donc un tag de modération pas encore
                # baké renvoie 400. On dégrade en lenteur, jamais en absence de
                # contrôle.
                if self.moderation_engine is self.inference_engine:
                    raise
                logger.warning(
                    "⚠️ [Guardrail] Moderation engine failed (%s); falling back to the "
                    "main inference engine.",
                    moderation_error,
                )
                inference_res = self.inference_engine.generate(
                    prompt, system_prompt=system
                )
```

- [ ] **Step 5: Injecter le moteur dans le conteneur**

Dans `backend/api/animetix/containers/agentic.py`, ajouter au provider `guardrail_service` :

```python
        moderation_engine=inference.brain_guardrail_adapter,
```

- [ ] **Step 6: Lancer les tests pour vérifier qu'ils passent**

Run: `.venv\Scripts\python.exe -m pytest tests/core/test_guardrail_moderation_engine.py -v`
Expected: PASS (3 tests).

- [ ] **Step 7: Vérifier la non-régression du guardrail**

Run: `.venv\Scripts\python.exe -m pytest tests/core tests/adapters -q`
Expected: PASS — en particulier les tests existants du guardrail, qui construisent `GuardrailService` sans `moderation_engine`.

- [ ] **Step 8: Commit**

```bash
git add backend/core/domain/services/guardrail_service.py backend/api/animetix/containers/agentic.py tests/core/test_guardrail_moderation_engine.py
git commit -m "feat(guardrail): run moderation prompts on a dedicated small engine"
```

---

### Task 6: Mesurer, déployer, vérifier en production

Aucun gain n'est annoncé sur une estimation. Cette tâche produit le chiffre.

**Files:**
- Aucun fichier de code. Produit une mesure et un déploiement.

**Interfaces:**
- Consumes: tout ce qui précède.
- Produces: un couple de mesures avant/après documenté dans le message de commit final ou le TODO.

- [ ] **Step 1: Mesurer la référence, sur instance chaude**

La seule mesure existante (6,79 s pour 3 tokens) a été prise sur une instance qui venait de démarrer et inclut probablement le chargement des 4,7 Go : elle ne vaut pas de référence. Chauffer d'abord, mesurer ensuite :

```powershell
$url = gcloud run services describe animetix-brain --region=europe-west1 --format="value(status.url)" --project=animetix
$key = gcloud secrets versions access latest --secret=BRAIN_API_KEY --project=animetix
# Chauffe (jetée), puis mesure
curl.exe -s -m 240 -X POST "$url/generate" -H "X-API-Key: $key" -H "Content-Type: application/json" --data-binary "@bench.json" > $null
curl.exe -s -m 240 -w "`nHTTP %{http_code} in %{time_total}s`n" -X POST "$url/generate" -H "X-API-Key: $key" -H "Content-Type: application/json" --data-binary "@bench.json"
```

`bench.json` contient un prompt de modération réaliste (le prompt `output_moderator` avec une réponse d'exemple), pas un « hi ».

- [ ] **Step 2: Reconstruire et déployer l'image brain**

Obligatoire : la CI ne reconstruit jamais le brain. Sans ce pas, le tag du modérateur n'existe pas en production, `/generate` renvoie 400 et le repli de la Task 5 ramène toute la modération sur le 7B — pipeline vert, gain nul.

```bash
python scripts/deploy/gcp/deploy_brain.py
```

- [ ] **Step 3: Vérifier que le modérateur est réellement servi**

```powershell
curl.exe -s "$url/health"
```

Expected: le champ `models` liste trois tags, dont `qwen2.5:1.5b-instruct`. Si le tag manque, l'image déployée n'est pas la bonne — ne pas continuer.

- [ ] **Step 4: Mesurer après, dans les mêmes conditions**

Rejouer exactement la commande du Step 1 avec `"model": "qwen2.5:1.5b-instruct"` ajouté à `bench.json`. Noter les deux temps.

- [ ] **Step 5: Consigner le résultat**

Ajouter les deux chiffres au `TODO.md` (ou au message du commit de clôture). Si le gain mesuré est inférieur à un facteur 2, le dire — et envisager le `0.5b`, qui ne coûte qu'une variable d'environnement (`GUARDRAIL_MODEL_NAME`) et un rebuild.

- [ ] **Step 6: Commit**

```bash
git add TODO.md
git commit -m "chore(brain): record the measured moderation latency before/after"
```

---

## Auto-relecture

**Couverture de la spec.** Chaque section a sa tâche : le champ `model` sur les deux endpoints et l'allowlist `/api/tags` → Task 2 ; le troisième tag baké et son préchauffage → Task 1 ; le rôle `GUARDRAIL_OLLAMA_MODEL` et le `brain_guardrail_adapter` → Tasks 1 et 4 ; le recâblage du `safety_engine` → Task 4 ; le `moderation_engine` de `GuardrailService` → Task 5 ; les postures d'échec → Task 5 (repli explicite) ; l'extension du garde-fou → Task 1 ; la mesure et le déploiement manuel → Task 6.

**Cohérence des noms.** `GUARDRAIL_OLLAMA_MODEL` (constante Python) / `GUARDRAIL_MODEL_NAME` (variable d'env) / `GUARDRAIL_MODEL` (ARG Docker) sont trois noms pour trois plans distincts, employés de façon constante ; `engine_for`, `_served_models`, `_served_models_cache`, `_engines`, `brain_guardrail_adapter`, `moderation_engine` gardent la même signature d'une tâche à l'autre. Le test de la Task 2 remet `_served_models_cache` à `None`, ce que la Task 2 définit bien comme nom de module.

**Ordre.** Les tâches 2 et 3 sont indépendantes l'une de l'autre mais toutes deux nécessaires avant la 5 ; la 4 dépend de la 3 (paramètre `model` du constructeur) et de la 1 (constante importée). La 6 vient en dernier et ne peut pas être anticipée.
