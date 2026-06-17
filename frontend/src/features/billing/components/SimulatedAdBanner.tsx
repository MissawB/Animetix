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
  const [sponsor] = useState(() => SPONSORS[Math.floor(Math.random() * SPONSORS.length)]);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    // Log Banner Impression
    fetch('/api/v1/billing/log_ad_event/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_type: 'impression', ad_type: 'banner' })
    }).catch(err => console.error('Failed to log ad impression', err));
  }, []);

  const handleCtaClick = () => {
    // Log Banner Click
    fetch('/api/v1/billing/log_ad_event/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_type: 'click', ad_type: 'banner' })
    }).catch(err => console.error('Failed to log ad click', err));

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
        <button 
          onClick={handleCtaClick}
          className="relative aspect-[8/3] w-full rounded-lg overflow-hidden border border-white/5 cursor-pointer hover:opacity-90 transition-opacity bg-transparent p-0 block"
          aria-label={`Visiter ${sponsor.name}`}
        >
          <img 
            src={sponsor.image} 
            alt="" 
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLElement).style.display = 'none';
            }}
          />
        </button>

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
export default SimulatedAdBanner;
