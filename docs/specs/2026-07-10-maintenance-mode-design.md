# Mode maintenance — design

**Date** : 2026-07-10 · **Statut** : approuvé (conversation)

## Objectif

Un mode maintenance **global**, activable en 2 clics depuis l'admin Django, qui
remplace toute l'app par une page dédiée stylée pour les visiteurs, tout en
laissant les admins (staff) naviguer normalement.

## Décisions de cadrage

- **Portée** : site entier (pas de maintenance par fonctionnalité).
- **Activation** : flag en base de données, togglable depuis `/admin/`
  (effet immédiat, aucun redéploiement — contrainte : les env-updates Cloud Run
  réutilisent l'ancienne image).

## Backend

### Modèle `SiteConfiguration` (singleton, pk=1)

| Champ | Type | Défaut |
| --- | --- | --- |
| `maintenance_mode` | Boolean | `False` |
| `maintenance_message` | Text (blank) | `""` |
| `maintenance_until` | DateTime (null/blank) | `None` |

Accès via `SiteConfiguration.get_solo()` (`get_or_create(pk=1)`). Enregistré
dans l'admin Django (« Configuration du site »), ajout/suppression désactivés.

### Endpoint `GET /api/v1/config/`

La route existait déjà (`ConfigView`, consommée par `getAppConfig()` côté
frontend) mais ne renvoyait ni `version` ni `maintenance_mode` : elle est
**étendue** plutôt que dupliquée. `AllowAny`, throttle `CpuGameThrottle`
(60/min, minute-seulement : elle est pollée pendant la maintenance et ne doit
jamais consommer le day-cap anonyme ; `[]` est banni par la politique
throttles du repo et refusé par mypy). Répond le type `AppConfig` déjà
déclaré côté frontend :

```json
{
  "version": "<AI_MODEL_VERSION>",
  "maintenance_mode": false,
  "maintenance_message": "",
  "maintenance_until": null,
  "features": {}
}
```

### Middleware `MaintenanceModeMiddleware`

Quand le flag est ON, toute requête `/api/…` reçoit **503**
`{"detail": …, "maintenance": true}`, avec exemptions :

- `/api/v1/config/` (le poll de sortie doit passer) ;
- `/admin/` et hors `/api/` (SPA, statiques) — le gating UX est fait côté front ;
- health checks (`/api/health…`) ;
- **staff** : session Django (admin connecté) ou token Firebase valide dont
  l'utilisateur est `is_staff` (l'authentification DRF n'est tentée que si le
  mode est ON — coût nul en fonctionnement normal).

Le flag est lu en base à chaque requête `/api/` via le singleton (une requête
SQL par hit, indexée par pk — acceptable ; pas de cache pour garder l'effet
immédiat du toggle).

## Frontend

- **`MaintenancePage`** : plein écran, univers visuel de la 404 (« Dimension
  inconnue ») — sombre, manga-font, i18n FR/EN. Affiche le message custom et
  l'heure de retour estimée si renseignés + bouton « Réessayer ».
- **Garde applicative** : au boot, query `['app-config']` sur
  `/api/v1/config/`. Si `maintenance_mode` et utilisateur non-staff → la page
  remplace toutes les routes. `refetchInterval` 30 s uniquement pendant la
  maintenance (sortie sans F5).
- **Bascule en session** : `apiClient` détecte un 503 `maintenance: true` et
  émet l'événement `animetix:maintenance` ; la garde refetch la config et
  bascule immédiatement.
- **Staff** : pas de blocage, bandeau jaune fixe « Mode maintenance actif ».

## Tests

- Backend : endpoint config (payload, flag ON/OFF) ; middleware (503 sur
  `/api/`, exemptions config/admin, bypass staff session, passthrough OFF).
- Frontend : rendu `MaintenancePage` (message/échéance), garde (bascule
  maintenance vs routes normales).

## Hors périmètre

Maintenance par fonctionnalité, page statique Cloudflare (backend down),
planification automatique (le champ `maintenance_until` est purement
informatif).
