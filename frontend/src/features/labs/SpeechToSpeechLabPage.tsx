import React from 'react';
import { Mic, Radio, Zap } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

const SpeechToSpeechLabPage: React.FC = () => {
  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-16 text-center">
        <Mic className="w-24 h-24 text-blue-400 mx-auto mb-8 opacity-20" />
        <h1 className="text-6xl font-black italic manga-font mb-4 tracking-tighter uppercase">
          SPEECH-TO-SPEECH <span className="text-blue-400">LAB</span>
        </h1>
        <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] mb-12">
            Interaction vocale Zero-Latency avec vos personnages.
        </p>
        
        <Card padding="lg" className="max-w-2xl mx-auto border-dashed border-white/10 bg-white/5">
            <Radio className="w-12 h-12 text-white/10 mx-auto mb-6" />
            <h2 className="text-2xl font-black italic manga-font uppercase mb-4">Initialisation du Flux S2S</h2>
            <p className="text-sm font-bold opacity-40 uppercase leading-relaxed tracking-wider">
                L'infrastructure WebSocket pour le streaming vocal haute fidélité est en cours de configuration finale. 
                Bientôt, parlez directement à vos avatars d'anime favoris.
            </p>
        </Card>
      </div>
    </AnimatedPage>
  );
};

export default SpeechToSpeechLabPage;
