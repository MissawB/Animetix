# Plan d'Implémentation - Vidéos de Publicité pour Quota & Boost

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer le faux minuteur progressif du modal de pub par un véritable lecteur vidéo HTML5 `<video>` jouant des vidéos de pub hébergées en ligne, avec coupure/activation du son, blocage de la fermeture et activation du bouton de récompense uniquement à la fin de la lecture.

**Architecture:** Mettre à jour `SponsorStreamModal.tsx` en insérant la balise `<video>` avec des écouteurs d'événements (`onTimeUpdate`, `onEnded`, `onError`). Mettre à jour les tests unitaires dans `PricingPage.test.tsx`.

**Tech Stack:** React, TypeScript, HTML5 Media APIs, Vitest, React Testing Library.

---

### Task 1: Implémentation du Lecteur Vidéo dans SponsorStreamModal

**Files:**
- Modify: `frontend/src/features/billing/components/SponsorStreamModal.tsx`

- [ ] **Step 1: Remplacer le code de `SponsorStreamModal.tsx`**

Modifier `frontend/src/features/billing/components/SponsorStreamModal.tsx` pour y intégrer l'élément `<video>`, le bouton de son, et les événements de cycle de vie :

```tsx
import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Film, CheckCircle2, X, Volume2, VolumeX, AlertTriangle } from 'lucide-react';
import { Button } from '../../../components/ui/Button';

interface Props {
  actionType: 'boost' | 'refill';
  onClose: () => void;
  onConfirm: () => Promise<void>;
}

const VIDEO_SOURCES = {
  boost: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
  refill: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4'
};

const SPONSORS_CLIPS = {
  boost: { name: "Capsule Corp", msg: "Capsulage moléculaire Hoipoi V10 en cours..." },
  refill: { name: "Future Gadget Lab", msg: "Optimisation de l'onde temporelle du micro-ondes..." }
};

export const SponsorStreamModal: React.FC<Props> = ({ actionType, onClose, onConfirm }) => {
  const [progress, setProgress] = useState(0);
  const [isDone, setIsDone] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isMuted, setIsMuted] = useState(true);
  const [hasError, setHasError] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  
  const sponsor = SPONSORS_CLIPS[actionType];
  const videoUrl = VIDEO_SOURCES[actionType];

  // Minuteur de secours si le chargement de la vidéo échoue
  useEffect(() => {
    if (!hasError) return;
    
    const duration = actionType === 'boost' ? 10000 : 5000;
    const intervalTime = 50;
    const step = (intervalTime / duration) * 100;
    
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(timer);
          setIsDone(true);
          return 100;
        }
        return prev + step;
      });
    }, intervalTime);
    
    return () => clearInterval(timer);
  }, [hasError, actionType]);

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const current = videoRef.current.currentTime;
      const duration = videoRef.current.duration || 1;
      setProgress((current / duration) * 100);
    }
  };

  const handleVideoEnded = () => {
    setIsDone(true);
    setProgress(100);
  };

  const handleVideoError = () => {
    console.error("Video failed to load, triggering fallback timer.");
    setHasError(true);
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !videoRef.current.muted;
      setIsMuted(videoRef.current.muted);
    }
  };

  const handleClaim = async () => {
    setIsSubmitting(true);
    try {
      await onConfirm();
      onClose();
    } catch (e) {
      console.error(e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
      <motion.div 
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/90 backdrop-blur-xl"
        onClick={isDone && !isSubmitting ? onClose : undefined}
      />

      <motion.div
        initial={{ scale: 0.9, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.9, opacity: 0, y: 20 }}
        className="relative w-full max-w-md bg-[#0b0c15] border border-yellow-500/30 rounded-3xl overflow-hidden shadow-[0_0_80px_rgba(234,179,8,0.15)]"
      >
        <div className="p-8 space-y-6">
          <header className="flex justify-between items-center">
            <div>
              <p className="text-yellow-500 text-[10px] font-black uppercase tracking-widest">Flux de Sponsoring</p>
              <h3 className="text-xl font-black italic uppercase text-white">Lecture Vidéo de Pub</h3>
            </div>
            {isDone && !isSubmitting && (
              <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full text-gray-400 hover:text-white">
                <X size={16}/>
              </button>
            )}
          </header>

          <div className="relative aspect-video rounded-2xl bg-black border border-white/5 overflow-hidden flex flex-col items-center justify-center text-center shadow-inner group">
            <div className="absolute inset-0 bg-grid-pattern opacity-10 pointer-events-none" />
            
            {hasError ? (
              <div className="p-4 space-y-2 z-10">
                <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto animate-pulse" />
                <h4 className="text-sm font-black uppercase text-yellow-500">{sponsor.name}</h4>
                <p className="text-xs text-gray-400 font-mono italic">Flux de secours actif...</p>
              </div>
            ) : isDone ? (
              <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="z-10">
                <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto animate-bounce" />
                <h4 className="text-sm font-black uppercase text-yellow-500 mt-2">{sponsor.name}</h4>
                <p className="text-xs text-gray-400 font-mono italic">Sponsor visionné avec succès !</p>
              </motion.div>
            ) : (
              <>
                <video
                  ref={videoRef}
                  src={videoUrl}
                  autoPlay
                  muted={isMuted}
                  onTimeUpdate={handleTimeUpdate}
                  onEnded={handleVideoEnded}
                  onError={handleVideoError}
                  className="absolute inset-0 w-full h-full object-cover"
                  onContextMenu={(e) => e.preventDefault()}
                  data-testid="ad-video-element"
                />
                
                {/* Contrôles overlay pour le son */}
                <div className="absolute bottom-3 right-3 z-10">
                  <button 
                    onClick={toggleMute}
                    className="p-2 bg-black/60 hover:bg-black/80 text-white rounded-full transition-colors border border-white/10"
                    title={isMuted ? "Activer le son" : "Couper le son"}
                    data-testid="mute-toggle-button"
                  >
                    {isMuted ? <VolumeX size={14} /> : <Volume2 size={14} />}
                  </button>
                </div>
              </>
            )}
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-[10px] font-bold uppercase tracking-wider text-gray-500 font-mono">
              <span>{isDone ? 'Complété' : 'Chargement du Boost...'}</span>
              <span>{Math.min(100, Math.round(progress))}%</span>
            </div>
            <div className="w-full bg-gray-950 h-2.5 rounded-full overflow-hidden border border-white/5">
              <div 
                className="bg-yellow-500 h-full shadow-[0_0_10px_#eab308] transition-all duration-75"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          <Button 
            variant={isDone ? 'primary' : 'outline'} 
            fullWidth 
            size="lg" 
            className="py-5 font-black uppercase tracking-widest" 
            onClick={handleClaim}
            disabled={!isDone || isSubmitting}
          >
            {isSubmitting ? 'VALIDATION...' : isDone ? 'RÉCLAMER LE BONUS' : 'VISIONNEZ LA PUB'}
          </Button>
        </div>
      </motion.div>
    </div>
  );
};
```

