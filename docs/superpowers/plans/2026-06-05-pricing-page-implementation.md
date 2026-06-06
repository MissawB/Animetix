# Page "Plans & Tarifs" Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Créer une page `/pricing/` immersive permettant aux utilisateurs de comparer les offres et de souscrire au niveau Premium via une modale de simulation de paiement ("Nexus Gateway").

**Architecture:** 
- Un nouveau feature directory `billing` contiendra la page et ses composants.
- Intégration avec `useAuthStore` pour la gestion de l'état utilisateur et les appels API de mise à jour de tier.
- Utilisation de `Framer Motion` pour les animations de la modale Gateway.

**Tech Stack:** React (TypeScript), Tailwind CSS, Framer Motion, Lucide React, TanStack Query.

---

### Task 1: Création de la structure et de la page Pricing

**Files:**
- Create: `frontend/src/features/billing/PricingPage.tsx`
- Modify: `frontend/src/features/social/routes/SocialRoutes.tsx`

- [ ] **Step 1: Créer le composant de base PricingPage**

```typescript
// frontend/src/features/billing/PricingPage.tsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Shield, Zap, Terminal, Cpu, ArrowRight, X } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { updateAccountSettings } from '../../api';
import { useToastStore } from '../../store/toastStore';
import { Button } from '../../components/ui/Button';

const TIERS = [
  {
    id: 'free',
    name: 'Explorateur',
    version: 'V01',
    price: '0',
    features: ['Accès au catalogue standard', 'Jusqu\'à 3 clubs de fans', 'Quota IA standard'],
    unavailable: ['Visualiseur de Graphe complet', 'Auras personnalisées'],
    color: 'gray'
  },
  {
    id: 'premium',
    name: 'Premium',
    version: 'V02',
    price: '9.99',
    features: ['Nexus Visualizer débloqué', 'Création de clubs illimitée', 'Auras d\'interface personnalisées', 'Quota IA boosté (x5)'],
    unavailable: ['Accès API Headless'],
    color: 'blue',
    recommended: true
  },
  {
    id: 'pro',
    name: 'Expert API',
    version: 'V03',
    price: '29.99',
    features: ['Accès complet à l\'API Headless', 'Diagnostics IA haute fidélité', 'Support développeur prioritaire'],
    unavailable: [],
    color: 'white'
  }
];

const PricingPage: React.FC = () => {
  const { user, checkAuth } = useAuthStore();
  const [selectedTier, setSelectedTier] = useState<any>(null);

  return (
    <div className="min-h-screen bg-[#050505] text-white pt-24 pb-32 px-6">
      <div className="max-w-7xl mx-auto">
        <header className="text-center mb-20 space-y-4">
          <h1 className="text-6xl md:text-8xl font-black italic uppercase tracking-tighter manga-font">
            Élevez votre <span className="text-blue-500 text-glow">Expérience</span>
          </h1>
          <p className="text-gray-500 font-bold uppercase tracking-[0.3em] text-sm">
            Choisissez le protocole qui vous convient
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {TIERS.map((tier) => (
            <motion.div
              key={tier.id}
              whileHover={{ y: -10 }}
              className={`relative p-8 rounded-3xl border-2 transition-all ${
                tier.id === 'premium' 
                  ? 'bg-blue-900/10 border-blue-500 shadow-[0_0_40px_rgba(59,130,246,0.15)] scale-105 z-10' 
                  : 'bg-white/5 border-white/5'
              }`}
            >
              {tier.recommended && (
                <div className="absolute -top-4 right-8 bg-blue-500 text-[10px] font-black uppercase px-3 py-1 rounded-full">
                  Recommandé
                </div>
              )}
              
              <div className="space-y-6">
                <div>
                  <p className="text-[10px] font-black uppercase opacity-30">{tier.version} PROTOCOLE</p>
                  <h2 className="text-3xl font-black italic uppercase tracking-tight">{tier.name}</h2>
                </div>

                <div className="flex items-baseline gap-1">
                  <span className="text-5xl font-black">{tier.price}€</span>
                  <span className="text-xs font-bold opacity-30 uppercase">/ mois</span>
                </div>

                <ul className="space-y-4 pt-4">
                  {tier.features.map(f => (
                    <li key={f} className="flex items-start gap-3 text-sm font-medium">
                      <Check className="w-5 h-5 text-green-500 shrink-0" />
                      {f}
                    </li>
                  ))}
                  {tier.unavailable.map(f => (
                    <li key={f} className="flex items-start gap-3 text-sm font-medium opacity-20">
                      <X className="w-5 h-5 text-red-500 shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>

                <Button
                  variant={tier.id === 'premium' ? 'primary' : 'outline'}
                  fullWidth
                  className="py-6 font-black uppercase italic tracking-widest"
                  onClick={() => tier.id !== 'pro' && setSelectedTier(tier)}
                  disabled={user?.tier === tier.id}
                >
                  {user?.tier === tier.id ? 'ACTIF' : tier.id === 'pro' ? 'CONTACTER' : 'SÉLECTIONNER'}
                </Button>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
      {/* TODO: NexusGatewayModal */}
    </div>
  );
};

export default PricingPage;
```

