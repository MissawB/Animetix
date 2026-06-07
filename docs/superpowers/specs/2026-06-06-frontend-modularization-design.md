# Design Doc: Modularisation Frontend (`src/pages/`)

**Date:** 2026-06-06  
**Status:** Approved  
**Topic:** Isoler les vues (Pages) des composants de fonctionnalités et de la logique métier (`features/`).

## 1. Objectifs
- **Séparation des préoccupations** : Les répertoires sous `features/` ne doivent contenir que des composants atomiques, des hooks, des services et des stores. Les composants qui représentent des routes complètes doivent être déplacés dans `pages/`.
- **Maintenabilité** : Faciliter la navigation dans le projet en séparant la structure de navigation (Pages) de l'implémentation des fonctionnalités.
- **Conformité** : Aligner l'architecture sur les standards modernes de React (Pattern "Features vs Pages").

## 2. Architecture Cible

Le projet utilisera désormais une structure à deux niveaux pour les composants :

```text
src/
├── features/          # Logique métier et composants réutilisables
│   ├── games/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── ...
├── pages/             # Vues de niveau route (Entry points)
│   ├── games/
│   │   ├── AkinetixPage.tsx
│   │   └── GamesHubPage.tsx
│   ├── social/
│   │   └── ProfilePage.tsx
│   └── ...
```

## 3. Stratégie de Migration

### A. Création de la Structure `src/pages/`
Création des sous-répertoires miroirs de `features/` :
- `admin`, `auth`, `billing`, `companion`, `explore`, `games`, `graph`, `home`, `labs`, `media`, `search`, `social`, `utils`.

### B. Déplacement des fichiers
Tous les fichiers terminant par `Page.tsx` (ou identifiés comme des vues de route comme `ClubDashboard.tsx` ou `UndercoverRoom.tsx`) seront déplacés.
- **Tests** : Les répertoires `__tests__` associés contenant les tests de ces pages seront également déplacés vers `src/pages/<feature>/__tests__/`.

### C. Refactorisation des Imports
1. **Imports Internes** : Dans les pages déplacées, les imports relatifs vers `./components`, `./hooks`, etc., doivent être mis à jour vers `../../features/<feature>/components`, etc.
2. **Routes** : Dans les fichiers `src/features/*/routes/*Routes.tsx`, les chemins d'importation des composants `lazy()` doivent être mis à jour pour pointer vers `src/pages/`.

## 4. Plan de Validation
- Exécuter `npm run tsc` pour vérifier l'intégrité des types et des chemins d'importation.
- Exécuter la suite de tests unitaires (`npm run test`) pour s'assurer que les tests déplacés fonctionnent toujours.
- Vérification manuelle de la navigation principale pour confirmer que le Lazy Loading fonctionne toujours correctement.
