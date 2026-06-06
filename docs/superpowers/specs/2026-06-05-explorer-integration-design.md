# Design Spec: Finalisation Intégration Explorer

**Date :** 2026-06-05
**Sujet :** Désorphelinisation de la page `/explore/` via l'intégration de recommandations personnalisées et l'amélioration des flux de navigation.

## 1. Objectifs
- Intégrer les recommandations personnalisées issues du modèle `UserRecommendation`.
- Faire de la page `/explore/` (Nexus) le point d'entrée principal pour la découverte de contenu.
- Améliorer la navigation contextuelle entre les pages de détails et l'explorateur.

## 2. Architecture Backend

### 2.1 API : `MediaExploreView`
- **Fichier :** `backend/api/animetix/api/explore.py`
- **Changements :**
    - Injecter `persistence.repository` (pour l'accès aux `UserRecommendation`).
    - Dans la méthode `get` :
        - Vérifier `request.user.is_authenticated`.
        - Si authentifié :
            - Récupérer les `UserRecommendation` liées à l'utilisateur (filtrées par `media_type`).
            - Charger les objets `MediaItem` correspondants.
            - Inclure une clé `recommendations` dans la réponse JSON.
        - Si anonyme :
            - Renvoyer une liste vide pour `recommendations` ou une sélection de "Staff Picks" (fallback).

### 2.2 Modèle de Données
- Utiliser le modèle `UserRecommendation` existant (`user`, `media_item`, `score`, `rank`).

## 3. Interface Frontend (React)

### 3.1 Page : `ExplorePage.tsx`
- **Fichier :** `frontend/src/features/explore/ExplorePage.tsx`
- **Modifications UI :**
    - Ajouter une section "Choisi pour vous" juste en dessous de la section Hero.
    - Utiliser le composant `MediaCard` existant pour afficher les items recommandés.
    - Afficher un badge discret "IA : SUGGESTION" sur les cartes de cette section pour renforcer la proposition de valeur IA.
    - Gérer l'état de chargement et l'absence de données (utilisateur anonyme).

### 3.2 Navigation & Routage
- **Page Détails :** `frontend/src/features/media/MediaDetailPage.tsx`
    - Changer le lien de retour pour pointer vers `/explore/` au lieu de `/`.
    - Harmoniser le label en "Retour au Nexus".
- **Composant Layout/Navbar :** Vérifier que tous les points d'entrée vers "Explore" sont cohérents.

## 4. Flux de Données
1. L'utilisateur accède à `/explore/`.
2. Le frontend appelle `GET /api/explore/?media_type=Anime`.
3. Le backend identifie l'utilisateur via JWT/Session.
4. Le backend combine les tendances globales (BigQuery/Cache) et les recommandations personnalisées (AlloyDB/PostgreSQL).
5. Le frontend affiche d'abord les recommandations personnalisées, puis les tendances et catégories.

## 5. Critères d'Acceptation
- [ ] Les utilisateurs connectés voient une ligne "Choisi pour vous" avec des items pertinents.
- [ ] Les utilisateurs anonymes ne voient pas d'erreur, mais une section alternative ou rien.
- [ ] Le bouton "Retour" de la page détails redirige vers `/explore/`.
- [ ] La navigation est fluide et respecte le design "Manga/Futuriste" existant.
