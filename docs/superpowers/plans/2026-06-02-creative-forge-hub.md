# Creative Forge Hub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Centralize all creative tools (Forge, Media Labs, Singularity Labs) into a single, immersive portal called "Forge des Mondes".

**Architecture:** A unified React component serving as a portal with four symbolic relics (Book, Frame, Headphones, Flask) acting as category entry points, each leading to a filtered list of labs.

**Tech Stack:** React 19, Tailwind CSS, Framer Motion, Lucide Icons, i18next.

---

### Task 1: Localization & Translations

**Files:**
- Modify: `frontend/public/locales/fr/translation.json`
- Modify: `frontend/public/locales/en/translation.json`

- [ ] **Step 1: Update French translations**
Add the `forge_hub` section to `fr/translation.json`.

```json
  "forge_hub": {
    "title": "Forge des Mondes",
    "subtitle": "Accès Protocol Omega",
    "description": "Sélectionnez une relique pour initialiser le laboratoire",
    "categories": {
      "narrative": {
        "title": "Narratif",
        "sub": "Reality Synthesis",
        "desc": "Forge de Scénarios"
      },
      "visual": {
        "title": "Visuel",
        "sub": "Visual Labs",
        "desc": "Manga & Video Lab"
      },
      "audio": {
        "title": "Audio",
        "sub": "Aural Nexus",
        "desc": "Voice & Soundscape"
      },
      "experimental": {
        "title": "Labo",
        "sub": "Singularity Lab",
        "desc": "Quantum & Swarm"
      }
    }
  }
```

- [ ] **Step 2: Update English translations**
Add the `forge_hub` section to `en/translation.json`.

```json
  "forge_hub": {
    "title": "Forge of Worlds",
    "subtitle": "Omega Access Protocol",
    "description": "Select a relic to initialize the laboratory",
    "categories": {
      "narrative": {
        "title": "Narrative",
        "sub": "Reality Synthesis",
        "desc": "Scenario Forge"
      },
      "visual": {
        "title": "Visual",
        "sub": "Visual Labs",
        "desc": "Manga & Video Lab"
      },
      "audio": {
        "title": "Audio",
        "sub": "Aural Nexus",
        "desc": "Voice & Soundscape"
      },
      "experimental": {
        "title": "Lab",
        "sub": "Singularity Lab",
        "desc": "Quantum & Swarm"
      }
    }
  }
```

- [ ] **Step 3: Commit translations**

```bash
git add frontend/public/locales/*/translation.json
git commit -m "i18n: add creative forge hub translations"
```

---

### Task 2: Base Component Structure

**Files:**
- Create: `frontend/src/features/labs/ForgeHubPage.tsx`
- Create: `frontend/src/features/labs/components/RelicItem.tsx`

- [ ] **Step 1: Create RelicItem component**
This component handles the visual state and animations for each relic.

```tsx
import React from 'react';
import { motion } from 'framer-motion';

interface RelicItemProps {
  id: string;
  title: string;
  sub: string;
  desc: string;
  color: string;
  glowColor: string;
  children: React.ReactNode;
  onClick: () => void;
}

export const RelicItem: React.FC<RelicItemProps> = ({ 
  title, sub, desc, color, glowColor, children, onClick 
}) => {
  return (
    <motion.div 
      onClick={onClick}
      className="flex flex-col items-center justify-center cursor-pointer group"
      whileHover={{ y: -20, scale: 1.05 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      <div className="relative w-60 h-80 flex items-center justify-center">
        <div className={`absolute inset-0 blur-[40px] opacity-20 group-hover:opacity-60 transition-opacity rounded-full ${glowColor}`} />
        <div className={`w-full h-full ${color} transition-all duration-500 group-hover:drop-shadow-[0_0_20px_currentColor]`}>
          {children}
        </div>
      </div>
      <div className="mt-8 text-center opacity-60 group-hover:opacity-100 transition-all transform group-hover:translate-y-2">
        <p className={`text-[10px] font-black uppercase tracking-widest mb-1 ${color}`}>{sub}</p>
        <h2 className="text-5xl font-black italic manga-font uppercase leading-none">{title}</h2>
        <p className="mt-4 text-[10px] font-bold opacity-30 uppercase tracking-widest">{desc}</p>
      </div>
    </motion.div>
  );
};
```

