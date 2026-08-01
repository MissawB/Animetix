# TODO — Améliorations du projet Animetix

> Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

## 🔴 Critiques

_Aucun item ouvert._

## 🟠 Élevés

- [/] **Fine-tune otaku — dataset assaini ✅ (PR #87) ; reste le réentraînement (bloqué GPU)** _(2026-07-13→17 ; détail cf. HISTORY 2026-07-17)_
  - **Reste** : réentraîner sur le dataset propre (`MissawB/otaku-expert-dataset`) **dès qu'un GPU est dispo** (cf. dette GPU), puis re-servir via `LLM_MODEL_NAME=otaku-qwen:7b` (déjà baké, aucun rebuild).

- [/] **Index visuel : phase 2 — `character_ccip_space` partiel, run GPU différé (mode économie)** _(phase 1 2026-07-14 ; run tenté 2026-07-17 ; facturation rétablie 2026-07-22, cf. HISTORY)_
  - Facturation GCP **rétablie le 2026-07-22**, mais le run GPU est **différé volontairement** : période de réduction des frais pendant la validation AdSense (sensors en pause, Redis migré Upstash, connecteur VPC retiré — cf. HISTORY 2026-07-22). Les ~3,5 h de vecteurs déjà écrits sont préservés (job reprenable).
  - **Reste (quand le mode économie sera levé)** : 1) vérifier/relever le plafond de budget (50 € conseillé) ; 2) Brain `/health` = 200 ; 3) re-exécuter **par chunks** (`--limit N`) jusqu'aux ~35 000 ; 4) recherche perso ne renvoie plus 503.

- [ ] **Monétisation « regarde une pub → Bx » : archi conforme AdSense (option A)** _(2026-08-01)_
  - **Contexte** : la mécanique « Active Mining / recharge » est le cœur du site, mais récompenser un utilisateur pour visionner une pub est **interdit par AdSense** (pas de format rewarded côté web ; incentivé = refus). En attendant, l'**option B est en place** (2026-08-01) : le vocabulaire « pub / watch ad » a été retiré de l'UI (ledger relabellé, identifiants renommés), la récompense est présentée comme un **engagement/énergie** non lié à une pub, et le flux est un simple minuteur (aucune pub AdSense n'est incentivée). Les `AdSlot` restent du **display passif** (games/pricing) — conforme.
  - **Scaffolding en place (2026-08-01)** : archi conforme, agnostique au réseau. Front = `features/billing/rewarded/rewardedAdProvider.ts` (`RewardedAdProvider` + stub d'engagement + `getRewardedAdProvider()` sur `VITE_REWARDED_PROVIDER`) ; la recharge passe par `showRewarded()` (jamais par un `AdSlot`). Back = `core/domain/services/rewarded_ad_verifier.py` (`verify_rewarded_ad`) appelé par `WalletWatchAdView` : **mode stub** = crédit sans jeton (dev) ; **réseau réel configuré** = jeton SSV valide OBLIGATOIRE, sinon 402 (fail-closed). Doc : `docs/REWARDED_ADS.md`.
  - **Bloqué par / séquence** : le compte **Google Ad Manager** (rewarded) exige un **compte éditeur Google approuvé** → **AdSense doit être validé d'abord** (confirmé 2026-08-01 : « je ne peux faire le compte qu'une fois qu'AdSense est validée »). Ordre : 1) la re-review AdSense passe → 2) ouvrir le compte rewarded → 3) brancher le provider réel + SSV dans le scaffolding déjà prêt. **En attendant, la prod tourne sur l'option B** (révision `animetix-web-00065`, commit `1b0845bc`) et le scaffolding reste en **stub** (comportement identique à B, AdSense-safe).
  - **Reste (une fois AdSense validé + compte ouvert)** : 1) ouvrir le compte **rewarded dédié** (Google Ad Manager rewarded units web, ou SSP tiers) — action externe ; 2) implémenter le provider réel (`showRewarded()` charge le SDK, affiche la pub, renvoie le jeton signé) + l'exposer dans `getRewardedAdProvider()` ; 3) implémenter la vérification de signature dans `verify_rewarded_ad` (SSV) ; 4) `VITE_REWARDED_PROVIDER` + `REWARDED_ADS_PROVIDER` + IDs/secret en env ; 5) re-caler `ad_reward_bx()` sur le revenu réel du réseau.
  - **Ne jamais** : câbler une pub AdSense derrière le bouton de recharge ; ré-introduire le libellé « pub / watch ad » près des `AdSlot` (cf. HISTORY 2026-07-24) ; **définir `REWARDED_ADS_PROVIDER` en prod tant que le vrai réseau + la vérif SSV ne sont pas branchés** — sinon le back exige un jeton et renvoie 402 (recharge bloquée). Le mode stub doit rester actif jusque-là.

## 🟡 Moyens

### Manga / Suwayomi _(analyse 2026-07-27)_

