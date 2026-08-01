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

## 🟡 Moyens

### Manga / Suwayomi _(analyse 2026-07-27)_

> Le backend manga d'Animetix **EST Suwayomi** (même écosystème Tachiyomi/Mihon) : la plomberie GraphQL de ces features existe déjà côté serveur, il s'agit surtout de l'exposer (adaptateur + endpoint + UI). Vérifié sur le serveur local.

- [x] **Lecture : état lu/non-lu + « Reprendre la lecture »** — Suwayomi expose par chapitre `isRead`, `lastPageRead`, `lastReadAt`, `pageCount`. Afficher pastille lu/non-lu + progression dans la popup de détail, bouton « Marquer comme lu » (`updateChapters`) et **« Reprendre au chapitre X »** ; faire remonter la progression depuis le lecteur (`updateChapter{isRead,lastPageRead}`). *(le manque le plus visible pour un lecteur — meilleur rapport valeur/effort)* _(2026-08-01 : plan complet livré en 10 tâches — modèle `MangaReadingProgress`, endpoints progress/mark-read/sync, bandeau « Reprendre » sur la fiche œuvre, progression par chapitres sur les cartes de la bibliothèque)_
- [ ] **Trackers AniList / MAL / … (sync de progression)** — Suwayomi expose 6 trackers (MyAnimeList, AniList, Kitsu, MangaUpdates, Shikimori, Bangumi) + `bindTrack` / `trackProgress` / `updateTrack` / `loginTrackerOAuth`. Lier une œuvre à AniList/MAL et synchroniser la progression ; relier fiche Suwayomi ↔ catalogue Animetix (déjà AniList). *(feature phare de Mihon)*
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
