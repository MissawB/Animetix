import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Shield, Zap, Terminal, Cpu, ArrowRight, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from "../../store/authStore";
import { updateAccountSettings } from '../../api';
import { useToastStore } from "../../store/toastStore";
import { Button } from "../../components/ui/Button";
import { NexusGatewayModal } from '../../features/billing/components/NexusGatewayModal';

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
  const navigate = useNavigate();
  const [selectedTier, setSelectedTier] = useState<any>(null);

  const handleConfirm = async () => {
    if (!selectedTier) return;
    try {
      await updateAccountSettings({ tier: selectedTier.id });
      await checkAuth();
    } catch (error) {
      console.error('Failed to update tier:', error);
      throw error;
    }
  };

  const handleSelectTier = (tier: any) => {
    if (!user) {
      navigate('/login?redirect=/pricing/');
      return;
    }
    if (tier.id !== 'pro') {
      setSelectedTier(tier);
    }
  };

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
                  onClick={() => handleSelectTier(tier)}
                  disabled={user?.tier === tier.id}
                >
                  {user?.tier === tier.id ? 'ACTIF' : tier.id === 'pro' ? 'CONTACTER' : 'SÉLECTIONNER'}
                </Button>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      <AnimatePresence>
        {selectedTier && (
          <NexusGatewayModal
            tier={selectedTier}
            onClose={() => setSelectedTier(null)}
            onConfirm={handleConfirm}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default PricingPage;


