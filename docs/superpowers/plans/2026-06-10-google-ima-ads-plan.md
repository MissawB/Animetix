# Plan d'Implémentation - Régies Publicitaires Réelles (Google IMA SDK)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer la vidéo HTML5 locale par le SDK Google IMA pour charger et jouer des publicités vidéo VAST 3.0 réelles, avec détection d'ad-blocker et repli fluide.

**Architecture:** 
1. Charger le SDK Google IMA (`ima3.js`) de manière dynamique.
2. Initialiser l'AdDisplayContainer et l'AdsLoader avec un geste de clic utilisateur obligatoire.
3. Gérer les événements de progression publicitaire et de fin de lecture pour débloquer la récompense.
4. Mettre en place un mécanisme de repli (fallback) automatique vers la vidéo locale si le chargement du SDK ou de la pub échoue (ad-blocker actif ou test JSDOM).

**Tech Stack:** React, TypeScript, Google IMA SDK HTML5, Vitest, React Testing Library.

---

### Task 1: Intégration du SDK Google IMA dans SponsorStreamModal

**Files:**
- Modify: `frontend/src/features/billing/components/SponsorStreamModal.tsx`

- [ ] **Step 1: Remplacer le code du SponsorStreamModal**

Mettre à jour `frontend/src/features/billing/components/SponsorStreamModal.tsx` avec la logique de chargement de l'IMA SDK, de gestion du geste utilisateur, de lecture de pub et de repli automatique :