- [ ] **Step 2: Create ForgeHubPage base**
Implement the main layout with the 4 relics.

```tsx
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { RelicItem } from './components/RelicItem';
import { Book, Frame, Headphones, FlaskConical as Flask } from 'lucide-react';

const ForgeHubPage: React.FC = () => {
  const { t } = useTranslation();
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const categories = [
    { id: 'narrative', icon: Book, color: 'text-amber-500', glow: 'bg-amber-500' },
    { id: 'visual', icon: Frame, color: 'text-blue-500', glow: 'bg-blue-500' },
    { id: 'audio', icon: Headphones, color: 'text-emerald-500', glow: 'bg-emerald-500' },
    { id: 'experimental', icon: Flask, color: 'text-red-600', glow: 'bg-red-600' }
  ];

  return (
    <AnimatedPage>
      <div className="min-h-screen flex flex-col items-center justify-center px-6 py-20 relative overflow-hidden bg-[#020202]">
        {/* Ambient Glows */}
        <div className="fixed inset-0 pointer-events-none z-0 opacity-10">
          <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-red-600/20 blur-[150px] rounded-full" />
          <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-blue-600/20 blur-[150px] rounded-full" />
        </div>

        <header className="text-center mb-24 z-10">
          <p className="text-[10px] font-black uppercase tracking-[0.5em] text-red-500 mb-2">
            {t('forge_hub.subtitle')}
          </p>
          <h1 className="text-7xl font-black italic manga-font uppercase tracking-tighter text-white">
            {t('forge_hub.title').split(' ')[0]} <span className="text-red-600 drop-shadow-[0_0_15px_rgba(220,38,38,0.5)]">
              {t('forge_hub.title').split(' ').slice(1).join(' ')}
            </span>
          </h1>
        </header>

        <div className="flex flex-wrap gap-12 justify-center items-center z-10 max-w-7xl">
          {categories.map((cat) => (
            <RelicItem
              key={cat.id}
              id={cat.id}
              title={t(`forge_hub.categories.${cat.id}.title`)}
              sub={t(`forge_hub.categories.${cat.id}.sub`)}
              desc={t(`forge_hub.categories.${cat.id}.desc`)}
              color={cat.color}
              glowColor={cat.glow}
              onClick={() => setSelectedCategory(cat.id)}
            >
              <cat.icon className="w-full h-full stroke-[0.5]" />
            </RelicItem>
          ))}
        </div>

        <footer className="mt-24 opacity-20 text-center z-10">
          <p className="text-xs uppercase tracking-[0.4em] text-white">
            {t('forge_hub.description')}
          </p>
        </footer>
      </div>
    </AnimatedPage>
  );
};

export default ForgeHubPage;
```

- [ ] **Step 3: Commit base structure**

```bash
git add frontend/src/features/labs/ForgeHubPage.tsx frontend/src/features/labs/components/RelicItem.tsx
git commit -m "feat: create base ForgeHubPage with relic items"
```

---

### Task 3: Category Detail & Lab List

**Files:**
- Modify: `frontend/src/features/labs/ForgeHubPage.tsx`
- Create: `frontend/src/features/labs/components/LabListOverlay.tsx`

- [ ] **Step 1: Define Lab data mapping**
Map each category to its corresponding lab modules.

```tsx
// Inside ForgeHubPage.tsx or a separate constants file
const categoryLabs = {
  narrative: [
    { id: 'forge', title: 'Forge de Réalité', url: '/forge/', desc: 'Fusionnez univers et scénarios.' },
  ],
  visual: [
    { id: 'manga', title: 'Manga Lab', url: '/manga_lab/', desc: 'Rendu Manga par IA.' },
    { id: 'video', title: 'Video Lab', url: '/video-lab/', desc: 'Analyse et indexation vidéo.' },
    { id: 'nexus', title: 'Visual Nexus', url: '/visual-nexus/', desc: 'Exploration d\'embeddings visuels.' },
    { id: 'reconstruction', title: 'Cinematic Reconstruction', url: '/cinematic-reconstruction/', desc: '3D de scènes animées.' },
  ],
  audio: [
    { id: 'audio', title: 'Audio Lab', url: '/audio_lab/', desc: 'Clonage vocal et synthèse.' },
    { id: 'soundscape', title: 'Soundscape Lab', url: '/soundscape-lab/', desc: 'Génération d\'ambiances sonores.' },
    { id: 'speech', title: 'Speech-to-Speech', url: '/s2s-lab/', desc: 'Transformation vocale temps-réel.' },
  ],
  experimental: [
    { id: 'singularity', title: 'Singularity Hub', url: '/lab/', desc: 'Accès aux modules de recherche Omega.' },
  ]
};
```

