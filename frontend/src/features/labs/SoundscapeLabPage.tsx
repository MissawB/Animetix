import React from 'react';
import { Volume2, Music, Sparkles } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

const SoundscapeLabPage: React.FC = () => {
  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-16 text-center">
        <Volume2 className="w-24 h-24 text-emerald-500 mx-auto mb-8 opacity-20" />
        <h1 className="text-6xl font-black italic manga-font mb-4 tracking-tighter uppercase">
          SOUNDSCAPE <span className="text-emerald-500">LAB</span>
        </h1>
        <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] mb-12">
            Génération d'ambiances sonores par IA AudioLDM.
        </p>
        
        <Card padding="lg" className="max-w-2xl mx-auto border-dashed border-white/10 bg-white/5">
            <Music className="w-12 h-12 text-white/10 mx-auto mb-6" />
            <h2 className="text-2xl font-black italic manga-font uppercase mb-4">Module en cours de déploiement</h2>
            <p className="text-sm font-bold opacity-40 uppercase leading-relaxed tracking-wider">
                Le moteur AudioLDM v2 est en cours de synchronisation avec le cluster de calcul. 
                Revenez très bientôt pour générer vos propres OST d'anime.
            </p>
        </Card>
      </div>
    </AnimatedPage>
  );
};

export default SoundscapeLabPage;
