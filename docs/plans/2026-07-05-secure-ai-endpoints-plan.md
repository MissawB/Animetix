# Sécurisation des endpoints IA/GPU + throttling — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fermer les 4 accès IA/GPU anonymes non facturés (S2S Live WS, carte-monde LLM, VideoRAG, modération LLM de la recherche) et remplacer le throttling « journalier ou rien » par un système à deux vitesses (burst/minute + scope GPU + protection des jeux CPU).

**Architecture:** On suit le pattern Bx canonique existant (`deduct_berrix` + `check_quota` + `log_usage`, cf. `paradox.py`). Une nouvelle unité `api/throttles.py` centralise les classes de throttle. La carte-monde passe en cache partagé (artefact identique pour tous). Le WS S2S gagne une garde auth+Bx au connect.

**Tech Stack:** Django/DRF, channels (WS), django cache (Redis en prod), React/TS, pytest + channels.testing, vitest.

**Spec:** `docs/plans/2026-07-05-secure-ai-endpoints-design.md` (validée).

## Global Constraints

- Windows : python du venv — `.venv/Scripts/python.exe` (Git Bash) depuis la racine du repo.
- NE PAS lancer la suite `tests/api` complète en local (mass-fail sans backend d'inférence) — fichiers ciblés uniquement ; validation large via `-m "not integration"`.
- Namespace nu obligatoire (tripwire actif) : imports `animetix.*`/`core.*`, jamais `backend.*`.
- Pattern Bx canonique verbatim (`paradox.py:74-120`) : `usage_port.check_quota(user.id, tier)` (403 si dépassé) PUIS `deduct_berrix(user, FEATURE_BX_COSTS[key], label)` (lève → 402) PUIS l'appel GPU PUIS `usage_port.log_usage(...)`. Ne jamais appeler le GPU avant la déduction.
- `deduct_berrix` (`api/billing.py:23`) lève `PaymentRequired` (402) si anonyme OU solde < coût.
- Coûts centralisés dans `FEATURE_BX_COSTS` (`core/domain/services/berrix_economy.py:93`), entiers.
- Jeux CPU : NE JAMAIS leur appliquer le cap journalier `anon`/`user` (cause des 429 mid-game) — uniquement le throttle `cpu_game` par minute.
- Travail sur branche `chore/secure-ai-endpoints` (créée en Task 1). `git add` par chemins explicites, jamais `-A`. Ne JAMAIS toucher `main` ni pousser.
- Pre-commit hooks actifs (ruff/black) ; jamais `--no-verify`. mypy local cassé (`SKIP=mypy` attendu, CI l'applique).

---

### Task 1: Infrastructure de throttling (classes + rates + application)

**Files:**
- Create: `backend/api/animetix/api/throttles.py`
- Create: `tests/api/test_throttles.py`
- Modify: `backend/api/animetix_project/settings.py:254-259`
- Modify: `backend/api/animetix/api/games/emoji.py` (5 vues, `throttle_classes`)
- Modify: `backend/api/animetix/api/games/undercover.py:22`
- Modify: `backend/api/animetix/api/games/covertest.py` (5 vues, `throttle_classes`)
- Modify: `backend/api/animetix/api/labs.py:153,506,579` (ajouter `ScopedRateThrottle` aux 3 vues `throttle_scope="gpu"`)

**Interfaces:**
- Produces: `BurstAnonRateThrottle` (scope `anon_burst`), `BurstUserRateThrottle` (scope `user_burst`), `CpuGameThrottle` (scope `cpu_game`) dans `animetix.api.throttles`. Rates dans settings : `anon_burst:30/min`, `user_burst:120/min`, `cpu_game:60/min`, `gpu:30/hour`.

- [ ] **Step 1: Écrire les tests de config des rates**

`tests/api/test_throttles.py` :

```python
from django.conf import settings
from rest_framework.throttling import ScopedRateThrottle

from animetix.api.throttles import (
    BurstAnonRateThrottle,
    BurstUserRateThrottle,
    CpuGameThrottle,
)


def test_all_declared_scopes_have_a_rate():
    rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
    for scope in ("anon", "user", "anon_burst", "user_burst", "cpu_game", "gpu"):
        assert scope in rates, f"missing rate for scope {scope}"
        assert rates[scope], f"empty rate for scope {scope}"


def test_burst_throttles_have_expected_scopes():
    assert BurstAnonRateThrottle.scope == "anon_burst"
    assert BurstUserRateThrottle.scope == "user_burst"
    assert CpuGameThrottle.scope == "cpu_game"


def test_burst_classes_are_in_default_throttle_classes():
    classes = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"]
    assert "animetix.api.throttles.BurstAnonRateThrottle" in classes
    assert "animetix.api.throttles.BurstUserRateThrottle" in classes


def test_gpu_scoped_throttle_resolves_a_rate():
    # A view declaring throttle_scope="gpu" with ScopedRateThrottle must resolve
    # a concrete rate (the historical bug: scope declared but no rate → no-op).
    t = ScopedRateThrottle()
    t.scope = "gpu"
    assert t.get_rate() == "30/hour"
```

- [ ] **Step 2: RED**

```bash
.venv/Scripts/python.exe -m pytest tests/api/test_throttles.py -q
```

Attendu : ÉCHEC à l'import (`animetix.api.throttles` n'existe pas).

- [ ] **Step 3: Créer les classes de throttle**

`backend/api/animetix/api/throttles.py` :

```python
"""Throttles à deux vitesses.

Historique : les seuls rates étaient des caps journaliers (anon 100/day,
user 1000/day) — inefficaces contre les rafales, et si agressifs sur les jeux
CPU qu'ils étaient désactivés (`throttle_classes = []`), supprimant TOUTE
protection. On ajoute des limites par minute et un throttle dédié aux jeux CPU.
"""

from rest_framework.throttling import (
    AnonRateThrottle,
    ScopedRateThrottle,
    UserRateThrottle,
)


class BurstAnonRateThrottle(AnonRateThrottle):
    """Plafond anti-rafale par minute pour les anonymes (en plus du cap /day)."""

    scope = "anon_burst"


class BurstUserRateThrottle(UserRateThrottle):
    """Plafond anti-rafale par minute pour les authentifiés (en plus du /day)."""

    scope = "user_burst"


class CpuGameThrottle(ScopedRateThrottle):
    """Throttle par minute pour les jeux CPU AllowAny.

    Protège du flood sans jamais appliquer le cap journalier global (qui coupait
    des parties en cours). Utilise l'IP pour les anonymes, l'utilisateur sinon.
    """

    scope = "cpu_game"

    def __init__(self):
        # ScopedRateThrottle lit self.scope depuis view.throttle_scope ; ici on
        # fixe le scope sur la classe pour l'utiliser sans view.throttle_scope.
        self.rate = self.get_rate()
        self.num_requests, self.duration = self.parse_rate(self.rate)
```

- [ ] **Step 4: Ajouter les rates + classes burst dans settings**

Dans `backend/api/animetix_project/settings.py`, remplacer le bloc (l.254-259) :

```python
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "100/day", "user": "1000/day"},
}
```

par :

```python
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "animetix.api.throttles.BurstAnonRateThrottle",
        "animetix.api.throttles.BurstUserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
        "anon_burst": "30/min",
        "user_burst": "120/min",
        "cpu_game": "60/min",
        "gpu": "30/hour",
    },
}
```

(Vérifier la structure exacte du bloc `REST_FRAMEWORK` avant d'éditer : s'il utilise déjà une liste multi-lignes pour `DEFAULT_THROTTLE_CLASSES`, adapter le match ; le résultat final doit contenir les 4 classes et les 6 rates ci-dessus.)

- [ ] **Step 5: GREEN sur la config**

```bash
.venv/Scripts/python.exe -m pytest tests/api/test_throttles.py -q
```

Attendu : 4 passed.

- [ ] **Step 6: Appliquer `CpuGameThrottle` aux jeux CPU**

Dans chacune des vues portant `throttle_classes: list = []` (emoji.py l.86,130,171,283,328 ; undercover.py l.22 ; covertest.py l.76,109,144,174,192), remplacer la valeur `[]` par `[CpuGameThrottle]` et ajouter en tête de fichier `from animetix.api.throttles import CpuGameThrottle`. Exemple pour emoji.py :

```python
    throttle_classes = [CpuGameThrottle]  # CPU game, no Bx: minute-cap only, never the day cap
```

(covertest.py a une annotation multi-ligne `throttle_classes: list = (\n []\n )` — la remplacer par `throttle_classes = [CpuGameThrottle]` sur une ligne, en gardant le commentaire adjacent.)

- [ ] **Step 7: Câbler le scope `gpu` sur les 3 vues labs**

Dans `backend/api/animetix/api/labs.py`, pour chacune des 3 vues déclarant `throttle_scope = "gpu"` (l.153, 506, 579), ajouter `ScopedRateThrottle` à ses throttles. Comme ces vues n'ont pas de `throttle_classes`, ajouter la ligne juste après `throttle_scope = "gpu"` :

```python
    throttle_scope = "gpu"
    throttle_classes = [ScopedRateThrottle]
```

et ajouter en tête de `labs.py` : `from rest_framework.throttling import ScopedRateThrottle` (vérifier qu'il n'y est pas déjà).

- [ ] **Step 8: Lint + tests jeux (aucune régression)**

```bash
.venv/Scripts/python.exe -m ruff check backend/api/animetix/api/ tests/api/test_throttles.py
.venv/Scripts/python.exe -m pytest tests/api/games/ tests/api/test_throttles.py -q -m "not integration" 2>&1 | tail -3
```

Attendu : ruff propre ; tests jeux verts (les jeux passent toujours, throttle non déclenché à faible volume).

- [ ] **Step 9: Commit**

```bash
git add backend/api/animetix/api/throttles.py tests/api/test_throttles.py backend/api/animetix_project/settings.py backend/api/animetix/api/games/emoji.py backend/api/animetix/api/games/undercover.py backend/api/animetix/api/games/covertest.py backend/api/animetix/api/labs.py
git commit -m "feat(throttle): two-speed throttling — per-minute burst + cpu_game + real gpu scope"
```

---

### Task 2: Nouveaux coûts Bx + sécurisation de VideoRAGSearchView

**Files:**
- Modify: `backend/core/domain/services/berrix_economy.py:93+` (ajouter `video_rag`, `s2s_live`)
- Modify: `backend/api/animetix/api/labs.py:640-658` (`VideoRAGSearchView`)
- Test: `tests/api/test_video_rag_security.py` (create)

**Interfaces:**
- Consumes: `FEATURE_BX_COSTS` (Task 2 ajoute les clés), `deduct_berrix`, `check_quota`/`log_usage` du `usage_port`, throttle `gpu` (Task 1).
- Produces: `FEATURE_BX_COSTS["video_rag"] = 6`, `FEATURE_BX_COSTS["s2s_live"] = 12` (consommé en Task 5).

- [ ] **Step 1: Ajouter les deux coûts**

Dans `backend/core/domain/services/berrix_economy.py`, dans le dict `FEATURE_BX_COSTS`, ajouter près des « quick ops » :

```python
    "video_rag": 6,   # RAG/vector search over indexed video embeddings
    "s2s_live": 12,   # Gemini Multimodal Live session (flat per-session charge)
```

- [ ] **Step 2: Écrire le test de sécurité VideoRAG**

`tests/api/test_video_rag_security.py` :

```python
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def _mk_user(balance):
    from animetix.models import Profile

    User = get_user_model()
    u = User.objects.create_user(username="vr", password="x")
    Profile.objects.filter(user=u).update(wallet_balance=balance)
    return u


def test_video_rag_anonymous_is_401():
    resp = APIClient().get("/api/v1/labs/video/search/", {"q": "duel"})
    assert resp.status_code == 401


def test_video_rag_zero_balance_is_402(mocker):
    u = _mk_user(0)
    c = APIClient()
    c.force_authenticate(u)
    resp = c.get("/api/v1/labs/video/search/", {"q": "duel"})
    assert resp.status_code == 402


def test_video_rag_happy_path_deducts_and_returns(mocker):
    from animetix.models import Profile

    u = _mk_user(100)
    mocker.patch(
        "animetix.containers.get_container"
    ).return_value.agentic.video_rag_service.return_value.search_video_segment.return_value = [
        {"id": 1}
    ]
    c = APIClient()
    c.force_authenticate(u)
    resp = c.get("/api/v1/labs/video/search/", {"q": "duel"})
    assert resp.status_code == 200
    assert Profile.objects.get(user=u).wallet_balance == 94  # 100 - 6
```

(Vérifier au moment de l'implémentation le chemin URL réel de `VideoRAGSearchView` dans `urls/` — l'ajuster dans les 3 tests s'il diffère de `/api/v1/labs/video/search/`. Vérifier aussi comment `Profile`/`wallet_balance` est créé — via signal `post_save` ; le `Profile.objects.filter(...).update()` suppose que le profil existe déjà, sinon le créer.)

- [ ] **Step 3: RED**

```bash
.venv/Scripts/python.exe -m pytest tests/api/test_video_rag_security.py -q
```

Attendu : `test_video_rag_anonymous_is_401` échoue (la vue est AllowAny → 200/500), les autres aussi.

- [ ] **Step 4: Sécuriser la vue**

Remplacer `VideoRAGSearchView` (`backend/api/animetix/api/labs.py:640-658`) par :

```python
class VideoRAGSearchView(APIView):
    """Endpoint pour rechercher des moments précis dans les vidéos indexées.

    GPU/RAG : requiert login + consomme des Berrix (règle « GPU = Bx »).
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "gpu"
    throttle_classes = [ScopedRateThrottle]

    def get(self, request):
        from core.domain.services.berrix_economy import FEATURE_BX_COSTS

        from animetix.api.billing import deduct_berrix

        query = request.GET.get("q")
        if not query:
            return Response({"error": "query q is required"}, status=400)

        container = get_container()
        usage_port = container.infrastructure.usage_port()
        tier = getattr(request, "user_tier", "free")
        if not usage_port.check_quota(request.user.id, tier):
            return Response({"error": "Daily AI quota exceeded."}, status=403)
        deduct_berrix(
            request.user, FEATURE_BX_COSTS["video_rag"], "VideoRAG — recherche vidéo"
        )

        video_rag = container.agentic.video_rag_service()
        try:
            results = video_rag.search_video_segment(query, limit=10)
            usage_port.log_usage(
                engine="video-rag", units=1, user_id=request.user.id
            )
            return Response({"status": "success", "results": results})
        except Exception:
            logger.exception("VideoRAGSearch Error")
            return Response({"error": "Internal server error"}, status=500)
```

(Vérifier le nom exact du provider `usage_port` et sa signature `check_quota`/`log_usage` contre `paradox.py:74-120` — les copier tel quel ; `ScopedRateThrottle` a été importé en Task 1.)

- [ ] **Step 5: GREEN**

```bash
.venv/Scripts/python.exe -m pytest tests/api/test_video_rag_security.py -q
.venv/Scripts/python.exe -m ruff check backend/api/animetix/api/labs.py backend/core/domain/services/berrix_economy.py
```

Attendu : 3 passed ; ruff propre.

- [ ] **Step 6: Commit**

```bash
git add backend/core/domain/services/berrix_economy.py backend/api/animetix/api/labs.py tests/api/test_video_rag_security.py
git commit -m "feat(security): require auth+Bx on VideoRAGSearchView (GPU/RAG endpoint)"
```

---

### Task 3: Modération LLM réservée aux authentifiés (MediaSearch)

**Files:**
- Modify: `backend/core/domain/services/guardrail_service.py:71` (`validate_input` signature)
- Modify: `backend/api/animetix/api/core.py` (`MediaSearchView.get`, l.~122 appel guardrail)
- Test: `tests/core/test_guardrail_llm_gating.py` (create)

**Interfaces:**
- Consumes: rien de neuf.
- Produces: `validate_input(text, allow_llm=True)` — quand `allow_llm=False`, le fallback `_llm_moderate` n'est jamais appelé.

- [ ] **Step 1: Écrire le test**

`tests/core/test_guardrail_llm_gating.py` :

```python
from unittest.mock import MagicMock


def _svc():
    from core.domain.services.guardrail_service import GuardrailService

    safety = MagicMock()
    # Force le chemin "stub" qui déclencherait normalement le fallback LLM
    safety.moderate_content.return_value = {"is_safe": True, "detected_categories": []}
    svc = GuardrailService(safety_engine=safety, prompt_manager=None, inference_engine=MagicMock())
    svc._llm_moderate = MagicMock(return_value={"is_safe": True, "detected_categories": ["X"]})
    svc._check_agent_gateway = MagicMock(return_value=None)
    svc._is_potential_jailbreak = MagicMock(return_value=False)
    return svc


def test_allow_llm_false_skips_llm_moderation():
    svc = _svc()
    svc.validate_input("some query", allow_llm=False)
    svc._llm_moderate.assert_not_called()


def test_allow_llm_true_uses_llm_fallback():
    svc = _svc()
    svc.validate_input("some query", allow_llm=True)
    svc._llm_moderate.assert_called_once()
```

(Vérifier le constructeur réel de `GuardrailService` — adapter les kwargs du `GuardrailService(...)` à sa vraie signature.)

- [ ] **Step 2: RED**

```bash
.venv/Scripts/python.exe -m pytest tests/core/test_guardrail_llm_gating.py -q
```

Attendu : `TypeError: validate_input() got an unexpected keyword argument 'allow_llm'`.

- [ ] **Step 3: Ajouter le flag `allow_llm`**

Dans `backend/core/domain/services/guardrail_service.py`, changer la signature (l.71) :

```python
    def validate_input(self, text: str, allow_llm: bool = True) -> Dict[str, Any]:
```

et garder le fallback LLM derrière le flag (le bloc `if (not result or ... or is_stub):` l.~107) :

```python
            if (
                not result
                or result.get("stub")
                or result.get("action") == "none"
                or is_stub
            ):
                if allow_llm:
                    result = self._llm_moderate(
                        text, self.enabled_categories, mode="input"
                    )

            return result
```

- [ ] **Step 4: Passer `allow_llm` depuis MediaSearchView**

Dans `backend/api/animetix/api/core.py`, dans `MediaSearchView.get`, l'appel `self.guardrail_service.validate_input(query)` devient :

```python
            guard_input = self.guardrail_service.validate_input(
                query, allow_llm=request.user.is_authenticated
            )
```

- [ ] **Step 5: GREEN + non-régression guardrail**

```bash
.venv/Scripts/python.exe -m pytest tests/core/test_guardrail_llm_gating.py -q
.venv/Scripts/python.exe -m pytest tests/core/ -k guardrail -q -m "not integration" 2>&1 | tail -3
.venv/Scripts/python.exe -m ruff check backend/core/domain/services/guardrail_service.py backend/api/animetix/api/core.py
```

Attendu : 2 passed ; suites guardrail existantes vertes ; ruff propre.

- [ ] **Step 6: Commit**

```bash
git add backend/core/domain/services/guardrail_service.py backend/api/animetix/api/core.py tests/core/test_guardrail_llm_gating.py
git commit -m "feat(security): gate the guardrail LLM-moderation fallback to authenticated users"
```

---

### Task 4: Carte-monde en cache partagé

**Files:**
- Modify: `backend/api/animetix/api/graph.py:73-91` (`GraphWorldMapView`)
- Test: `tests/api/test_world_map_cache.py` (create)

**Interfaces:**
- Consumes: `django.core.cache`.
- Produces: `GraphWorldMapView` sert le cache ; 202 `{"status": "generating"}` pendant la génération concurrente.

- [ ] **Step 1: Écrire le test**

`tests/api/test_world_map_cache.py` :

```python
import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


def test_second_hit_serves_cache_without_partitioning(mocker):
    fake = mocker.patch("animetix.containers.get_container")
    partitioner = fake.return_value.agentic.community_partitioner.return_value
    partitioner.run_partitioning.return_value = [{"name": "C1"}]

    c = APIClient()
    r1 = c.get("/api/v1/graph/world-map/")
    r2 = c.get("/api/v1/graph/world-map/")

    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.data == r2.data == [{"name": "C1"}]
    # Only the first hit ran the LLM partitioning.
    partitioner.run_partitioning.assert_called_once()
```

(Vérifier le chemin URL réel de `GraphWorldMapView` et l'ajuster ; le `get_container` mocké doit correspondre à la façon dont la vue résout le partitioner — la vue actuelle l'injecte via `@inject`/`Provide`, donc le mock doit patcher ce provider. Si l'injection DI rend le mock difficile, patcher directement `animetix.api.graph.GraphWorldMapView.partitioner` via `mocker.patch.object` sur l'instance, ou le provider `Container.agentic.community_partitioner`. Choisir le point de patch qui fonctionne et le documenter dans le rapport.)

- [ ] **Step 2: RED**

```bash
.venv/Scripts/python.exe -m pytest tests/api/test_world_map_cache.py -q
```

Attendu : échec sur `assert_called_once` (aujourd'hui chaque hit appelle `run_partitioning`).

- [ ] **Step 3: Ajouter le cache partagé**

Remplacer la méthode `get` de `GraphWorldMapView` (`backend/api/animetix/api/graph.py`) par :

```python
    def get(self, request):
        from django.core.cache import cache

        cache_key = "graph:world_map:v1"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        # Anti-stampede : un seul hit génère ; les concurrents reçoivent 202 et
        # le frontend re-tente. La carte est un artefact partagé (identique pour
        # tous), donc on ne facture personne et on ne régénère qu'à l'expiration.
        lock_key = "graph:world_map:v1:lock"
        if not cache.add(lock_key, "1", timeout=120):
            return Response({"status": "generating"}, status=202)

        try:
            communities = self.partitioner.run_partitioning()
            cache.set(cache_key, communities, timeout=86400)  # 24 h
            return Response(communities)
        finally:
            cache.delete(lock_key)
```

- [ ] **Step 4: GREEN**

```bash
.venv/Scripts/python.exe -m pytest tests/api/test_world_map_cache.py -q
.venv/Scripts/python.exe -m ruff check backend/api/animetix/api/graph.py
```

Attendu : 1 passed ; ruff propre.

- [ ] **Step 5: Commit**

```bash
git add backend/api/animetix/api/graph.py tests/api/test_world_map_cache.py
git commit -m "perf(graph): cache the shared world-map artifact (kill per-hit anon LLM cost)"
```

---

### Task 5: WebSocket S2S Live — auth + Bx + durée max

**Files:**
- Modify: `backend/api/animetix/consumers/speech_to_speech_live.py:88-119` (`connect`)
- Test: `tests/backend/test_s2s_live_security.py` (create)

**Interfaces:**
- Consumes: `FEATURE_BX_COSTS["s2s_live"]` (Task 2), `deduct_berrix`, la vérif token de `GoogleIdentityAuthentication`.
- Produces: `connect()` refuse 4401 (non auth), 4402 (solde), 4408 (timeout).

- [ ] **Step 1: Écrire le test (channels testing)**

`tests/backend/test_s2s_live_security.py` :

```python
import pytest
from channels.testing import WebsocketCommunicator

from animetix_project.asgi import application

pytestmark = [pytest.mark.django_db, pytest.mark.asyncio]


async def _connect(path):
    comm = WebsocketCommunicator(application, path)
    connected, code = await comm.connect()
    await comm.disconnect()
    return connected, code


async def test_anonymous_connection_is_rejected():
    connected, code = await _connect("/ws/labs/s2s/live/")
    assert connected is False
    assert code == 4401
```

(Le test authentifié+Bx est complexe à monter sous channels — le brief se limite au rejet anonyme, qui est le contrôle de sécurité principal ; ajouter le cas authentifié-sans-solde → 4402 si le montage d'un scope user via `WebsocketCommunicator` est faisable proprement, sinon le noter comme couvert par revue manuelle dans le rapport.)

- [ ] **Step 2: RED**

```bash
.venv/Scripts/python.exe -m pytest tests/backend/test_s2s_live_security.py -q
```

Attendu : échec (aujourd'hui `connect()` fait `self.accept()` inconditionnel → `connected is True`).

- [ ] **Step 3: Garde auth + Bx + timeout dans connect()**

Remplacer le début de `connect()` (`backend/api/animetix/consumers/speech_to_speech_live.py`, de `async def connect(self):` jusqu'à `self.receiver_task = asyncio.create_task(...)` inclus) par :

```python
    async def connect(self):
        user = await self._resolve_user()
        if user is None or not user.is_authenticated:
            await self.close(code=4401)
            return
        self.user = user

        # GPU facturé : déduction forfaitaire par session (règle « GPU = Bx »).
        if not await self._charge_session():
            await self.close(code=4402)
            return

        await self.accept()
        self.client_connected = True
        self.gemini_session = None
        self.gemini_client = None
        self.receiver_task = None

        from urllib.parse import parse_qs

        query_string = self.scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        profile_id_str = query_params.get("voice_profile_id", [None])[0]
        self.voice_profile_id = (
            int(profile_id_str)
            if (profile_id_str and profile_id_str.isdigit())
            else None
        )

        # Borne le coût Gemini : coupe la session après 10 min.
        self.deadline_task = asyncio.create_task(self._enforce_deadline())
        self.receiver_task = asyncio.create_task(self.run_gemini_session())
        logger.info("SpeechToSpeechLiveConsumer client connected (user=%s).", self.user.id)

    async def _resolve_user(self):
        # 1) Session (AuthMiddlewareStack) ; 2) token Firebase en query param.
        user = self.scope.get("user")
        if user is not None and user.is_authenticated:
            return user
        from urllib.parse import parse_qs

        qs = parse_qs(self.scope.get("query_string", b"").decode("utf-8"))
        token = qs.get("token", [None])[0]
        if not token:
            return None
        return await self._verify_firebase_token(token)

    @database_sync_to_async
    def _verify_firebase_token(self, token):
        from rest_framework.exceptions import AuthenticationFailed

        from animetix.auth import GoogleIdentityAuthentication

        # Réutilise le vérificateur DRF : on fabrique une pseudo-requête portant
        # l'Authorization Bearer attendu par authenticate().
        class _Req:
            META = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

        try:
            result = GoogleIdentityAuthentication().authenticate(_Req())
        except AuthenticationFailed:
            return None
        return result[0] if result else None

    @database_sync_to_async
    def _charge_session(self):
        from core.domain.services.berrix_economy import FEATURE_BX_COSTS

        from animetix.api.billing import deduct_berrix

        try:
            deduct_berrix(
                self.user, FEATURE_BX_COSTS["s2s_live"], "Speech-to-Speech Live (session)"
            )
            return True
        except Exception:
            return False

    async def _enforce_deadline(self):
        await asyncio.sleep(600)  # 10 minutes
        logger.info("S2S session deadline reached (user=%s), closing.", getattr(self, "user", None))
        await self.close(code=4408)
```

(Vérifier que `GoogleIdentityAuthentication().authenticate` accepte un objet avec seulement `.META` — c'est le cas d'après le code (l.150 : lit `request.META.get("HTTP_AUTHORIZATION")`). Vérifier aussi que `disconnect()` annule bien `self.deadline_task` s'il existe — ajouter `if getattr(self, "deadline_task", None): self.deadline_task.cancel()` dans `disconnect()`.)

- [ ] **Step 4: GREEN**

```bash
.venv/Scripts/python.exe -m pytest tests/backend/test_s2s_live_security.py -q
.venv/Scripts/python.exe -m ruff check backend/api/animetix/consumers/speech_to_speech_live.py
```

Attendu : test(s) verts ; ruff propre.

- [ ] **Step 5: Commit**

```bash
git add backend/api/animetix/consumers/speech_to_speech_live.py tests/backend/test_s2s_live_security.py
git commit -m "feat(security): require auth+Bx on the S2S Live WS + 10-min session cap"
```

---

### Task 6: Frontend — gates login sur les pages nouvellement protégées

**Files:**
- Modify: `frontend/src/pages/labs/VideoLabPage.tsx`
- Modify: `frontend/src/pages/labs/VisualNexusPage.tsx`
- Modify: `frontend/src/pages/labs/SpeechToSpeechLabPage.tsx` (gate + token WS)
- Test: `frontend/src/pages/labs/__tests__/*` (adapter/ajouter selon le pattern de gate existant)

**Interfaces:**
- Consumes: le hook d'auth existant (`useAuth()`), le helper de token Firebase (`getIdToken`, cf. `apiClient.ts:19`).

- [ ] **Step 1: Repérer le pattern de gate existant**

Lire une page déjà gatée par Bx/login (p.ex. une page qui appelle `run_vs_battle` ou `paradox`) pour copier son mécanisme exact (composant `RequireAuth`, redirection, ou prompt inline). Documenter le pattern trouvé dans le rapport avant d'éditer.

```bash
grep -rln "useAuth\|RequireAuth\|isAuthenticated\|login" frontend/src/pages/games/VsBattlePage.tsx frontend/src/pages/games/ParadoxPage.tsx
```

- [ ] **Step 2: Gater VideoLabPage et VisualNexusPage**

Appliquer le même gate login que les pages Bx existantes à `VideoLabPage.tsx` et `VisualNexusPage.tsx` : si l'utilisateur n'est pas authentifié, afficher le prompt/redirect login au lieu de déclencher l'appel VideoRAG. (Reproduire le pattern repéré au Step 1 — code exact selon ce pattern.)

- [ ] **Step 3: Gater + tokeniser SpeechToSpeechLabPage**

Dans `SpeechToSpeechLabPage.tsx` : (a) gate login identique ; (b) à l'ouverture du WebSocket, ajouter le token Firebase à l'URL — `const token = await auth.currentUser.getIdToken(); const ws = new WebSocket(\`${base}/ws/labs/s2s/live/?token=${token}&voice_profile_id=${id}\`)` (adapter à la construction d'URL réelle de la page).

- [ ] **Step 4: Vérifier build + tests + lint frontend**

```bash
cd frontend && npm run type-check 2>&1 | tail -5
npx eslint src/pages/labs/VideoLabPage.tsx src/pages/labs/VisualNexusPage.tsx src/pages/labs/SpeechToSpeechLabPage.tsx
npx vitest run src/pages/labs 2>&1 | tail -8
```

Attendu : type-check propre, eslint propre, tests verts (ajouter/adapter un test de gate par page si le pattern de gate est testé ailleurs).

- [ ] **Step 5: Commit**

```bash
cd .. && git add frontend/src/pages/labs/VideoLabPage.tsx frontend/src/pages/labs/VisualNexusPage.tsx frontend/src/pages/labs/SpeechToSpeechLabPage.tsx frontend/src/pages/labs/__tests__/
git commit -m "feat(labs): login-gate Video/VisualNexus/S2S pages + pass WS auth token"
```

---

### Task 7: Vérification finale + clôture docs

**Files:**
- Modify: `TODO.md` (item 🟠 « AllowAny »)
- Modify: `docs/HISTORY.md` (entrée en tête)

**Interfaces:**
- Consumes: Tasks 1-6.

- [ ] **Step 1: Suite backend CI-équivalente**

```bash
.venv/Scripts/python.exe -m pytest -m "not integration" --cov=backend --cov-report=term -q 2>&1 | tail -4
```

Attendu : 0 failed ; couverture ≥ 75 %. Si des échecs apparaissent, les quoter et reporter DONE_WITH_CONCERNS (ne pas bricoler).

- [ ] **Step 2: TODO — clore l'item**

Remplacer l'item `- [ ] **Sécu/coûts — endpoints IA/GPU en \`AllowAny\`...` (les deux puces) par :

```markdown
- [x] **Sécu/coûts — endpoints IA/GPU en `AllowAny` + throttling incohérent** _(audit dette 2026-07-05 ; **clos** le 2026-07-05, archivé dans [docs/HISTORY.md](docs/HISTORY.md))_
  - Inventaire : 3 des 4 vues labs citées étaient CPU (restent publiques). 4 vrais trous fermés : S2S Live WS (auth+Bx forfaitaire+cap 10 min), carte-monde (cache partagé public), VideoRAG (auth+Bx), fallback modération LLM (réservé aux authentifiés). Throttling à deux vitesses : burst/minute global + scope `gpu` réhabilité + `cpu_game` sur les jeux (fin des `throttle_classes=[]`). Spec : [docs/plans/2026-07-05-secure-ai-endpoints-design.md](docs/plans/2026-07-05-secure-ai-endpoints-design.md).
```

- [ ] **Step 3: HISTORY — entrée de clôture**

Insérer après la ligne d'intro de `docs/HISTORY.md`, avant la première section datée :

```markdown
## [2026-07-05] Session: Secured the anonymous AI/GPU endpoints + rationalized throttling

Closure of the 🟠 debt item on `AllowAny` AI endpoints. A precise inventory corrected the audit: 3 of the 4 named labs views are CPU/DB and stayed public; the real anonymous GPU holes were the Speech-to-Speech Live WebSocket (a full Gemini Live session, now auth-gated with a flat 12-Bx per-session charge and a 10-minute cap), `GraphWorldMapView` (per-hit LLM community summaries, now a 24 h shared cache — the map is identical for everyone, so it stays public and bills no one), `VideoRAGSearchView` (now IsAuthenticated + 6-Bx via the canonical deduct_berrix pattern), and the guardrail's `_llm_moderate` fallback on `MediaSearchView` (now authenticated-only; anonymous search keeps the heuristic layer). Throttling went from "daily cap or nothing" to two-speed: per-minute burst throttles (anon 30/min, user 120/min) added globally, the long-dead `gpu` scope wired to a real 30/hour rate, and a `cpu_game` 60/min throttle replacing the `throttle_classes = []` overrides on emoji/undercover/covertest (which had removed all protection to avoid the daily cap cutting games mid-session).
```

- [ ] **Step 4: Commit**

```bash
git add TODO.md docs/HISTORY.md
git commit -m "docs: close the AllowAny AI-endpoints debt item"
```
