# Design — Consentement RGPD (CMP) + désactivation des pubs

**Date** : 2026-07-04
**Statut** : approuvé (brainstorming) → à planifier
**Périmètre frontend** : `frontend/` (React 19 + Vite), prod GCP Cloud Run, utilisateurs UE.

## Contexte & problème

L'infrastructure publicitaire existe déjà :
- `frontend/src/features/billing/components/AdSlot.tsx` — unité Google AdSense réelle (env `VITE_ADSENSE_CLIENT`, `VITE_ADSENSE_SLOT_GAME`, `VITE_ADSENSE_SLOT_SIDEBAR`) avec fallback placeholder ; couplée au **minage passif de Berrix (Bx)** via `usePassiveMiningStore` (`registerAd`/`unregisterAd`).
- Utilisée dans `SidebarDrawer.tsx` (slot sidebar) et `features/billing/components/GameLayout.tsx` (slot jeu).
- `PassiveAdMiner.tsx` : minage effectif si `user` connecté **ET** `isEnabled` **ET** `adSlotsVisible > 0`, POST `/api/v1/billing/wallet/mine/` toutes les 180 s (crédite de vrais Bx côté serveur).

**Deux manques** :
1. **Aucun CMP / gestion du consentement RGPD** (aucune trace de TCF, Consent Mode, Funding Choices, CMP tiers). Servir de l'AdSense à des utilisateurs UE sans CMP certifié Google viole le RGPD **et** la politique Google (CMP certifié obligatoire depuis janv. 2024, même pour les pubs non personnalisées).
2. **Pas de moyen pour l'utilisateur de désactiver les pubs** depuis les paramètres.

## Décisions (issues du brainstorming)

| Sujet | Décision |
|---|---|
| CMP | **Google Funding Choices** (Privacy & messaging AdSense) — gratuit, certifié Google + IAB TCF v2.2 |
| Désactiver les pubs → minage | **Pas de pub = pas de minage** (couplage naturel via `adSlotsVisible`) |
| Persistance de la préférence | **Client / localStorage** (store zustand, calqué sur `passiveMiningStore`) ; couvre anonymes + connectés |
| Nouvelles bannières | **Hors périmètre** (non demandé pour l'instant) |
| Sync compte / backend | **Hors périmètre** (YAGNI) |
| Gating premium ad-free | **Hors périmètre** |

## Architecture

### 1. Couche consentement (CMP)

**Consent Mode v2 bootstrap** — snippet exécuté **avant** le chargement d'`adsbygoogle.js`, dans `frontend/index.html` (dans `<head>`, avant tout script d'app) :

```html
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){ dataLayer.push(arguments); }
  gtag('consent', 'default', {
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    analytics_storage: 'denied',
    region: ['EEA', 'GB'],        // périmètre UE/UK ; hors UE non contraint
    wait_for_update: 500
  });
</script>
```

**Google Funding Choices** = le CMP certifié, **activé côté console AdSense** (« Confidentialité et messages » → message RGPD ciblant EEE/UK). C'est une **étape ops**, pas du code. Une fois activé, l'`adsbygoogle.js` déjà chargé par `AdSlot` :
- affiche automatiquement le bandeau de consentement aux visiteurs EEE/UK ;
- met à jour le Consent Mode selon le choix ;
- sert des pubs **personnalisées** (consentement) ou **non personnalisées** (refus) — légal des deux côtés.

Aucun SDK tiers à charger.

### 2. Store de préférence pub

Nouveau fichier `frontend/src/store/adPreferenceStore.ts` (zustand + localStorage, même style que `passiveMiningStore.ts`) :

```ts
interface AdPreferenceState {
  adsEnabled: boolean;            // défaut true
  setAdsEnabled: (enabled: boolean) => void;
}
```
- Clé localStorage : `ads_enabled`. Défaut `true` si absente (`localStorage.getItem('ads_enabled') !== 'false'`).
- `setAdsEnabled` persiste dans localStorage et met à jour l'état.

### 3. `AdSlot` — gating

