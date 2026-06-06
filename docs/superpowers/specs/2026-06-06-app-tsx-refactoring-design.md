# Design Doc: Refactorisation de `App.tsx` (Composants Atomiques)

**Date:** 2026-06-06  
**Status:** Approved  
**Topic:** Découper le fichier monolithique `frontend/src/App.tsx` en composants atomiques et services/data dédiés.

## 1. Objectifs
- Réduire la taille et la complexité du fichier `App.tsx` (actuellement ~418 lignes, 21 KB).
- Séparer la logique des données (configurations des modes de jeu) de la couche de présentation.
- Créer des composants de présentation isolés, réutilisables et testables.
- Respecter le mandat `GEMINI.md` du frontend en créant des composants UI modulaires.

## 2. Architecture et Découpage

Le refactoring va introduire un nouveau domaine fonctionnel : `frontend/src/features/home/`.

### A. Extraction des Données
Fichier : `frontend/src/features/home/data/gameModes.ts`
- Contiendra les constantes statiques : `modesSolo`, `modesMulti`, et `modesCreative`.
- Exportera ces données pour être consommées par les composants d'interface.

### B. Composants Atomiques
Les composants suivants seront créés dans `frontend/src/features/home/components/` :

1. **`HomeNav.tsx`** :
   - Gère la barre de navigation intégrée au hero (bouton menu, logo, liens Défi Quotidien/Classement, et informations utilisateur).
   - Dépendances : `useUIStore`, `useAuthStore`, `useTranslation`.

2. **`HeroSection.tsx`** :
   - Gère l'affichage principal "ANIMETIX" et l'image du Hero avec `DynamicAuraWrapper`.
   - Dépendances : `useTranslation`.

3. **`SoloChallenges.tsx`** :
   - Itère sur la liste `modesSolo` et affiche les cartes de jeu (Akinetix, Classic, etc.).
   - Dépendances : `gameModes.ts`, `useTranslation`.

4. **`WorldBossBanner.tsx`** :
   - Extrait la bannière promotionnelle du "World Boss".
   - Dépendances : `useTranslation`.

5. **`MultiplayerModes.tsx`** :
   - Itère sur `modesMulti` pour l'affichage des modes "Entre Amis".
   - Dépendances : `gameModes.ts`, `useTranslation`.

6. **`CreativeForge.tsx`** :
   - Gère la section cinématique pour les modes "Creative Forge".
   - Dépendances : `gameModes.ts`, `useTranslation`.

7. **`SingularityLab.tsx`** :
   - Gère la section finale expérimentale "NIVEAU OMEGA".
   - Dépendances : `useTranslation`, icônes `Zap` et `ArrowRight`.

### C. Refactorisation de `App.tsx`
Le fichier `frontend/src/App.tsx` deviendra un simple orchestrateur qui importe et assemble ces composants.

```tsx
import React from 'react';
import { HomeNav } from './features/home/components/HomeNav';
import { HeroSection } from './features/home/components/HeroSection';
import { SoloChallenges } from './features/home/components/SoloChallenges';
import { WorldBossBanner } from './features/home/components/WorldBossBanner';
import { MultiplayerModes } from './features/home/components/MultiplayerModes';
import { CreativeForge } from './features/home/components/CreativeForge';
import { SingularityLab } from './features/home/components/SingularityLab';
import './App.css';

const App: React.FC = () => {
  return (
    <div className="w-full bg-transparent transition-colors duration-500 bg-manga-overlay">
        <div className="hero-bg w-full transition-all duration-500 shadow-sm border-b border-gray-100/10 dark:border-navy-950/10">
          <HomeNav />
          <HeroSection />
        </div>
        <div className="max-w-[1600px] mx-auto px-6 md:px-10 pb-20 mt-12 bg-[#fffcf0] dark:bg-[#1a1a2e] rounded-[3rem] shadow-xl border border-gray-100 dark:border-white/5 transition-colors duration-500">
          <SoloChallenges />
          <WorldBossBanner />
          <MultiplayerModes />
          <CreativeForge />
          <SingularityLab />
        </div>
    </div>
  );
}

export default App;
```

## 3. Gestion de l'Internationalisation (i18n)
La constante de données statique nécessite `isEn` (un booléen basé sur la locale active) pour ses descriptions. 
**Design decision :** Les données exportées de `gameModes.ts` seront englobées dans un hook personnalisé `useGameModes()` ou une fonction `getGameModes(isEn: boolean)` afin que les textes puissent être réactifs aux changements de langue au runtime.

## 4. Plan de Validation
- S'assurer que le refactoring ne casse aucun style (`App.css` global et Tailwind classes préservés).
- Vérifier les liens de navigation (React Router `Link`).
- Lancer le frontend (ou la suite de tests) pour confirmer l'absence d'erreurs d'import.