- [ ] **Step 2: Implement LabListOverlay**
Create a component that appears when a category is selected.

```tsx
import React from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ArrowRight } from 'lucide-react';
import { Card } from '../../../components/ui/Card';

interface LabListOverlayProps {
  category: string | null;
  labs: { id: string, title: string, url: string, desc: string }[];
  onClose: () => void;
}

export const LabListOverlay: React.FC<LabListOverlayProps> = ({ category, labs, onClose }) => {
  return (
    <AnimatePresence>
      {category && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/90 backdrop-blur-xl"
        >
          <div className="max-w-4xl w-full">
            <header className="flex justify-between items-center mb-12">
              <h2 className="text-4xl font-black italic manga-font uppercase tracking-tighter text-white">
                Laboratoires <span className="text-red-600">{category}</span>
              </h2>
              <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition-colors text-white">
                <X className="w-8 h-8" />
              </button>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {labs.map((lab) => (
                <Link key={lab.id} to={lab.url} className="no-underline group">
                  <Card padding="lg" className="bg-white/5 border-white/10 hover:border-red-600/50 transition-all">
                    <div className="flex justify-between items-center">
                      <div>
                        <h3 className="text-xl font-black italic uppercase manga-font mb-2 group-hover:text-red-500 transition-colors">
                          {lab.title}
                        </h3>
                        <p className="text-xs opacity-40 uppercase font-bold tracking-wider">
                          {lab.desc}
                        </p>
                      </div>
                      <ArrowRight className="w-6 h-6 opacity-0 group-hover:opacity-100 transform translate-x-[-10px] group-hover:translate-x-0 transition-all text-red-500" />
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
```

- [ ] **Step 3: Integrate Overlay into ForgeHubPage**
Update `ForgeHubPage` to show the overlay.

- [ ] **Step 4: Commit category detail**

```bash
git add frontend/src/features/labs/ForgeHubPage.tsx frontend/src/features/labs/components/LabListOverlay.tsx
git commit -m "feat: implement lab list overlay for category selection"
```

---

### Task 4: Routing & Integration

**Files:**
- Modify: `frontend/src/features/labs/routes/LabRoutes.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/Navbar.tsx`

- [ ] **Step 1: Update LabRoutes**
Change the route for `/forge/` and `/lab/` or add `/forge-hub/`. Let's use `/forge-hub/` as the main and redirect others if needed, but for now just add it.

```tsx
// Modify LabRoutes.tsx
// ... imports
const ForgeHubPage = lazy(() => import('../ForgeHubPage'));

export const LabRoutes = (
  <>
    <Route path="/forge-hub/" element={<ForgeHubPage />} />
    {/* Keep existing for now but we will redirect later if desired */}
    {/* ... rest of routes */}
  </>
);
```

- [ ] **Step 2: Update App.tsx Creative Section**
Update the "Creative Forge" section on the home page to point to the new Hub.

- [ ] **Step 3: Update Navbar**
Change "BETA LAB" or "LA FORGE" to "FORGE HUB".

- [ ] **Step 4: Commit integration**

```bash
git add frontend/src/features/labs/routes/LabRoutes.tsx frontend/src/App.tsx frontend/src/components/Navbar.tsx
git commit -m "refactor: integrate Forge Hub as central creative entry point"
```

---

### Task 5: Final Polish & Visual Effects

**Files:**
- Modify: `frontend/src/features/labs/ForgeHubPage.tsx`

- [ ] **Step 1: Add Particle background**
Implement a simple particle system using `framer-motion` or CSS.

- [ ] **Step 2: Refine relic animations**
Add floating animations to relics.

- [ ] **Step 3: Commit final polish**

```bash
git add frontend/src/features/labs/ForgeHubPage.tsx
git commit -m "style: add final polish and animations to Forge Hub"
```
