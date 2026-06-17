import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Zap, 
  Battery, 
  Play, 
  CheckCircle2,
  History, 
  TrendingUp,
  AlertCircle,
  Cpu,
  Unplug,
  ShieldCheck,
  Heart,
  Coffee,
  Star
} from 'lucide-react';
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { useAuthStore } from "../../store/authStore";
import { apiClient } from '../../utils/apiClient';
import { useToastStore } from "../../store/toastStore";

interface WalletTransaction {
  amount: number;
  type: string;
  description: string;
  date: string;
}

const PowerStationPage: React.FC = () => {
  const { user, refetchUser } = useAuthStore();
  const { addToast } = useToastStore();
  
  const [isWatching, setIsWatching] = useState(false);
  const [watchProgress, setWatchProgress] = useState(0);
  const [isCrediting, setIsCrediting] = useState(false);
  const [walletHistory, setWalletHistory] = useState<WalletTransaction[]>([]);

  useEffect(() => {
    const fetchBalance = async () => {
      try {
        const data = await apiClient('/api/v1/billing/wallet/balance/');
        setWalletHistory(data.history || []);
      } catch (_err) {
        console.error("Failed to fetch wallet data:", err);
      }
    };
    if (user) fetchBalance();
  }, [user]);

  const handleWatchAd = () => {
    setIsWatching(true);
    setWatchProgress(0);
    
    const duration = 15000; // 15 secondes pour la démo
    const interval = 100;
    const steps = duration / interval;
    
    let currentStep = 0;
    const timer = setInterval(() => {
      currentStep++;
      setWatchProgress((currentStep / steps) * 100);
      
      if (currentStep >= steps) {
        clearInterval(timer);
        completeAd();
      }
    }, interval);
  };

  const completeAd = async () => {
    setIsCrediting(true);
    try {
      const res = await apiClient('/api/v1/billing/wallet/watch-ad/', { method: 'POST' });
      addToast(`Énergie injectée : +${res.earned} Bx !`, 'success');
      await refetchUser();
      // Refresh history
      const data = await apiClient('/api/v1/billing/wallet/balance/');
      setWalletHistory(data.history || []);
    } catch (_err) {
      addToast("Erreur lors de la recharge.", "error");
    } finally {
      setIsWatching(false);
      setIsCrediting(false);
      setWatchProgress(0);
    }
  };

  const buyPack = async (amount: number, price: string) => {
    addToast(`Redirection vers Stripe pour le pack ${amount} Bx (${price})...`, 'info');
    // Simulation d'achat direct
    setTimeout(async () => {
       try {
         // Appeler un endpoint de mock pour créditer
         await apiClient('/api/v1/profiles/refill_quota/', { method: 'POST' }); // Réutilise l'ancien refill pour le test
         addToast("Achat réussi (Simulé) !", "success");
         await refetchUser();
       } catch (_e) {
         // Erreur gérée par le toast ou silencieuse en simulation
       }
    }, 2000);
  };

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#050505] text-white pt-24 pb-32 px-6 bg-manga-overlay">
        <div className="max-w-6xl mx-auto space-y-12">
          
          <header className="flex flex-col md:flex-row justify-between items-end gap-6 mb-16">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-blue-500/20 rounded-2xl border border-blue-500/30">
                  <Battery className="w-8 h-8 text-blue-500 animate-pulse" />
                </div>
                <h1 className="text-5xl md:text-7xl font-black italic uppercase tracking-tighter manga-font">
                  POWER <span className="text-blue-500 text-glow">STATION</span>
                </h1>
              </div>
              <p className="text-gray-500 font-bold uppercase tracking-[0.2em] text-xs">
                Injectez de l'énergie neuronale dans votre profil Animetix.
              </p>
            </div>
            
            <div className="bg-white/5 border border-white/10 p-6 rounded-[2rem] flex items-center gap-6 shadow-2xl backdrop-blur-xl">
              <div className="text-right">
                <span className="text-[10px] font-black uppercase text-gray-500 tracking-widest block mb-1">Solde Actuel</span>
                <span className="text-4xl font-black italic text-white manga-font">{user?.wallet_balance?.toLocaleString() || 0} <span className="text-blue-500">Bx</span></span>
              </div>
              <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(59,130,246,0.5)]">
                <Zap className="w-6 h-6 text-black fill-current" />
              </div>
            </div>
          </header>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
            
            {/* Active Recharge (Ads) */}
            <Card padding="none" className="lg:col-span-2 bg-gradient-to-br from-blue-900/20 to-transparent border-white/10 rounded-[3rem] overflow-hidden relative group">
              <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none">
                <Cpu className="w-64 h-64 text-blue-500" />
              </div>
              
              <div className="p-12 space-y-8 relative z-10">
                <div className="space-y-2">
                  <h2 className="text-3xl font-black italic uppercase manga-font tracking-tight">Injection Gratuite</h2>
                  <p className="text-gray-400 text-sm font-bold uppercase tracking-wider">Visionnez un spot sponsorisé pour recharger votre batterie.</p>
                </div>

                <div className="aspect-video bg-black/60 rounded-[2rem] border-2 border-white/5 flex flex-col items-center justify-center relative overflow-hidden group/screen">
                  {isWatching ? (
                    <div className="w-full h-full flex flex-col items-center justify-center p-12 space-y-6">
                      <div className="text-blue-400 font-black italic manga-font text-2xl animate-pulse">TRANSMISSION EN COURS...</div>
                      <div className="w-full max-w-md h-3 bg-white/10 rounded-full overflow-hidden">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${watchProgress}%` }}
                          className="h-full bg-blue-500 shadow-[0_0_15px_rgba(59,130,246,1)]"
                        />
                      </div>
                      <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Ne quittez pas la page pour valider les Bx</p>
                    </div>
                  ) : (
                    <>
                      <div className="absolute inset-0 bg-blue-500/5 group-hover/screen:bg-blue-500/10 transition-colors" />
                      <Button 
                        size="lg" 
                        className="rounded-full w-24 h-24 p-0 flex items-center justify-center bg-blue-500 hover:bg-blue-400 shadow-[0_0_30px_rgba(59,130,246,0.4)] transition-all hover:scale-110"
                        onClick={handleWatchAd}
                        disabled={isCrediting}
                      >
                        <Play className="w-10 h-10 text-black fill-current ml-1" />
                      </Button>
                      <span className="mt-6 text-xs font-black uppercase tracking-[0.3em] text-blue-400">Démarrer le flux (+250 Bx)</span>
                    </>
                  )}
                </div>

                <div className="flex items-center gap-6 pt-4">
                   <div className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase italic">
                     <ShieldCheck className="w-4 h-4 text-green-500" /> Sécurisé par NeuralGuard
                   </div>
                   <div className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase italic">
                     <CheckCircle2 className="w-4 h-4 text-blue-500" /> Flux Haute Fidélité
                   </div>
                </div>
              </div>
            </Card>

            {/* Direct Purchase (Stripe) */}
            <div className="space-y-8">
              <h3 className="text-sm font-black uppercase tracking-[0.3em] text-gray-500 border-l-4 border-blue-500 pl-4">Achat Direct (Stripe)</h3>
              
              <button 
                onClick={() => buyPack(10000, "4.99€")}
                className="w-full p-8 rounded-[2rem] bg-white/5 border border-white/10 hover:border-blue-500/50 hover:bg-blue-500/5 transition-all text-left group"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="p-3 bg-blue-500/10 rounded-xl group-hover:bg-blue-500 group-hover:text-black transition-colors">
                    <Zap className="w-6 h-6" />
                  </div>
                  <span className="text-xl font-black text-white">4.99€</span>
                </div>
                <div className="text-2xl font-black italic manga-font uppercase mb-1 text-white">Pack Initié</div>
                <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">10 000 Berrix (Bx) + Badge Bronze</p>
              </button>

              <button 
                onClick={() => buyPack(25000, "9.99€")}
                className="w-full p-8 rounded-[2rem] bg-blue-500 border border-blue-400 hover:bg-blue-400 transition-all text-left shadow-[0_0_40px_rgba(59,130,246,0.2)]"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="p-3 bg-black/20 rounded-xl text-white">
                    <TrendingUp className="w-6 h-6" />
                  </div>
                  <span className="text-xl font-black text-black">9.99€</span>
                </div>
                <div className="text-2xl font-black italic manga-font uppercase mb-1 text-black">Pack Elite</div>
                <p className="text-[10px] text-blue-900 font-black uppercase tracking-widest">25 000 Berrix (Bx) + Badge Argent</p>
              </button>

              <div className="p-8 rounded-[2.5rem] bg-white/5 border border-dashed border-white/20 text-center">
                 <Unplug className="w-10 h-10 text-gray-600 mx-auto mb-4" />
                 <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest leading-relaxed">
                   Le minage passif (+20 Bx / 3 min) est actif sur toutes les pages de jeux.
                 </p>
              </div>
            </div>

          </div>

          {/* Donation / Support Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mt-20">
            <Card padding="none" className="bg-gradient-to-br from-pink-900/20 to-transparent border-white/10 rounded-[3rem] overflow-hidden relative group shadow-2xl">
              <div className="p-10 space-y-6 relative z-10 text-center md:text-left">
                <div className="flex flex-col md:flex-row items-center gap-4">
                  <div className="p-3 bg-pink-500/20 rounded-2xl border border-pink-500/30 shadow-[0_0_15px_rgba(236,72,153,0.3)]">
                    <Heart className="w-8 h-8 text-pink-500 animate-pulse fill-current" />
                  </div>
                  <div>
                    <h2 className="text-3xl font-black italic uppercase manga-font tracking-tight">Soutien Indépendant</h2>
                    <p className="text-[10px] text-gray-500 font-black uppercase tracking-[0.2em]">Animetix est maintenu par une équipe passionnée.</p>
                  </div>
                </div>

                <p className="text-sm text-gray-400 leading-relaxed font-bold uppercase tracking-wide italic">
                  Chaque don nous aide à couvrir les coûts GPU massifs et à garder le serveur <span className="text-pink-500">100% indépendant</span>. 
                  En guise de remerciement, débloquez des récompenses uniques.
                </p>

                <div className="flex flex-col sm:flex-row gap-4 pt-4">
                  <a 
                    href="https://ko-fi.com/animetix" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex-1 px-8 py-5 bg-[#29abe2] hover:bg-[#29abe2]/80 text-white font-black italic uppercase text-xs rounded-2xl shadow-xl transition-all hover:scale-[1.02] flex items-center justify-center gap-3 no-underline group"
                  >
                    <Coffee className="w-5 h-5 group-hover:rotate-12 transition-transform" /> Soutenir sur Ko-fi
                  </a>
                  <a 
                    href="https://patreon.com/animetix" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex-1 px-8 py-5 bg-[#f96854] hover:bg-[#f96854]/80 text-white font-black italic uppercase text-xs rounded-2xl shadow-xl transition-all hover:scale-[1.02] flex items-center justify-center gap-3 no-underline group"
                  >
                    <Star className="w-5 h-5 group-hover:scale-125 transition-transform fill-current" /> Devenir Patron
                  </a>
                </div>
              </div>
              
              <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none group-hover:scale-110 transition-transform duration-700">
                  <Heart className="w-40 h-48 text-pink-500 fill-current" />
              </div>
            </Card>

            <div className="bg-white/5 border border-white/10 rounded-[3rem] p-10 flex flex-col justify-center space-y-6 relative overflow-hidden backdrop-blur-md">
               <div className="absolute -bottom-20 -right-20 opacity-10 rotate-12">
                  <Zap className="w-64 h-64 text-yellow-500 fill-current" />
               </div>
               <h3 className="text-xl font-black italic uppercase manga-font tracking-tight flex items-center gap-3">
                 <Star className="w-5 h-5 text-yellow-500 fill-current" /> Cosmétiques Exclusifs
               </h3>
               <div className="grid grid-cols-1 gap-3">
                  {[
                    { label: "Badge 'Sponsor' permanent", detail: "Exhibez votre soutien sur chaque message." },
                    { label: "Couleur de Pseudo 'Gold'", detail: "Distinguez-vous dans le classement mondial." },
                    { label: "Avatars Animés (GIF)", detail: "Donnez vie à votre profil sur le Hub." },
                    { label: "Accès Prioritaire Labs", detail: "Testez les nouveaux modèles avant tout le monde." },
                    { label: "Canal Discord Privé", detail: "Échangez directement avec les créateurs." }
                  ].map((benefit, i) => (
                    <motion.div 
                      key={i}
                      initial={{ opacity: 0, x: 20 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="flex items-start gap-4 p-3 rounded-2xl hover:bg-white/5 transition-colors border border-transparent hover:border-white/5"
                    >
                      <CheckCircle2 className="w-5 h-5 text-pink-500 shrink-0 mt-0.5" />
                      <div>
                        <div className="text-[11px] font-black uppercase text-white tracking-widest">{benefit.label}</div>
                        <div className="text-[9px] text-gray-500 font-bold uppercase tracking-widest mt-0.5">{benefit.detail}</div>
                      </div>
                    </motion.div>
                  ))}
               </div>
            </div>
          </div>

          {/* History Section */}
          <div className="mt-20 space-y-8">
            <h3 className="text-2xl font-black italic uppercase manga-font flex items-center gap-3">
              <History className="w-6 h-6 text-blue-500" /> Flux Energétique Récent
            </h3>
            
            <div className="bg-white/5 border border-white/10 rounded-[2rem] overflow-hidden">
               {walletHistory.length > 0 ? (
                 <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-white/5 bg-white/5">
                        <th className="p-6 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">Transaction</th>
                        <th className="p-6 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">Source</th>
                        <th className="p-6 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">Date</th>
                        <th className="p-6 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 text-right">Montant</th>
                      </tr>
                    </thead>
                    <tbody>
                      {walletHistory.map((t, i) => (
                        <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                          <td className="p-6 font-bold text-sm">{t.description}</td>
                          <td className="p-6">
                            <span className={`text-[9px] font-black uppercase px-3 py-1 rounded-full border ${
                              t.type === 'ai_usage' ? 'border-red-500/30 text-red-500' : 'border-blue-500/30 text-blue-500'
                            }`}>
                              {t.type.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="p-6 text-xs text-gray-500 font-bold">{new Date(t.date).toLocaleString()}</td>
                          <td className={`p-6 text-right font-black italic manga-font ${t.amount > 0 ? 'text-green-500' : 'text-red-500'}`}>
                            {t.amount > 0 ? `+${t.amount}` : t.amount} Bx
                          </td>
                        </tr>
                      ))}
                    </tbody>
                 </table>
               ) : (
                 <div className="p-20 text-center space-y-4">
                    <AlertCircle className="w-12 h-12 text-gray-700 mx-auto" />
                    <p className="text-gray-500 font-bold uppercase tracking-widest text-sm">Aucune transaction détectée sur ce nœud.</p>
                 </div>
               )}
            </div>
          </div>

        </div>
      </div>
    </AnimatedPage>
  );
};

export default PowerStationPage;
