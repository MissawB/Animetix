import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, Cpu, CheckCircle, Sparkles, X } from 'lucide-react';
import { Button } from '../../../components/ui/Button';

interface PricingTier {
  id: string;
  name: string;
  price: number;
  features: string[];
}

interface Props {
  tier: PricingTier;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}

export const NexusGatewayModal: React.FC<Props> = ({ tier, onClose, onConfirm }) => {
  const [status, setStatus] = useState<'idle' | 'processing' | 'success'>('idle');

  const handleConfirm = async () => {
    setStatus('processing');
    await new Promise(r => setTimeout(r, 2500));
    try {
        await onConfirm();
        setStatus('success');
    } catch (_e) {
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
                  <h3 className="text-2xl font-black italic uppercase">Confirmation Transaction</h3>
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
