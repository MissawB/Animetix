import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Cpu, Film, CheckCircle2, X } from 'lucide-react';
import { Button } from '../../../components/ui/Button';

interface Props {
  actionType: 'boost' | 'refill';
  onClose: () => void;
  onConfirm: () => Promise<void>;
}

const SPONSORS_CLIPS = [
  { name: "Capsule Corp", msg: "Capsulage moléculaire Hoipoi V10 en cours..." },
  { name: "Future Gadget Lab", msg: "Optimisation de l'onde temporelle du micro-ondes..." },
  { name: "NERV HQ", msg: "Synchronisation neurale EVA-01 active..." },
  { name: "Ichiraku Ramen", msg: "Préparation du bouillon de Konoha à 100°C..." }
];

export const SponsorStreamModal: React.FC<Props> = ({ actionType, onClose, onConfirm }) => {
  const [progress, setProgress] = useState(0);
  const [isDone, setIsDone] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [sponsor] = useState(() => SPONSORS_CLIPS[Math.floor(Math.random() * SPONSORS_CLIPS.length)]);
  
  const duration = actionType === 'boost' ? 7000 : 4000; // 7s pour le Boost, 4s pour la Recharge

  useEffect(() => {
    const interval = 50;
    const step = (interval / duration) * 100;
    
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(timer);
          setIsDone(true);
          return 100;
        }
        return prev + step;
      });
    }, interval);

    return () => clearInterval(timer);
  }, [duration]);

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
        onClick={!isDone && !isSubmitting ? onClose : undefined}
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
              <h3 className="text-xl font-black italic uppercase text-white">Lecture en Cours</h3>
            </div>
            {!isDone && !isSubmitting && (
              <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full text-gray-400 hover:text-white">
                <X size={16}/>
              </button>
            )}
          </header>

          <div className="relative aspect-video rounded-2xl bg-black border border-white/5 overflow-hidden flex flex-col items-center justify-center text-center p-6 space-y-4 shadow-inner">
            <div className="absolute inset-0 bg-grid-pattern opacity-10 pointer-events-none" />
            
            {isDone ? (
              <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
                <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto animate-bounce" />
              </motion.div>
            ) : (
              <Film className="w-12 h-12 text-yellow-500 animate-pulse" />
            )}

            <div className="space-y-1">
              <h4 className="text-sm font-black uppercase text-yellow-500">{sponsor.name}</h4>
              <p className="text-xs text-gray-400 font-mono italic">{sponsor.msg}</p>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-[10px] font-bold uppercase tracking-wider text-gray-500 font-mono">
              <span>{isDone ? 'Complété' : 'Chargement du Boost...'}</span>
              <span>{Math.min(100, Math.round(progress))}%</span>
            </div>
            <div className="w-full bg-gray-900 h-2.5 rounded-full overflow-hidden border border-white/5">
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
            {isSubmitting ? 'VALIDATION...' : isDone ? 'RÉCLAMER LE BONUS' : 'RESTEZ SUR LE FLUX'}
          </Button>
        </div>
      </motion.div>
    </div>
  );
};
