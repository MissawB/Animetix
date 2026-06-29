import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Sparkles} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from "../../store/authStore";
import { updateAccountSettings } from '../../api';
import { apiClient } from '../../utils/apiClient';
import { useToastStore } from "../../store/toastStore";
import { Button } from "../../components/ui/Button";
import { SponsorStreamModal } from '../../features/billing/components/SponsorStreamModal';
import { AdSlot } from '../../features/billing/components/AdSlot';

const PRICING_AD_SLOT = import.meta.env.VITE_ADSENSE_SLOT_SIDEBAR as string | undefined;

export const PricingPage: React.FC = () => {
  const { user, checkAuth, refetchUser } = useAuthStore();
  const navigate = useNavigate();
  const { addToast } = useToastStore();
  const [activeModal, setActiveModal] = useState<'boost' | 'refill' | null>(null);
  const [isClaiming, setIsClaiming] = useState(false);

  const handleConfirmBoost = async () => {
    try {
      await updateAccountSettings({ tier: 'premium' });
      await checkAuth();
      addToast("Statut Boosté activé avec succès pour 24H !", "success");
    } catch (error) {
      console.error('Failed to update tier:', error);
      addToast("Erreur lors de l'activation du boost.", "error");
      throw error;
    }
  };

  const handleConfirmRefill = async () => {
    try {
      await apiClient('/api/v1/profiles/refill_quota/', { method: 'POST' });
      await checkAuth();
      addToast("Votre quota quotidien a été rechargé !", "success");
    } catch (error) {
      console.error('Failed to refill quota:', error);
      addToast("Erreur lors de la recharge de quota.", "error");
      throw error;
    }
  };

  const handleAction = (type: 'boost' | 'refill') => {
    if (!user) {
      navigate('/login?redirect=/pricing/');
      return;
    }
    setActiveModal(type);
  };

  const handleClaimDonation = async () => {
    if (!user) {
      navigate('/login?redirect=/pricing/');
      return;
    }
    setIsClaiming(true);
    try {
      await apiClient('/api/v1/profiles/claim_donation/', { method: 'POST' });
      await refetchUser();
      addToast("Merci pour votre soutien ! Badge Sponsor Or et couleur de pseudo débloqués.", "success");
    } catch (error) {
      console.error('Failed to claim donation:', error);
      addToast("Erreur lors de la validation du don.", "error");
    } finally {
      setIsClaiming(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white pt-24 pb-32 px-6">
      <div className="max-w-6xl mx-auto space-y-12">
        <header className="text-center mb-16 space-y-4">
          <h1 className="text-5xl md:text-7xl font-black italic uppercase tracking-tighter manga-font">
            Centre de <span className="text-yellow-500 text-glow">Sponsoring & Boost</span>
          </h1>
          <p className="text-gray-500 font-bold uppercase tracking-[0.2em] text-xs">
            Financez le moteur IA par la publicité et accédez au niveau supérieur
          </p>
        </header>

        {user && (
          <div className="max-w-md mx-auto bg-white/5 border border-white/5 p-6 rounded-3xl text-center space-y-4">
            <h3 className="text-xs font-black uppercase tracking-widest text-gray-400">Votre Statut Actuel</h3>
            <div className="flex justify-center items-center gap-3">
              <span className={`px-4 py-1.5 rounded-full text-xs font-black uppercase tracking-wider ${
                user.tier === 'premium' 
                  ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' 
                  : 'bg-gray-500/20 text-gray-400 border border-white/5'
              }`}>
                {user.tier === 'premium' ? 'Statut Boosté' : 'Statut Standard'}
              </span>
            </div>
            <p className="text-xs text-gray-500">
              {user.tier === 'premium' 
                ? 'Profitez d\'un accès illimité aux clubs et d\'un quota x5.' 
                : 'Quota standard actif. Regardez un sponsor ci-dessous pour booster votre compte.'}
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {/* Option Standard / Quota Refill */}
          <motion.div whileHover={{ y: -5 }} className="bg-white/5 border border-white/5 p-8 rounded-3xl space-y-6 flex flex-col justify-between">
            <div className="space-y-4">
              <div>
                <p className="text-[9px] font-black uppercase opacity-40">Option 01</p>
                <h2 className="text-2xl font-black italic uppercase">Recharge Quota</h2>
              </div>
              <p className="text-3xl font-black text-white">GRATUIT</p>
              <p className="text-xs text-gray-400 leading-relaxed">
                Réinitialisez immédiatement votre compteur de requêtes IA pour la journée. Idéal si vous êtes bloqué au milieu d'une session d'exploration intense.
              </p>
              <ul className="space-y-3 pt-2">
                <li className="flex items-center gap-2.5 text-xs text-gray-300">
                  <Check className="w-4 h-4 text-green-500" /> Remise à zéro instantanée
                </li>
                <li className="flex items-center gap-2.5 text-xs text-gray-300">
                  <Check className="w-4 h-4 text-green-500" /> Sponsor ultra-rapide (4 secondes)
                </li>
              </ul>
            </div>
            <Button
              variant="outline"
              fullWidth
              className="py-5 font-black uppercase italic tracking-wider mt-6"
              onClick={() => handleAction('refill')}
            >
              RECHARGER MON QUOTA
            </Button>
          </motion.div>

          {/* Option Boosté / Premium 24H */}
          <motion.div whileHover={{ y: -5 }} className="relative bg-yellow-950/10 border-2 border-yellow-500/40 p-8 rounded-3xl space-y-6 flex flex-col justify-between shadow-[0_0_30px_rgba(234,179,8,0.1)]">
            <div className="absolute -top-3 right-6 bg-yellow-500 text-black text-[9px] font-black uppercase px-3 py-1 rounded-full italic">
              RECOMMANDÉ
            </div>
            <div className="space-y-4">
              <div>
                <p className="text-[9px] font-black uppercase opacity-40">Option 02</p>
                <h2 className="text-2xl font-black italic uppercase text-yellow-500">Boost Cyber-Nexus</h2>
              </div>
              <p className="text-3xl font-black text-yellow-500">GRATUIT <span className="text-xs font-mono text-gray-400">/ 24H</span></p>
              <p className="text-xs text-gray-300 leading-relaxed">
                Débloquez toutes les fonctionnalités premium : quota IA boosté (x5), création illimitée de clubs de fans et accès au visualiseur de graphe.
              </p>
              <ul className="space-y-3 pt-2">
                <li className="flex items-center gap-2.5 text-xs text-gray-200">
                  <Check className="w-4 h-4 text-yellow-500" /> Quota IA augmenté (x5)
                </li>
                <li className="flex items-center gap-2.5 text-xs text-gray-200">
                  <Check className="w-4 h-4 text-yellow-500" /> Visualiseur de Graphe complet
                </li>
                <li className="flex items-center gap-2.5 text-xs text-gray-200">
                  <Check className="w-4 h-4 text-yellow-500" /> Suppression totale des bannières pubs
                </li>
              </ul>
            </div>
            <Button
              variant="primary"
              fullWidth
              className="py-5 font-black uppercase italic tracking-wider mt-6"
              onClick={() => handleAction('boost')}
              disabled={user?.tier === 'premium'}
            >
              {user?.tier === 'premium' ? 'BOOST ACTIF' : 'ACTIVER LE BOOST'}
            </Button>
          </motion.div>
        </div>

        {/* Financement Participatif */}
        <div className="max-w-4xl mx-auto bg-gradient-to-r from-amber-500/10 via-yellow-500/5 to-transparent border border-yellow-500/20 p-8 rounded-3xl space-y-6 relative overflow-hidden shadow-[0_0_50px_rgba(245,158,11,0.05)]">
          <div className="absolute top-0 right-0 p-8 opacity-5">
            <Sparkles className="w-48 h-48 text-yellow-500" />
          </div>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
            <div className="space-y-3 max-w-xl">
              <span className="bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest flex items-center gap-1.5 w-fit">
                <Sparkles className="w-3.5 h-3.5" /> Soutenir Animetix
              </span>
              <h3 className="text-2xl font-black italic uppercase tracking-tight manga-font text-white">
                Financement Participatif (Dons)
              </h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                Aidez-nous à payer les serveurs et les APIs de modèles d'IA ! En guise de remerciement, vous débloquerez un badge exclusif <span className="text-yellow-400 font-bold">"Sponsor Or"</span> sur votre profil public ainsi que la possibilité de <span className="text-yellow-400 font-bold">personnaliser la couleur de votre pseudo</span>.
              </p>
            </div>
            <div className="flex flex-col gap-3 min-w-[240px]">
              <a
                href="https://ko-fi.com/animetix"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2.5 bg-[#FF5E5B] hover:bg-[#ff4c48] text-white font-black uppercase tracking-wider text-xs py-3.5 px-6 rounded-2xl shadow-lg shadow-[#FF5E5B]/15 transition-all text-center no-underline hover:scale-[1.02]"
              >
                ☕ Soutenir sur Ko-fi
              </a>
              <a
                href="https://patreon.com/animetix"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2.5 bg-[#FF424D] hover:bg-[#e03a44] text-white font-black uppercase tracking-wider text-xs py-3.5 px-6 rounded-2xl shadow-lg shadow-[#FF424D]/15 transition-all text-center no-underline hover:scale-[1.02]"
              >
                🎁 Devenir Patron (Patreon)
              </a>
            </div>
          </div>
          
          <div className="border-t border-white/5 pt-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <p className="text-[10px] font-black uppercase text-gray-400">Déjà donateur ?</p>
              <p className="text-xs text-gray-500">Récupérez et appliquez instantanément vos cosmétiques en simulant la validation ci-contre.</p>
            </div>
            <Button
              variant="outline"
              className="border-yellow-500/30 text-yellow-500 hover:bg-yellow-500 hover:text-black font-black uppercase italic tracking-wider py-4 px-6 text-xs"
              onClick={handleClaimDonation}
              disabled={isClaiming}
            >
              {isClaiming ? "Vérification..." : user?.unlocked_badges?.includes("Sponsor Or") ? "COSMÉTIQUES DÉBLOQUÉS !" : "Valider mon don & débloquer"}
            </Button>
          </div>
        </div>

        {/* Espace Développeur */}
        <div className="max-w-4xl mx-auto border border-red-500/20 bg-red-950/5 p-6 rounded-3xl flex justify-between items-center">
          <div className="space-y-1">
            <h3 className="text-sm font-black uppercase text-red-500">Accès API Développeur</h3>
            <p className="text-xs text-gray-400">Pour intégrer le moteur RAG d'Animetix à vos projets. Aucun abonnement requis.</p>
          </div>
          <Button variant="outline" className="border-red-500/30 text-red-500 hover:bg-red-500 hover:text-white" onClick={() => navigate('/auth/settings/')}>
            GÉRER MA CLÉ API
          </Button>
        </div>

        {/* Real ad banner (AdSense) */}
        <div className="max-w-md mx-auto">
          <AdSlot slot={PRICING_AD_SLOT} format="rectangle" fundsMining={false} />
        </div>

      </div>

      <AnimatePresence>
        {activeModal && (
          <SponsorStreamModal
            actionType={activeModal}
            onClose={() => setActiveModal(null)}
            onConfirm={activeModal === 'boost' ? handleConfirmBoost : handleConfirmRefill}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default PricingPage;