> Le backend manga d'Animetix **EST Suwayomi** (même écosystème Tachiyomi/Mihon) : la plomberie GraphQL de ces features existe déjà côté serveur, il s'agit surtout de l'exposer (adaptateur + endpoint + UI). Vérifié sur le serveur local.

- [x] **Lecture : état lu/non-lu + « Reprendre la lecture »** — Suwayomi expose par chapitre `isRead`, `lastPageRead`, `lastReadAt`, `pageCount`. Afficher pastille lu/non-lu + progression dans la popup de détail, bouton « Marquer comme lu » (`updateChapters`) et **« Reprendre au chapitre X »** ; faire remonter la progression depuis le lecteur (`updateChapter{isRead,lastPageRead}`). *(le manque le plus visible pour un lecteur — meilleur rapport valeur/effort)* _(2026-08-01 : plan complet livré en 10 tâches — modèle `MangaReadingProgress`, endpoints progress/mark-read/sync, bandeau « Reprendre » sur la fiche œuvre, progression par chapitres sur les cartes de la bibliothèque)_
- [ ] **Suivis de la progression de lecture** _(ouverts 2026-08-01 à la fusion, aucun n'est bloquant)_
  - Hors-ligne, la requête `/progress/` passe en `fetchStatus: 'paused'` (React Query, `networkMode: 'online'`) : `isFresh` ne devient jamais vrai, donc un chapitre téléchargé ne reprend plus **et** n'enregistre plus. Correctif d'une ligne : accepter `paused` dans `useMangaProgress`.
  - `dirtyMediaId` est posé dans le `.then()` de l'écriture : quitter le lecteur pendant le `PUT` en vol perd l'invalidation. Le poser avant l'appel.
  - Le `staleTime: 0` épinglé sur la requête de progression réactive `refetchOnWindowFocus` : un aller-retour alt-tab coûte un `GET` sur les trois écrans consommateurs.
  - Écriture-écho au montage : rouvrir un chapitre repris émet un `PUT` redondant **et** une mutation Suwayomi. Le remède touche `isResolved`, la garde qui vient d'être stabilisée — à traiter isolément.
- [x] **Trackers AniList / MAL (liaison explicite + sync de progression)** — _(2026-08-01)_ La synchro existait déjà mais devinait l'œuvre distante par recherche de titre à chaque envoi (mauvaise œuvre mise à jour sur un titre ambigu) et écrivait la progression en absolu (relire un vieux chapitre rabaissait le compte distant). Remplacé par une liaison explicite : modèle `MangaTrackerLink`, port `TrackerPort` + un adaptateur par tracker, service qui propose puis confirme, et une poussée qui ne part que sur liaison **confirmée** et seulement si elle dépasse le compteur distant mémorisé. Encart sur la fiche œuvre + liste des liaisons dans le panneau profil.
  - **Écarté volontairement** : les 4 autres trackers (Kitsu, MangaUpdates, Shikimori, Bangumi) et la couche trackers de Suwayomi — Suwayomi est injoignable en prod (`SUWAYOMI_URL` = `127.0.0.1`), son état est mono-utilisateur, et son « OAuth » est un copier-coller de jeton comme le formulaire actuel (vérifié : sur 6 trackers, 4 ont une `authUrl`, dont 2 redirigent vers une page tierce).
  - **Suivis ouverts** : `confirm` n'exige pas que le tracker soit connecté (liaison orpheline créable, sans effet) ; le message `"No trackers connected."` sort aussi quand des comptes sont connectés sans liaison confirmée ; `TrackerLinkListView` fait un N+1 sur `link.manga` ; `"aucune correspondance"` n'est pas mémorisé, donc la recherche externe repart à chaque affichage de la fiche.
- [ ] **Catégories de bibliothèque personnalisées** — au-delà des 3 statuts (reading/completed/plan_to_read). CRUD complet côté Suwayomi (`createCategory`, `updateMangaCategories`, `updateCategoryOrder`).
- [ ] **Filtres de source (genre / statut / tri)** — `source.filters` renvoie des `GroupFilter` acceptés par `fetchSourceManga(filters:…)`. Navigation par genre/statut au lieu de populaire/recherche uniquement.

## 🟢 Faibles

### Manga / Suwayomi — inspiré de Mihon _(analyse 2026-07-27, Tier 2/3)_

- [ ] **Téléchargement hors-ligne côté serveur** — file d'attente Suwayomi (`enqueueChapterDownload`, `startDownloader`, `downloadStatus`, `deleteDownloadedChapter`), à combiner avec la bibliothèque offline PWA existante.
- [ ] **Recherche multi-sources (global search)** — chercher un titre dans **toutes** les sources installées d'un coup (aujourd'hui : une source à la fois).
- [ ] **Signets de chapitres** — `isBookmarked` par chapitre.
- [ ] **Backup / restore de la bibliothèque Suwayomi** — `createBackup` / `restoreBackup`.
- [ ] **Migration entre sources** — déplacer une œuvre d'une source morte vers une autre.
- [ ] **Modes de lecture** — directions RTL/LTR, webtoon/vertical, filtre couleur (polissage du lecteur).