- [ ] **Step 2: Enregistrer la route dans SocialRoutes.tsx**

```typescript
// frontend/src/features/social/routes/SocialRoutes.tsx
// Ajouter l'import
const PricingPage = lazy(() => import('../../billing/PricingPage'));

// Ajouter la route
<Route path="/pricing/" element={<PricingPage />} />
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/billing/PricingPage.tsx frontend/src/features/social/routes/SocialRoutes.tsx
git commit -m "feat(frontend): create base Pricing page and route"
```

---

### Task 2: Implémentation de la Nexus Gateway Modal

**Files:**
- Create: `frontend/src/features/billing/components/NexusGatewayModal.tsx`
- Modify: `frontend/src/features/billing/PricingPage.tsx`

- [ ] **Step 1: Créer le composant de la modale avec Framer Motion**

```typescript
// frontend/src/features/billing/components/NexusGatewayModal.tsx
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield, Cpu, RefreshCw, CheckCircle, Sparkles, X } from 'lucide-react';
import { Button } from '../../../components/ui/Button';

interface Props {
  tier: any;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}

export const NexusGatewayModal: React.FC<Props> = ({ tier, onClose, onConfirm }) => {
  const [status, setStatus] = useState<'idle' | 'processing' | 'success'>('idle');

  const handleConfirm = async () => {
    setStatus('processing');
    // Simulation du temps de traitement "cyber"
    await new Promise(r => setTimeout(r, 2500));
    try {
        await onConfirm();
        setStatus('success');
    } catch (e) {
        setStatus('idle');
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
      <motion.div 
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/90 backdrop-blur-xl"
        onClick={status !== 'processing' ? onClose : undefined}
      />

      <motion.div
        initial={{ scale: 0.9, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.9, opacity: 0, y: 20 }}
        className="relative w-full max-w-lg bg-navy-950 border border-blue-500/30 rounded-3xl overflow-hidden shadow-[0_0_100px_rgba(59,130,246,0.2)]"
      >
        <div className="p-8 space-y-8">
          {status === 'idle' && (
            <>
              <header className="flex justify-between items-center">
                <div>
                  <p className="text-blue-500 text-[10px] font-black uppercase tracking-widest">Nexus Gateway</p>
                  <h3 className="text-2xl font-black italic uppercase italic">Confirmation Transaction</h3>
                </div>
                <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full"><X size={20}/></button>
              </header>

              <div className="bg-white/5 rounded-2xl p-6 border border-white/5 space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold uppercase opacity-40">Protocole</span>
                  <span className="font-black italic uppercase text-blue-400">{tier.name}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold uppercase opacity-40">Cycle de facturation</span>
                  <span className="font-bold">Mensuel</span>
                </div>
                <div className="h-px bg-white/5" />
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold uppercase opacity-40">Total</span>
                  <span className="text-3xl font-black tracking-tighter">{tier.price}€</span>
                </div>
              </div>

              <Button variant="primary" fullWidth size="lg" className="py-6 font-black uppercase tracking-widest" onClick={handleConfirm}>
                ACTIVER LE PROTOCOLE <Shield className="ml-2 w-5 h-5" />
              </Button>
            </>
          )}

          {status === 'processing' && (
            <div className="py-20 flex flex-col items-center text-center space-y-6">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              >
                <Cpu className="w-16 h-16 text-blue-500" />
              </motion.div>
              <div className="space-y-2">
                <h4 className="text-xl font-black uppercase italic tracking-widest">Initialisation...</h4>
                <p className="text-xs text-gray-500 font-mono">CRYPT_SIG_VALIDATION // NEXUS_HANDSHAKE</p>
              </div>
            </div>
          )}

          {status === 'success' && (
            <div className="py-12 flex flex-col items-center text-center space-y-8">
              <div className="relative">
                <motion.div 
                    initial={{ scale: 0 }} animate={{ scale: 1 }}
                    className="w-24 h-24 bg-green-500/20 text-green-500 rounded-full flex items-center justify-center shadow-[0_0_50px_rgba(34,197,94,0.3)]"
                >
                    <CheckCircle className="w-12 h-12" />
                </motion.div>
                <motion.div animate={{ opacity: [0, 1, 0], scale: [1, 1.5, 2] }} transition={{ repeat: Infinity, duration: 1.5 }} className="absolute inset-0 bg-green-500/30 rounded-full" />
              </div>
              
              <div className="space-y-2">
                <h4 className="text-3xl font-black uppercase italic manga-font">Protocole Activé</h4>
                <p className="text-gray-400 font-medium">Votre accès <span className="text-blue-400 font-black">{tier.name}</span> est maintenant opérationnel.</p>
              </div>

              <Button variant="outline" fullWidth onClick={onClose} className="font-black uppercase italic tracking-widest">
                ENTRER DANS LE NEXUS <Sparkles className="ml-2 w-4 h-4" />
              </Button>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};
```

