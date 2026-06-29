import React, { useEffect } from 'react';
import { logAdEvent } from '../services/billingService';
import { usePassiveMiningStore } from '../../../store/passiveMiningStore';

// Real Google AdSense display unit. Configure via env:
//   VITE_ADSENSE_CLIENT = ca-pub-xxxxxxxxxxxxxxxx   (publisher id)
//   VITE_ADSENSE_SLOT_* = the ad-unit slot id for each placement
// Without those (e.g. local dev, or before the AdSense account is approved) we
// render a clear placeholder instead — AdSense never serves on localhost anyway.
const ADSENSE_CLIENT = import.meta.env.VITE_ADSENSE_CLIENT as string | undefined;

declare global {
  interface Window {
    adsbygoogle?: Record<string, unknown>[];
  }
}

let scriptRequested = false;
function loadAdSenseScript(client: string) {
  if (scriptRequested || typeof document === 'undefined') return;
  scriptRequested = true;
  const s = document.createElement('script');
  s.async = true;
  s.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${client}`;
  s.crossOrigin = 'anonymous';
  s.setAttribute('data-adsense', 'true');
  document.head.appendChild(s);
}

interface AdSlotProps {
  /** AdSense ad-unit slot id (data-ad-slot). */
  slot?: string;
  /** AdSense format hint (data-ad-format). */
  format?: string;
  className?: string;
  /** When true, this ad's visibility funds passive Bx mining while it is mounted. */
  fundsMining?: boolean;
  label?: string;
}

/**
 * Une vraie pub AdSense. Tant qu'elle est montée, elle alimente le minage passif
 * (via le compteur du store) — c'est ce qui « finance » les Bx crédités.
 */
export const AdSlot: React.FC<AdSlotProps> = ({
  slot,
  format = 'auto',
  className = '',
  fundsMining = true,
  label = 'Publicité',
}) => {
  const registerAd = usePassiveMiningStore((s) => s.registerAd);
  const unregisterAd = usePassiveMiningStore((s) => s.unregisterAd);
  const hasRealAds = Boolean(ADSENSE_CLIENT && slot);

  // Impression tracking + mining registration for the lifetime of the slot.
  useEffect(() => {
    logAdEvent('impression', 'banner');
    if (fundsMining) registerAd();
    return () => {
      if (fundsMining) unregisterAd();
    };
  }, [fundsMining, registerAd, unregisterAd]);

  // Ask AdSense to fill the unit once the script is in place.
  useEffect(() => {
    if (!hasRealAds) return;
    loadAdSenseScript(ADSENSE_CLIENT as string);
    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch (e) {
      console.error('AdSense push failed', e);
    }
  }, [hasRealAds]);

  if (!hasRealAds) {
    return (
      <div
        className={`relative overflow-hidden rounded-2xl border border-dashed border-white/15 bg-black/40 ${className}`}
        aria-label={label}
      >
        <span className="absolute top-2 right-2 text-[8px] font-black uppercase tracking-widest text-gray-500 border border-white/10 rounded px-2 py-0.5">
          {label}
        </span>
        <div className="flex items-center justify-center min-h-[90px] text-[10px] font-mono uppercase tracking-widest text-gray-600">
          Espace publicitaire
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`} aria-label={label}>
      <span className="absolute top-1 right-2 z-10 text-[8px] font-black uppercase tracking-widest text-gray-500">
        {label}
      </span>
      <ins
        className="adsbygoogle"
        style={{ display: 'block' }}
        data-ad-client={ADSENSE_CLIENT}
        data-ad-slot={slot}
        data-ad-format={format}
        data-full-width-responsive="true"
      />
    </div>
  );
};

export default AdSlot;