```tsx
import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Film, CheckCircle2, X, AlertTriangle, Play } from 'lucide-react';
import { Button } from '../../../components/ui/Button';

interface Props {
  actionType: 'boost' | 'refill';
  onClose: () => void;
  onConfirm: () => Promise<void>;
}

const FALLBACK_VIDEO_SOURCES = {
  boost: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
  refill: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4'
};

const SPONSORS_CLIPS = {
  boost: { name: "Capsule Corp", msg: "Capsulage moléculaire Hoipoi V10 en cours..." },
  refill: { name: "Future Gadget Lab", msg: "Optimisation de l'onde temporelle du micro-ondes..." }
};

const AD_TAG_URL = 'https://pubads.g.doubleclick.net/gampad/ads?iu=/21775744923/external/single_ad_samples&sz=640x480&ciu_szs=300x250&impl=s&gdfp_req=1&env=vp&output=vast&unviewed_position_start=1&cust_params=deployment%3Ddevsite%26sample_ct%3Dlinear&correlator=';

export const SponsorStreamModal: React.FC<Props> = ({ actionType, onClose, onConfirm }) => {
  const [isSdkLoaded, setIsSdkLoaded] = useState(false);
  const [isAdStarted, setIsAdStarted] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [progress, setProgress] = useState(0);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const adContainerRef = useRef<HTMLDivElement>(null);
  const adsLoaderRef = useRef<any>(null);
  const adsManagerRef = useRef<any>(null);
  const adDisplayContainerRef = useRef<any>(null);

  const sponsor = SPONSORS_CLIPS[actionType];

  // 1. Chargement dynamique du script Google IMA SDK
  useEffect(() => {
    if ((window as any).google && (window as any).google.ima) {
      setIsSdkLoaded(true);
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://imasdk.googleapis.com/js/sdkloader/ima3.js';
    script.async = true;
    script.onload = () => {
      if ((window as any).google && (window as any).google.ima) {
        setIsSdkLoaded(true);
      } else {
        console.error("IMA SDK script loaded but window.google.ima is undefined");
        setHasError(true);
      }
    };
    script.onerror = () => {
      console.error("Failed to load Google IMA SDK script");
      setHasError(true);
    };
    document.body.appendChild(script);

    return () => {
      try {
        document.body.removeChild(script);
      } catch (e) {
        // Ignorer si déjà retiré ou absent
      }
    };
  }, []);

  // 2. Initialisation d'AdsLoader
  useEffect(() => {
    if (!isSdkLoaded || hasError) return;

    try {
      const google = (window as any).google;
      
      const adDisplayContainer = new google.ima.AdDisplayContainer(
        adContainerRef.current,
        videoRef.current
      );
      adDisplayContainerRef.current = adDisplayContainer;

      const adsLoader = new google.ima.AdsLoader(adDisplayContainer);
      adsLoaderRef.current = adsLoader;

      adsLoader.addEventListener(
        google.ima.AdsManagerLoadedEvent.Type.ADS_MANAGER_LOADED,
        onAdsManagerLoaded,
        false
      );
      adsLoader.addEventListener(
        google.ima.AdErrorEvent.Type.AD_ERROR,
        onAdError,
        false
      );
    } catch (e) {
      console.error("Error initializing IMA loader:", e);
      setHasError(true);
    }

    return () => {
      destroyAds();
    };
  }, [isSdkLoaded, hasError]);

  const destroyAds = () => {
    try {
      if (adsManagerRef.current) {
        adsManagerRef.current.destroy();
      }
      if (adsLoaderRef.current) {
        adsLoaderRef.current.contentComplete();
      }
    } catch (e) {
      // Ignorer les erreurs d'extinction
    }
  };

  const onAdsManagerLoaded = (adsManagerLoadedEvent: any) => {
    try {
      const google = (window as any).google;
      const adsRenderingSettings = new google.ima.AdsRenderingSettings();
      adsRenderingSettings.restoreHeaderAd = true;

      const adsManager = adsManagerLoadedEvent.getAdsManager(
        videoRef.current,
        adsRenderingSettings
      );
      adsManagerRef.current = adsManager;

      adsManager.addEventListener(
        google.ima.AdErrorEvent.Type.AD_ERROR,
        onAdError
      );
      adsManager.addEventListener(
        google.ima.AdEvent.Type.CONTENT_PAUSE_REQUESTED,
        () => {
          if (videoRef.current) videoRef.current.pause();
        }
      );
      adsManager.addEventListener(
        google.ima.AdEvent.Type.CONTENT_RESUME_REQUESTED,
        () => {
          if (videoRef.current) videoRef.current.play();
        }
      );
      adsManager.addEventListener(
        google.ima.AdEvent.Type.COMPLETE,
        onAdComplete
      );
      adsManager.addEventListener(
        google.ima.AdEvent.Type.ALL_ADS_COMPLETED,
        onAdComplete
      );
      
      adsManager.addEventListener(
        google.ima.AdEvent.Type.AD_PROGRESS,
        (adEvent: any) => {
          const adData = adEvent.getAdData();
          if (adData && adData.duration) {
            setProgress((adData.currentTime / adData.duration) * 100);
          }
        }
      );
    } catch (e) {
      console.error("Error setting up AdsManager:", e);
      setHasError(true);
    }
  };

  const onAdComplete = () => {
    setIsDone(true);
    setProgress(100);
    destroyAds();
  };

  const onAdError = (adErrorEvent: any) => {
    console.error("IMA SDK Ad Error:", adErrorEvent?.getError?.() || adErrorEvent);
    setHasError(true);
  };

  const startAdPlayback = () => {
    if (hasError) return;

    try {
      const google = (window as any).google;
      
      if (adDisplayContainerRef.current) {
        adDisplayContainerRef.current.initialize();
      }

      const adsRequest = new google.ima.AdsRequest();
      adsRequest.adTagUrl = AD_TAG_URL;
      
      const width = adContainerRef.current?.clientWidth || 640;
      const height = adContainerRef.current?.clientHeight || 360;
      adsRequest.linearAdSlotWidth = width;
      adsRequest.linearAdSlotHeight = height;
      adsRequest.nonLinearAdSlotWidth = width;
      adsRequest.nonLinearAdSlotHeight = height;

      setIsAdStarted(true);

      adsLoaderRef.current.requestAds(adsRequest);

      setTimeout(() => {
        if (adsManagerRef.current) {
          try {
            adsManagerRef.current.init(width, height, google.ima.ViewMode.NORMAL);
            adsManagerRef.current.start();
          } catch (managerError) {
            console.error("AdsManager init/start error:", managerError);
            setHasError(true);
          }
        }
      }, 500);

    } catch (e) {
      console.error("Error starting ad playback:", e);
      setHasError(true);
    }
  };

  // Logique du lecteur vidéo de secours (fallback local)
  const fallbackVideoUrl = FALLBACK_VIDEO_SOURCES[actionType];

  const handleFallbackTimeUpdate = () => {
    if (videoRef.current) {
      const current = videoRef.current.currentTime;
      const duration = videoRef.current.duration || 1;
      setProgress((current / duration) * 100);
    }
  };

  const handleFallbackEnded = () => {
    setIsDone(true);
    setProgress(100);
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
              <h3 className="text-xl font-black italic uppercase text-white">Sponsor Réel (IMA SDK)</h3>
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
              <div className="absolute inset-0 w-full h-full flex flex-col items-center justify-center p-6 space-y-4">
                <video
                  ref={videoRef}
                  src={fallbackVideoUrl}
                  autoPlay
                  muted
                  onTimeUpdate={handleFallbackTimeUpdate}
                  onEnded={handleFallbackEnded}
                  className="absolute inset-0 w-full h-full object-cover"
                />
                <div className="z-10 bg-black/60 p-2 rounded-lg border border-yellow-500/20 text-yellow-500 text-[10px] uppercase font-bold tracking-widest flex items-center gap-1.5 animate-pulse">
                  <AlertTriangle size={12} /> Ad-Blocker détecté / Repli Actif
                </div>
              </div>
            ) : isDone ? (
              <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="z-10">
                <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto animate-bounce" />
                <h4 className="text-sm font-black uppercase text-yellow-500 mt-2">{sponsor.name}</h4>
                <p className="text-xs text-gray-400 font-mono italic">Sponsor visionné avec succès !</p>
              </motion.div>
            ) : !isAdStarted ? (
              <div className="space-y-4 p-6 z-10 flex flex-col items-center">
                <Film className="w-12 h-12 text-yellow-500 animate-pulse" />
                <div className="space-y-1">
                  <h4 className="text-sm font-black uppercase text-yellow-500">{sponsor.name}</h4>
                  <p className="text-xs text-gray-400 font-mono italic">Cliquez ci-dessous pour charger la vidéo</p>
                </div>
                <button
                  onClick={startAdPlayback}
                  className="mt-2 py-2.5 px-6 bg-yellow-500 hover:bg-yellow-600 active:scale-95 text-black font-black text-xs uppercase tracking-wider rounded-xl transition-all flex items-center gap-2"
                >
                  <Play size={12} fill="currentColor" /> Lancer le Sponsor
                </button>
              </div>
            ) : (
              <>
                <video
                  ref={videoRef}
                  className="absolute inset-0 w-full h-full object-cover pointer-events-none"
                  muted
                  playsInline
                />
                <div 
                  ref={adContainerRef} 
                  className="absolute inset-0 w-full h-full z-10" 
                />
              </>
            )}
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-[10px] font-bold uppercase tracking-wider text-gray-500 font-mono">
              <span>{isDone ? 'Complété' : 'Lecture Publicitaire...'}</span>
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

### Task 2: Validation et Tests

**Files:**
- Modify: `frontend/src/pages/billing/__tests__/PricingPage.test.tsx`

- [ ] **Step 1: Lancer les tests frontend**

S'assurer que la page de tests unitaires passe toujours avec le nouveau composant (repli JSDOM automatique en action) :
Run: `npx vitest run src/pages/billing/`
Expected: PASS

- [ ] **Step 2: Commiter et Pousser**

```bash
git add frontend/src/features/billing/components/SponsorStreamModal.tsx
git commit -m "feat(frontend): integrate real programmatic video ads with Google IMA SDK and smart ad-blocker fallback"
git push origin main
```