---

### Task 2: Mise à jour et Validation des Tests Frontend

**Files:**
- Modify: `frontend/src/pages/billing/__tests__/PricingPage.test.tsx`

- [ ] **Step 1: Mettre à jour `PricingPage.test.tsx`**

Modifier `frontend/src/pages/billing/__tests__/PricingPage.test.tsx` pour s'assurer qu'aucun avertissement sur HTMLVideoElement ne perturbe JSDOM et que la structure de test reste cohérente :

```tsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import PricingPage from '../PricingPage';
import { useAuthStore } from '../../../store/authStore';

vi.mock('../../../store/authStore');
vi.mock('../../../api', () => ({
  updateAccountSettings: vi.fn().mockResolvedValue({ status: 'updated' }),
  apiClient: vi.fn().mockResolvedValue({ status: 'refilled' })
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<any>();
  return {
    ...actual,
    useNavigate: () => mockNavigate
  };
});

describe('PricingPage (Espace Sponsors)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly for guests', () => {
    (useAuthStore as any).mockReturnValue({
      user: null,
      isAuthenticated: false,
      checkAuth: vi.fn()
    });

    render(
      <BrowserRouter>
        <PricingPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/Sponsoring & Boost/i)).toBeInTheDocument();
    expect(screen.getByText(/Recharge Quota/i)).toBeInTheDocument();
    expect(screen.getByText(/Boost Cyber-Nexus/i)).toBeInTheDocument();
  });

  it('redirects to login when standard user tries to boost without login', () => {
    (useAuthStore as any).mockReturnValue({
      user: null,
      isAuthenticated: false,
      checkAuth: vi.fn()
    });

    render(
      <BrowserRouter>
        <PricingPage />
      </BrowserRouter>
    );

    const boostButton = screen.getByText('ACTIVER LE BOOST');
    fireEvent.click(boostButton);

    expect(mockNavigate).toHaveBeenCalledWith('/login?redirect=/pricing/');
  });
});
```

- [ ] **Step 2: Lancer les tests frontend**

Run: `npx vitest run src/pages/billing/`
Expected: PASS

- [ ] **Step 3: Commiter les changements**

```bash
git add frontend/src/features/billing/components/SponsorStreamModal.tsx frontend/src/pages/billing/__tests__/PricingPage.test.tsx
git commit -m "feat(frontend): integrate actual unskippable HTML5 video ads for quota refill and boost rewards"
```
