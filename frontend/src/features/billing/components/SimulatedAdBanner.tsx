import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ExternalLink, Sparkles, X } from 'lucide-react';

const SPONSORS = [
  {
    name: 'Capsule Corp',
    slogan: 'Le transport de demain dans le creux de votre main !',
    cta: 'Découvrir les Hoipoi',
    color: 'from-blue-600 to-cyan-500'
  },
  {
    name: 'Future Gadget Lab',
    slogan: 'PhoneWave (Nom Temporaire) : réchauffez vos bananes et le temps.',
    cta: 'Devenir membre 001',
    color: 'from-green-600 to-emerald-500'
  },
  {
    name: 'NERV Recruiting',
    slogan: 'Protégez Tokyo-3. Postulez pour piloter un EVA dès aujourd\'hui.',
    cta: 'S\'engager',
    color: 'from-red-600 to-orange-500'
  },
  {
    name: 'Ichiraku Ramen',
    slogan: 'Le bouillon légendaire qui nourrit les Hokage. Bol spécial dispo !',
    cta: 'Commander',
    color: 'from-yellow-500 to-orange-600'
  },
  {
    name: 'Arasaka Corp',
    slogan: 'Équipez-vous du meilleur cyberware militaire de Night City.',
    cta: 'S\'équiper',
    color: 'from-purple-600 to-pink-500'
  }
];

export const SimulatedAdBanner: React.FC = () => {
  const navigate = useNavigate();
  const [sponsor, setSponsor] = useState(SPONSORS[0]);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const random = SPONSORS[Math.floor(Math.random() * SPONSORS.length)];
    setSponsor(random);
  }, []);

  if (!visible) return null;

  return (
    <div className="relative overflow-hidden rounded-2xl border-2 border-dashed border-yellow-500/30 bg-black/40 p-4 font-mono shadow-md backdrop-blur-md">
      <div className="absolute top-2 right-2 flex items-center gap-2">
        <span className="animate-pulse bg-yellow-500/20 text-yellow-400 text-[8px] font-black uppercase px-2 py-0.5 rounded border border-yellow-500/30">
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

      <div className="space-y-2 mt-2">
        <h4 className="text-xs font-black uppercase tracking-tight text-white flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-yellow-400" /> {sponsor.name}
        </h4>
        <p className="text-[10px] text-gray-400 font-medium leading-relaxed">
          {sponsor.slogan}
        </p>
        <button
          onClick={() => navigate('/pricing/')}
          className={`w-full text-center text-[10px] font-black uppercase tracking-wider py-2 px-3 rounded-lg bg-gradient-to-r ${sponsor.color} text-white flex items-center justify-center gap-1 hover:scale-[1.02] active:scale-95 transition-all mt-2`}
        >
          {sponsor.cta} <ExternalLink size={10} />
        </button>
        <p className="text-[8px] text-center text-gray-600 mt-1">
          Activer le Boost pour supprimer les publicités.
        </p>
      </div>
    </div>
  );
};
