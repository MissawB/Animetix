# Plan d'Implémentation - Sponsoring Anime Direct (B2B)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer les faux sponsors textuels de `SimulatedAdBanner.tsx` par de vraies marques de l'univers anime (Crunchyroll, ADN, Crunchyroll Store) avec des illustrations publicitaires premium générées par l'IA et une redirection externe vers leurs sites.

**Architecture:**
1. Générer les trois illustrations publicitaires dans `frontend/public/img/sponsors/`.
2. Mettre à jour `SimulatedAdBanner.tsx` pour afficher les images, les slogans réels et rediriger l'utilisateur dans un nouvel onglet avec `window.open`.
3. S'assurer que le rendu est fluide et responsive.

**Tech Stack:** React, TypeScript, Tailwind, Lucide-Icons, Nano Banana (Générateur d'images).

---

### Task 1: Génération des Images Publicitaires B2B

**Files:**
- Create: `frontend/public/img/sponsors/crunchyroll_ad.png`
- Create: `frontend/public/img/sponsors/adn_ad.png`
- Create: `frontend/public/img/sponsors/manga_store_ad.png`

- [ ] **Step 1: Créer le dossier cible si nécessaire**

S'assurer que le dossier `frontend/public/img/sponsors/` existe.

- [ ] **Step 2: Générer l'image publicitaire Crunchyroll**

Générer un visuel orange de style cyber-manga pour Crunchyroll :
- Name: `crunchyroll_ad`
- Prompt: "Orange cyber anime advertising banner, futuristic interface, sleek clean design, digital art, high quality, manga background, horizontal 400x150"

- [ ] **Step 3: Générer l'image publicitaire ADN**

Générer un visuel bleu néon de style cyber-manga pour Animation Digital Network :
- Name: `adn_ad`
- Prompt: "Blue cyber neon anime streaming banner, futuristic terminal, digital technology background, sleek sci-fi style, horizontal 400x150"

- [ ] **Step 4: Générer l'image publicitaire Crunchyroll Store**

Générer un visuel rose/violet pour la boutique de mangas et figurines :
- Name: `manga_store_ad`
- Prompt: "Purple and pink neon futuristic manga bookstore display, anime figurines, cyber toy shopfront banner illustration, horizontal 400x150"

---

### Task 2: Refonte de SimulatedAdBanner

**Files:**
- Modify: `frontend/src/features/billing/components/SimulatedAdBanner.tsx`

- [ ] **Step 1: Mettre à jour le code du composant**

Remplacer le code de `frontend/src/features/billing/components/SimulatedAdBanner.tsx` pour afficher les nouveaux sponsors et charger les illustrations :

```tsx
import React, { useState, useEffect } from 'react';
import { ExternalLink, Sparkles, X } from 'lucide-react';

const SPONSORS = [
  {
    name: 'Crunchyroll',
    slogan: 'Le meilleur de l\'anime en HD. Essai gratuit de 14 jours !',
    cta: 'Regarder sur Crunchyroll',
    color: 'from-orange-600 to-amber-500',
    image: '/img/sponsors/crunchyroll_ad.png',
    url: 'https://www.crunchyroll.com'
  },
  {
    name: 'Animation Digital Network',
    slogan: 'Découvrez ADN, la plateforme de streaming 100% anime VF/VOSTFR.',
    cta: 'Explorer le Catalogue',
    color: 'from-blue-600 to-indigo-500',
    image: '/img/sponsors/adn_ad.png',
    url: 'https://animationdigitalnetwork.fr'
  },
  {
    name: 'Crunchyroll Store',
    slogan: 'Figurines de collection et produits officiels de vos séries favoris !',
    cta: 'Visiter la Boutique',
    color: 'from-purple-600 to-pink-500',
    image: '/img/sponsors/manga_store_ad.png',
    url: 'https://store.crunchyroll.com'
  }
];

export const SimulatedAdBanner: React.FC = () => {
  const [sponsor, setSponsor] = useState(SPONSORS[0]);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const random = SPONSORS[Math.floor(Math.random() * SPONSORS.length)];
    setSponsor(random);
  }, []);

  const handleCtaClick = () => {
    window.open(sponsor.url, '_blank', 'noopener,noreferrer');
  };

  if (!visible) return null;

  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-black/60 p-4 font-mono shadow-xl backdrop-blur-md transition-all duration-300 hover:border-yellow-500/20">
      <div className="absolute top-2 right-2 flex items-center gap-2 z-10">
        <span className="bg-yellow-500/20 text-yellow-400 text-[8px] font-black uppercase px-2 py-0.5 rounded border border-yellow-500/30">
          SPONSORISÉ
        </span>
        <button 
          onClick={() => setVisible(false)} 
          className="text-gray-500 hover:text-white transition-colors"
          title="Masquer la publicité"
        >
          <X size={12} />
        </button>
      </div>

      <div className="space-y-3 mt-2 flex flex-col">
        {/* Image de la bannière publicitaire */}
        <div 
          onClick={handleCtaClick}
          className="relative aspect-[8/3] w-full rounded-lg overflow-hidden border border-white/5 cursor-pointer hover:opacity-90 transition-opacity"
        >
          <img 
            src={sponsor.image} 
            alt={sponsor.name} 
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLElement).style.display = 'none';
            }}
          />
        </div>

        <div className="space-y-1">
          <h4 className="text-xs font-black uppercase tracking-tight text-white flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-yellow-400" /> {sponsor.name}
          </h4>
          <p className="text-[10px] text-gray-400 font-medium leading-relaxed">
            {sponsor.slogan}
          </p>
        </div>

        <button
          onClick={handleCtaClick}
          className={`w-full text-center text-[10px] font-black uppercase tracking-wider py-2.5 px-3 rounded-xl bg-gradient-to-r ${sponsor.color} text-white flex items-center justify-center gap-1 hover:scale-[1.02] active:scale-95 transition-all`}
        >
          {sponsor.cta} <ExternalLink size={10} />
        </button>
        <p className="text-[7px] text-center text-gray-600">
          Activer le Boost pour supprimer les publicités.
        </p>
      </div>
    </div>
  );
};
```

---

### Task 3: Validation et Tests

**Files:**
- Modify: `frontend/src/pages/billing/__tests__/PricingPage.test.tsx`

- [ ] **Step 1: Lancer les tests frontend**

S'assurer que la page de tests unitaires passe toujours sans régression :
Run: `npx vitest run src/pages/billing/`
Expected: PASS

- [ ] **Step 2: Commiter et Pousser**

```bash
git add frontend/public/img/sponsors/ frontend/src/features/billing/components/SimulatedAdBanner.tsx
git commit -m "feat(frontend): implement direct B2B anime sponsoring banners for Crunchyroll and ADN"
git push origin main
```