`AdSlot` lit `adsEnabled` du store. **Si `adsEnabled === false` → retourne `null`** en tout début de composant :
- pas de DOM rendu (ni pub réelle ni placeholder) ;
- l'`useEffect` d'impression/mining ne s'exécute pas → **pas de `registerAd()`, pas de `logAdEvent('impression', …)`, pas de push AdSense**.

Conséquence : `adSlotsVisible` reste à 0 → `PassiveAdMiner` passe `OFFLINE` et **n'appelle plus `/wallet/mine/`**. Le couplage « pas de pub = pas de minage » est obtenu **sans changement backend**.

Le consentement (personnalisé vs non) est géré par Google au niveau du serving (Consent Mode + Funding Choices) ; `AdSlot` n'a pas à gater sur le consentement pour la légalité.

### 4. UI paramètres — `SettingsDrawer`

Dans `frontend/src/components/layout/SettingsDrawer.tsx` (le panneau paramètres qui contient déjà « Apparence » et « Langue »), nouvelle section **« Publicités »** :
- Un **toggle on/off** lié à `adsEnabled` (`setAdsEnabled`).
- Texte d'aide : *« Désactiver les pubs met aussi en pause le minage passif de Bx. »*
- Un lien **« Gérer mon consentement »** qui ré-affiche le bandeau Funding Choices via `window.googlefc?.showRevocationMessage?.()` (no-op silencieux si `googlefc` absent, ex. hors UE / script non chargé).

## Flux de données

1. **Boot** → Consent Mode defaults `denied` → `adsbygoogle.js` chargé (par le 1er `AdSlot` monté) → Funding Choices affiche le bandeau (EEE/UK) → choix utilisateur → Google met à jour le consent → pubs servies en conséquence.
2. **Toggle off** → `adPreferenceStore.adsEnabled = false` → tous les `AdSlot` rendent `null` → `adSlotsVisible = 0` → `PassiveAdMiner` OFFLINE → plus de crédit Bx.
3. **Toggle on** → `AdSlot` re-montent → mining reprend (si connecté).

## Gestion des erreurs / cas limites

- **Refus de consentement** → pubs non personnalisées (Consent Mode) ; les `AdSlot` restent montés, le minage peut continuer (une NPA rapporte quand même). Acceptable.
- **Adblocker / `adsbygoogle` bloqué** → pas de pub réelle ; le minage ne progresse pas faute d'ad servie. Comportement inchangé.
- **`googlefc` absent** (hors UE, script non chargé) → « Gérer mon consentement » est un no-op silencieux.
- **SSR / pas de `document`** → gardes déjà présentes dans `AdSlot`.

## Tests

- `adPreferenceStore` : défaut `true` ; `setAdsEnabled(false)` persiste `'false'` dans localStorage et repasse à `true` correctement (calqué sur `passiveMiningStore.test.ts`).
- `AdSlot` : quand `adsEnabled === false`, rend `null` **et** n'appelle ni `registerAd` ni `logAdEvent` (mock des stores/service).
- `SettingsDrawer` : le toggle « Publicités » appelle `setAdsEnabled` et reflète l'état du store.
- (Optionnel) présence du snippet Consent Mode dans `index.html`.

## Hors périmètre / non-objectifs

- Nouvelles bannières / emplacements pub supplémentaires.
- Synchronisation de la préférence sur le compte (backend).
- Gating « ad-free » réservé au premium.
- Le trou de confiance de l'endpoint `/api/v1/billing/wallet/mine/` (crédite sans preuve serveur qu'une pub a été vue) : **préexistant**, noté, non traité ici.

## Étapes ops (hors code, à faire par le propriétaire)

1. Console AdSense → **Confidentialité et messages** → créer un message **RGPD** certifié (Funding Choices), ciblant **EEE + Royaume-Uni**, le publier.
2. Vérifier que `VITE_ADSENSE_CLIENT` / `VITE_ADSENSE_SLOT_*` sont bien renseignés en prod (déjà présents dans `.env.production`).