- [ ] **Step 2: Intégrer la modale dans PricingPage.tsx**

```typescript
// frontend/src/features/billing/PricingPage.tsx
import { NexusGatewayModal } from './components/NexusGatewayModal';

// ... à l'intérieur du composant PricingPage
  const { addToast } = useToastStore();

  const handleConfirmSubscription = async () => {
    try {
      await updateAccountSettings({ tier: selectedTier.id });
      await checkAuth();
    } catch (error) {
      addToast('Erreur lors de la synchronisation Nexus', 'error');
      throw error;
    }
  };

  return (
    // ...
    <AnimatePresence>
      {selectedTier && (
        <NexusGatewayModal 
          tier={selectedTier} 
          onClose={() => setSelectedTier(null)}
          onConfirm={handleConfirmSubscription}
        />
      )}
    </AnimatePresence>
  );
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/billing/components/NexusGatewayModal.tsx frontend/src/features/billing/PricingPage.tsx
git commit -m "feat(frontend): implement Nexus Gateway simulation modal"
```

---

### Task 3: Liaison dans la Navbar et Finalisation

**Files:**
- Modify: `frontend/src/components/Navbar.tsx`

- [ ] **Step 1: Ajouter le lien "Nexus Pro" ou "Premium" dans la Navbar**

```typescript
// frontend/src/components/Navbar.tsx
{/* Remplacer ou ajouter près du bouton Profile */}
<Link 
  to="/pricing/" 
  className="flex items-center gap-2 px-4 py-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/20 rounded-xl transition-all group"
>
  <Zap className="w-4 h-4 group-hover:fill-current" />
  <span className="text-[10px] font-black uppercase tracking-widest hidden md:block">Nexus Pro</span>
</Link>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/Navbar.tsx
git commit -m "feat(frontend): add navigation link to Pricing page in Navbar"
```
