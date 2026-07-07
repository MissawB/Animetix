# Suppression des features Stripe — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Retirer tout le code de paiement Stripe (endpoints checkout, webhook, service, packs, colonnes DB, dépendance, UI d'achat morte), en gardant le tier Pro comme concept gratuit/manuel.

**Architecture:** Suppression pure, ordonnée pour ne jamais laisser de référence pendante : (1) retirer le code backend qui référence les champs/service Stripe et repurposer le mock Pro, (2) retirer les 3 colonnes DB + migration, (3) retirer PACKS + settings + dépendance, (4) retirer l'UI d'achat morte + régénérer les types, (5) vérifier + clore.

**Tech Stack:** Django/DRF, pytest, pip-tools, React/TS, drf-spectacular (génération OpenAPI).

**Spec (validée, inline)** : retirer paiement Stripe ; Berrix gagnés (pub/mining) ; tier Pro gratuit/manuel ; retirer 3 colonnes DB via migration.

## Global Constraints

- Windows : python du venv — `.venv/Scripts/python.exe` (Git Bash) depuis la racine.
- NE PAS lancer la suite `tests/api` complète en local (mass-fail sans backend d'inférence) — fichiers ciblés ; validation large via `-m "not integration"`.
- Namespace nu (tripwire actif) : imports `animetix.*`/`core.*`, jamais `backend.*`.
- Ordre impératif : repurposer/retirer tout code référençant `stripe_customer_id`/`stripe_subscription_id`/`stripe_subscription_item_id` AVANT de retirer les colonnes (Task 2), sinon `makemigrations`/le modèle cassent.
- CONSERVER volontairement : `backend/core/utils/scrubbing.py` (regex de masquage des clés Stripe dans les logs) et `BX_PRICE_USD_NET` dans `berrix_economy.py` (ancre du calcul de marge). NE PAS retirer le champ `Profile.tier` (concept free/pro conservé).
- Le working tree contient du travail frontend concurrent de l'utilisateur (i18n) — `git add` par chemins explicites, jamais `-A`.
- Branche : `chore/remove-stripe` (créée en Task 1). Ne jamais toucher/pusher `main`. Pre-commit hooks actifs ; jamais `--no-verify` (mypy local cassé → `SKIP=mypy` attendu, CI l'applique).

---

### Task 1: Backend — retirer les endpoints de paiement + service + reporting d'usage

**Files:**
- Modify: `backend/api/animetix/api/developer.py` (retirer 3 vues Stripe, repurposer le mock, nettoyer imports)
- Modify: `backend/adapters/persistence/django_usage_adapter.py:45-60` (retirer le bloc reporting Stripe)
- Delete: `backend/api/animetix/stripe_billing.py`
- Modify: `backend/api/animetix/urls/api.py` (retirer 3 routes, garder la route mock)
- Delete: `tests/adapters/test_billing_webhook.py`
- Modify: `tests/api/test_developer_coverage.py`, `tests/backend/test_developer_billing.py` (élaguer les cas Stripe)

**Interfaces:**
- Produces: `DeveloperSubscriptionMockView.post` pose `profile.tier = "pro"` sans aucun ID Stripe ; plus aucun import de `animetix.stripe_billing` ni référence à `StripeBillingService`/`PACKS` dans developer.py.

- [ ] **Step 1: Créer la branche**

```bash
git checkout -b chore/remove-stripe
```

- [ ] **Step 2: developer.py — repurposer le mock Pro (retirer les IDs Stripe)**

Dans `backend/api/animetix/api/developer.py`, remplacer le corps de `DeveloperSubscriptionMockView.post` :

```python
    def post(self, request):
        profile = request.user.profile

        profile.tier = "pro"
        profile.stripe_customer_id = f"cus_mock_{secrets.token_hex(8)}"
        profile.stripe_subscription_id = f"sub_mock_{secrets.token_hex(8)}"
        profile.stripe_subscription_item_id = f"si_mock_{secrets.token_hex(8)}"
        profile.save()

        return Response(
            {
                "status": "subscribed",
                "tier": profile.tier,
                "stripe_customer_id": profile.stripe_customer_id,
            }
        )
```

par :

```python
    def post(self, request):
        profile = request.user.profile
        profile.tier = "pro"
        profile.save(update_fields=["tier"])
        return Response({"status": "subscribed", "tier": profile.tier})
```

Et mettre à jour la docstring de la classe :

```python
class DeveloperSubscriptionMockView(APIView):
    """Active le tier Pro (gratuit/manuel — plus de facturation Stripe)."""
```

- [ ] **Step 3: developer.py — supprimer les 3 vues Stripe**

Supprimer intégralement les classes `CreateProSubscriptionCheckoutView` (l.133-153), `CreateBxCheckoutView` (l.182-214) et `StripeWebhookView` (l.217 jusqu'à la fin de la classe, ~l.335). NE PAS supprimer `DeveloperSubscriptionMockView` (repurposée au Step 2). Vérifier par lecture qu'aucune autre classe ne suit `StripeWebhookView`.

- [ ] **Step 4: developer.py — nettoyer les imports devenus inutiles**

En tête de `developer.py`, supprimer les imports qui ne servaient qu'aux vues retirées :
- `from animetix.stripe_billing import StripeBillingService`
- `from core.domain.services.berrix_economy import PACKS`
- `import secrets` (n'était utilisé que par le mock ; retirer après le Step 2)
- `from django.utils.decorators import method_decorator` et `from django.views.decorators.csrf import csrf_exempt` (n'étaient utilisés que par `@method_decorator(csrf_exempt...)` sur le webhook)

Faire tourner `ruff check` (Step 8) pour attraper tout import résiduel inutilisé (F401) ; ne retirer que ce que ruff signale + les 5 ci-dessus. Garder les imports encore utilisés par les vues conservées (`settings`, `Response`, `APIView`, `IsAuthenticated`, `Profile`, etc.).

- [ ] **Step 5: django_usage_adapter.py — retirer le reporting Stripe**

Dans `backend/adapters/persistence/django_usage_adapter.py`, supprimer le bloc « Automatic Stripe Reporting for Pro Developers » (l.~45-60) : le `if user_id:` qui importe `StripeBillingService` et appelle `report_usage`, ainsi que son `try/except`. Le tier Pro reste, mais son usage n'est plus reporté à Stripe. Vérifier que la méthode reste syntaxiquement correcte après retrait (le reste de `log_usage` continue).

- [ ] **Step 6: Supprimer le service Stripe**

```bash
git rm backend/api/animetix/stripe_billing.py
```

- [ ] **Step 7: urls/api.py — retirer les 3 routes Stripe (garder le mock)**

Dans `backend/api/animetix/urls/api.py`, supprimer :
- la route `billing/wallet/checkout/` → `api_views.CreateBxCheckoutView` (l.23-25) ;
- la route pointant vers `api_views.CreateProSubscriptionCheckoutView` (l.809) ;
- la route pointant vers `api_views.StripeWebhookView` (l.824).

CONSERVER la route vers `api_views.DeveloperSubscriptionMockView` (l.814). Retirer les `path(...)` complets (ouverture à fermeture, virgule incluse).

- [ ] **Step 8: Supprimer/élaguer les tests Stripe + lint**

```bash
git rm tests/adapters/test_billing_webhook.py
```

Dans `tests/api/test_developer_coverage.py` et `tests/backend/test_developer_billing.py`, retirer les tests qui exercent `CreateBxCheckoutView`, `CreateProSubscriptionCheckoutView`, `StripeWebhookView`, `StripeBillingService.report_usage`, ou qui asservissent le mock à des IDs Stripe (ex. `assert ... stripe_customer_id`). Adapter le test du mock à la nouvelle réponse `{"status": "subscribed", "tier": "pro"}` (sans `stripe_customer_id`). Lire chaque fichier, retirer les fonctions concernées entièrement (pas de demi-assertion).

```bash
.venv/Scripts/python.exe -m ruff check backend/api/animetix/api/developer.py backend/adapters/persistence/django_usage_adapter.py backend/api/animetix/urls/api.py
```

Attendu : ruff propre (aucun F401).

- [ ] **Step 9: Vérifier — collecte + tests ciblés + boot**

```bash
grep -rn "stripe_billing\|StripeBillingService\|StripeWebhook\|CreateBxCheckout\|CreateProSubscription" backend/ tests/ --include="*.py" | grep -v __pycache__
.venv/Scripts/python.exe backend/api/manage.py check
.venv/Scripts/python.exe -m pytest tests/api/test_developer_coverage.py tests/backend/test_developer_billing.py -q -m "not integration" 2>&1 | tail -3
.venv/Scripts/python.exe -m pytest tests/ -q --collect-only 2>&1 | tail -3
```

Attendu : grep vide ; `check` OK ; tests verts ; collecte saine.

- [ ] **Step 10: Commit**

```bash
git add backend/api/animetix/api/developer.py backend/adapters/persistence/django_usage_adapter.py backend/api/animetix/urls/api.py tests/api/test_developer_coverage.py tests/backend/test_developer_billing.py
git commit -m "refactor(billing): remove Stripe payment endpoints, webhook & usage reporting; Pro tier is now free/manual" -- backend/api/animetix/api/developer.py backend/adapters/persistence/django_usage_adapter.py backend/api/animetix/urls/api.py backend/api/animetix/stripe_billing.py tests/adapters/test_billing_webhook.py tests/api/test_developer_coverage.py tests/backend/test_developer_billing.py
```

---

### Task 2: Backend — retirer les 3 colonnes Stripe du modèle + migration

**Files:**
- Modify: `backend/api/animetix/models.py:152-157`
- Create: `backend/api/animetix/migrations/00NN_remove_stripe_fields.py` (généré)

**Interfaces:**
- Consumes: Task 1 (plus aucun code ne référence les champs Stripe).
- Produces: `Profile` sans `stripe_customer_id`/`stripe_subscription_id`/`stripe_subscription_item_id`.

- [ ] **Step 1: Vérifier zéro référence restante aux champs**

```bash
grep -rn "stripe_customer_id\|stripe_subscription_id\|stripe_subscription_item_id" backend/ tests/ --include="*.py" | grep -v __pycache__ | grep -v migrations/
```

Attendu : **vide**. Si un hit subsiste (hors migrations historiques), le corriger AVANT de continuer.

- [ ] **Step 2: models.py — supprimer les 3 champs**

Dans `backend/api/animetix/models.py`, supprimer les 3 déclarations (l.152-157) :

```python
    stripe_customer_id = models.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_subscription_item_id = models.CharField(
        max_length=255, null=True, blank=True
    )
```

Laisser intacts `wallet_balance`, `api_key_hash`, `tier` et le reste.

- [ ] **Step 3: Générer la migration**

```bash
.venv/Scripts/python.exe backend/api/manage.py makemigrations animetix 2>&1 | tail -6
```

Attendu : une migration `RemoveField` × 3 (customer_id, subscription_id, subscription_item_id). Noter son nom.

- [ ] **Step 4: Vérifier la migration à blanc (SQLite de test) + check**

```bash
.venv/Scripts/python.exe backend/api/manage.py migrate animetix --plan 2>&1 | tail -5
.venv/Scripts/python.exe backend/api/manage.py check
```

Attendu : la nouvelle migration apparaît au plan ; `check` OK.

- [ ] **Step 5: Commit**

```bash
git add backend/api/animetix/models.py backend/api/animetix/migrations/
git commit -m "refactor(db): drop the Profile Stripe columns (customer/subscription ids)"
```

Note : cette migration devra être **appliquée manuellement à la DB Neon en prod** (op séparée hors de ce plan).

---

### Task 3: Backend — retirer PACKS + settings STRIPE + dépendance

**Files:**
- Modify: `backend/core/domain/services/berrix_economy.py` (retirer `PACKS`)
- Modify: `tests/core/test_berrix_economy.py:71` (retirer la boucle PACKS)
- Modify: `backend/api/animetix_project/settings.py:650-656`
- Modify: `requirements.in`, `requirements.txt` (retrait `stripe` + relock)

**Interfaces:**
- Consumes: Task 1 (PACKS n'est plus importé par developer.py).

- [ ] **Step 1: berrix_economy.py — supprimer PACKS**

Supprimer le dict `PACKS: dict[str, dict] = { ... }` (à partir de `backend/core/domain/services/berrix_economy.py:147` jusqu'à sa `}` fermante). C'est la définition des packs *achetables* — sans achat, il est mort. NE PAS toucher `BX_PRICE_USD_NET`, `FEATURE_BX_COSTS`, `FEATURE_COMPUTE_USD`, `bx_cost_for_usd`, `ad_reward_bx`, `MINING_REWARD_BX`.

- [ ] **Step 2: test_berrix_economy.py — retirer le test PACKS**

Dans `tests/core/test_berrix_economy.py`, retirer la fonction de test qui itère `econ.PACKS.items()` (autour de l.71) — la supprimer entièrement (elle valide la marge des packs, qui n'existent plus).

- [ ] **Step 3: settings.py — retirer les clés STRIPE**

Supprimer le bloc `settings.py:650-656` :

```python
# --- STRIPE BILLING CONFIGURATION ---
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default=None)
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default=None)
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default=None)
STRIPE_USE_METERS = env.bool("STRIPE_USE_METERS", default=True)
STRIPE_METER_EVENT_NAME = env("STRIPE_METER_EVENT_NAME", default="rag_api_requests")
STRIPE_PRO_PRICE_ID = env("STRIPE_PRO_PRICE_ID", default="price_pro_metered")
```

(Vérifier au passage qu'aucune autre ligne de settings ne lit `STRIPE_PRO_API_PRICE_ID` — elle était lue par la vue supprimée en Task 1 ; sinon rien à faire.)

- [ ] **Step 4: Retirer la dépendance stripe + relock**

Dans `requirements.in`, supprimer la ligne `stripe==15.2.0`. Puis :

```bash
.venv/Scripts/python.exe -m piptools compile --allow-unsafe --output-file=requirements.txt --strip-extras requirements.in
git diff requirements.txt | grep -E "^[+-][a-z]"
```

Attendu : le diff ne retire que `stripe==...` (et ses éventuels orphelins transitifs). Si d'autres pins bougent, `git checkout -- requirements.txt` et investiguer.

- [ ] **Step 5: Vérifier + commit**

```bash
grep -rn "STRIPE_\|import stripe\|PACKS" backend/ tests/ --include="*.py" | grep -v __pycache__ | grep -v migrations/ | grep -v scrubbing.py
.venv/Scripts/python.exe -m pytest tests/core/test_berrix_economy.py -q
```

Attendu : grep vide (hors scrubbing/migrations) ; berrix tests verts.

```bash
git add backend/core/domain/services/berrix_economy.py tests/core/test_berrix_economy.py backend/api/animetix_project/settings.py requirements.in requirements.txt
git commit -m "chore(billing): drop purchasable PACKS, STRIPE settings and the stripe dependency"
```

---

### Task 4: Frontend — retirer l'UI d'achat morte + commentaire périmé + types

**Files:**
- Delete: `frontend/src/features/billing/components/NexusGatewayModal.tsx`
- Delete: `frontend/src/features/billing/components/__tests__/NexusGatewayModal.test.tsx`
- Modify: `frontend/src/pages/billing/PowerStationPage.tsx` (commentaire périmé)
- Modify: `frontend/src/types/api.d.ts` (types Stripe générés — régénérés)

**Interfaces:**
- Consumes: Task 1-3 (endpoints Stripe retirés côté backend).

- [ ] **Step 1: Confirmer que NexusGatewayModal est mort**

```bash
grep -rn "NexusGatewayModal" frontend/src --include="*.tsx" --include="*.ts" | grep -v "NexusGatewayModal.tsx" | grep -v "NexusGatewayModal.test"
```

Attendu : **vide** (seul son test le rend). Si un rendu de production apparaît, STOP et signaler.

- [ ] **Step 2: Supprimer le composant mort + son test**

```bash
git rm frontend/src/features/billing/components/NexusGatewayModal.tsx frontend/src/features/billing/components/__tests__/NexusGatewayModal.test.tsx
```

- [ ] **Step 3: PowerStationPage — corriger le commentaire périmé**

Dans `frontend/src/pages/billing/PowerStationPage.tsx`, remplacer le commentaire `{/* Left Column: Berrix Card & Stripe Packs */}` par `{/* Left Column: Berrix Wallet Card */}` (la fonctionnalité est déjà 100 % gagner-via-pub/mining, aucun code à retirer).

- [ ] **Step 4: Régénérer les types OpenAPI (retirer les endpoints Stripe de api.d.ts)**

```bash
.venv/Scripts/python.exe backend/api/manage.py spectacular --file schema.yaml 2>&1 | tail -3
cd frontend && npx openapi-typescript ../schema.yaml -o src/types/api.d.ts 2>&1 | tail -3 && cd ..
git diff --stat frontend/src/types/api.d.ts schema.yaml
```

Attendu : `api.d.ts` et `schema.yaml` régénérés sans les 3 chemins Stripe (`/billing/wallet/checkout/`, `/developer/webhook/stripe/`, la Pro subscription). Si `openapi-typescript` n'est pas installé, consulter `sync-api.bat` pour la commande exacte du projet ; en dernier recours, retirer manuellement de `api.d.ts` les blocs de chemins Stripe (l.460-470, 987, 995-1008, 4484) et noter la divergence.

- [ ] **Step 5: Vérifier build + lint frontend**

```bash
cd frontend && npm run type-check 2>&1 | tail -5 && npx eslint src/pages/billing/PowerStationPage.tsx 2>&1 | tail -3 && npm run build 2>&1 | tail -4 && cd ..
```

Attendu : type-check propre (les refs aux endpoints Stripe supprimés ne doivent plus être appelées — NexusGatewayModal parti) ; eslint propre ; build OK.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/billing/PowerStationPage.tsx frontend/src/types/api.d.ts schema.yaml
git commit -m "refactor(billing-ui): remove the dead Stripe purchase modal + stale comment; regen API types" -- frontend/src/features/billing/components/NexusGatewayModal.tsx "frontend/src/features/billing/components/__tests__/NexusGatewayModal.test.tsx" frontend/src/pages/billing/PowerStationPage.tsx frontend/src/types/api.d.ts schema.yaml
```

---

### Task 5: Vérification finale + clôture

**Files:**
- Modify: `docs/HISTORY.md` (entrée)

- [ ] **Step 1: Grep global zéro-Stripe (hors résidus autorisés)**

```bash
grep -rniE "stripe" backend/ tests/ frontend/src/ --include="*.py" --include="*.ts" --include="*.tsx" | grep -viE "scrubbing.py|migrations/|__pycache__"
```

Attendu : **vide**. (scrubbing.py garde la regex ; les migrations historiques gardent l'historique.)

- [ ] **Step 2: Suite backend CI-équivalente**

```bash
.venv/Scripts/python.exe -m pytest -m "not integration" --cov=backend --cov-report=term -q 2>&1 | tail -4
```

Attendu : 0 failed ; couverture ≥ 75 %. Si des échecs apparaissent, les quoter et reporter DONE_WITH_CONCERNS.

- [ ] **Step 3: HISTORY — entrée de clôture**

Insérer après la ligne d'intro de `docs/HISTORY.md`, avant la première section datée :

```markdown
## [2026-07-07] Session: Removed all Stripe payment features

Purchasing Berrix (or a Pro subscription) via Stripe is no longer offered, so the payment code was removed end to end: the `CreateBxCheckoutView` / `CreateProSubscriptionCheckoutView` / `StripeWebhookView` endpoints, the `StripeBillingService`, the metered usage reporting in `django_usage_adapter`, the purchasable `PACKS`, the six `STRIPE_*` settings, the `stripe` dependency, and the three `Profile` Stripe columns (dropped via migration — to be applied to the Neon prod DB manually). The front had no live purchase path: `NexusGatewayModal` (the only priced component) was dead (test-only) and was deleted; PowerStation/Pricing already run on earned Berrix (rewarded ads + mining) and sponsor/donation. The `tier` (free/pro) concept stays: `DeveloperSubscriptionMockView` now simply sets `tier="pro"` for free. The Stripe-key log-scrubbing regex was intentionally kept.
```

- [ ] **Step 4: Commit**

```bash
git add docs/HISTORY.md
git commit -m "docs: record the Stripe removal"
```
