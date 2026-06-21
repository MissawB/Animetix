import React, { useState, useEffect, useCallback } from 'react';
import { Shield, Sparkles, AlertTriangle, Coins, RefreshCw, BarChart2, TrendingUp, HelpCircle } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

interface FinancialData {
  total_ai_cost: number;
  cost_by_engine: Record<string, number>;
  ad_stats: {
    video_impressions: number;
    banner_impressions: number;
    clicks: number;
  };
  donation_stats: {
    gold_sponsors: number;
    total_donations: number;
  };
  estimated_ad_revenue: number;
  total_revenue: number;
  net_margin: number;
  recommendation: string;
}

const FinancialDashboardPage: React.FC = () => {
  const [data, setData] = useState<FinancialData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Sliders simulation values
  const [videoCpm, setVideoCpm] = useState<number>(3.00);
  const [bannerCpm, setBannerCpm] = useState<number>(1.00);
  const [cpc, setCpc] = useState<number>(0.15);
  const [donationVal, setDonationVal] = useState<number>(5.00);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/billing/admin/financial-summary/');
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const json = await res.json();
      setData(json);
      setError(null);
    } catch (err) {
      const error = err as Error;
      setError(error.message || 'Erreur inconnue');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let ignore = false;
    if (loading) {
        setTimeout(() => {
            fetchData().then(() => {
                if (ignore) return;
            });
        }, 0);
    }
    return () => { ignore = true; };
  }, [fetchData, loading]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[500px] bg-[#fffcf0] dark:bg-[#1a1a2e]">
        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-4xl mx-auto p-8 mt-12 bg-red-500/10 border border-red-500/30 rounded-2xl text-center">
        <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-xl font-bold text-red-500">Erreur lors de la récupération des données financières</h3>
        <p className="text-gray-400 mt-2">{error}</p>
        <button onClick={fetchData} className="mt-6 px-4 py-2 bg-red-500 text-white rounded-xl font-bold text-xs uppercase">
          Réessayer
        </button>
      </div>
    );
  }

  // Live simulation calculations
  const simAdRevenue = 
    (data.ad_stats.video_impressions * (videoCpm / 1000)) + 
    (data.ad_stats.banner_impressions * (bannerCpm / 1000)) + 
    (data.ad_stats.clicks * cpc);

  const simDonations = data.donation_stats.gold_sponsors * donationVal;
  const simTotalRevenue = simAdRevenue + simDonations;
  const simNetMargin = simTotalRevenue - data.total_ai_cost;

  // Live breakeven calculations
  const isDeficit = simNetMargin < 0;
  const deficitVal = Math.abs(simNetMargin);
  const neededVideoImpressions = videoCpm > 0 ? Math.ceil((deficitVal / (videoCpm / 1000))) : 0;
  const neededClicks = cpc > 0 ? Math.ceil(deficitVal / cpc) : 0;

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] bg-[#fffcf0] dark:bg-[#1a1a2e] bg-manga-overlay transition-colors duration-500">
        <div className="max-w-7xl mx-auto px-6 py-12">
          
          {/* Header */}
          <div className="mb-12">
            <div className="flex items-center gap-3 text-blue-500 font-black uppercase tracking-widest text-xs mb-3">
              <Shield size={16} /> Dashboard Financier Admin
            </div>
            <h1 className="text-5xl font-black italic manga-font tracking-tighter uppercase text-black dark:text-white leading-none">
              EQUILIBRE <span className="text-blue-500">FINANCIER</span>
            </h1>
            <p className="text-gray-500 font-bold uppercase tracking-widest mt-2 text-xs">
              Calculez et équilibrez vos coûts d'IA avec la régie publicitaire
            </p>
          </div>

          {/* KPI Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card padding="md" className="border-2 border-red-500/20 bg-white dark:bg-[#0f0f1a]">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-wider text-gray-500 mb-1">Coût Total IA</p>
                  <h3 className="text-3xl font-black text-red-500">${data.total_ai_cost.toFixed(2)}</h3>
                </div>
                <Coins className="text-red-500 w-5 h-5" />
              </div>
              <p className="text-[10px] text-gray-400 mt-3 font-mono">Consommation cumulée des API</p>
            </Card>

            <Card padding="md" className="border-2 border-green-500/20 bg-white dark:bg-[#0f0f1a]">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-wider text-gray-500 mb-1">Revenus Pubs (Simulés)</p>
                  <h3 className="text-3xl font-black text-green-500">${simAdRevenue.toFixed(2)}</h3>
                </div>
                <TrendingUp className="text-green-500 w-5 h-5" />
              </div>
              <p className="text-[10px] text-gray-400 mt-3 font-mono">
                {data.ad_stats.video_impressions} videos • {data.ad_stats.clicks} clics
              </p>
            </Card>

            <Card padding="md" className="border-2 border-yellow-500/20 bg-white dark:bg-[#0f0f1a]">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-wider text-gray-500 mb-1">Dons (Sponsors Or)</p>
                  <h3 className="text-3xl font-black text-yellow-500">${simDonations.toFixed(2)}</h3>
                </div>
                <Sparkles className="text-yellow-500 w-5 h-5" />
              </div>
              <p className="text-[10px] text-gray-400 mt-3 font-mono">
                {data.donation_stats.gold_sponsors} sponsors or actifs
              </p>
            </Card>

            <Card padding="md" className={`border-2 bg-white dark:bg-[#0f0f1a] ${isDeficit ? 'border-red-500' : 'border-green-500'}`}>
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-wider text-gray-500 mb-1">Solde Net (Simulation)</p>
                  <h3 className={`text-3xl font-black ${isDeficit ? 'text-red-500' : 'text-green-500'}`}>
                    {isDeficit ? '-' : '+'}${deficitVal.toFixed(2)}
                  </h3>
                </div>
                <div className={`px-2 py-0.5 rounded text-[8px] font-black uppercase ${isDeficit ? 'bg-red-500/10 text-red-500 border border-red-500/30' : 'bg-green-500/10 text-green-500 border border-green-500/30'}`}>
                  {isDeficit ? 'Déficit' : 'Bénéfice'}
                </div>
              </div>
              <p className="text-[10px] text-gray-400 mt-3 font-mono">Total revenus - Coûts IA</p>
            </Card>
          </div>

          {/* Interactive Equalizer Section */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
            {/* Sliders Console */}
            <div className="lg:col-span-2 space-y-6">
              <Card padding="lg" className="bg-white dark:bg-[#0f0f1a]">
                <h3 className="text-xl font-black italic uppercase text-black dark:text-white mb-6 flex items-center gap-2">
                  <BarChart2 className="w-5 h-5 text-blue-500" /> CONSOLE D'ÉGALISATION INTERACTIVE
                </h3>
                
                <div className="space-y-6">
                  {/* Slider 1: Video CPM */}
                  <div>
                    <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">
                      <span>CPM Vidéo (pour 1000 vues)</span>
                      <span className="text-blue-500 font-mono">${videoCpm.toFixed(2)}</span>
                    </div>
                    <input
                      type="range" min="0.50" max="15.00" step="0.10" value={videoCpm}
                      aria-label="CPM Vidéo (pour 1000 vues)"
                      onChange={(e) => setVideoCpm(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-gray-200 dark:bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                    />
                  </div>

                  {/* Slider 2: Banner CPM */}
                  <div>
                    <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">
                      <span>CPM Bannière (pour 1000 vues)</span>
                      <span className="text-blue-500 font-mono">${bannerCpm.toFixed(2)}</span>
                    </div>
                    <input
                      type="range" min="0.10" max="5.00" step="0.10" value={bannerCpm}
                      aria-label="CPM Bannière (pour 1000 vues)"
                      onChange={(e) => setBannerCpm(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-gray-200 dark:bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                    />
                  </div>

                  {/* Slider 3: CPC */}
                  <div>
                    <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">
                      <span>CPC (Revenu par clic pub)</span>
                      <span className="text-blue-500 font-mono">${cpc.toFixed(2)}</span>
                    </div>
                    <input
                      type="range" min="0.05" max="2.00" step="0.05" value={cpc}
                      aria-label="CPC (Revenu par clic pub)"
                      onChange={(e) => setCpc(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-gray-200 dark:bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                    />
                  </div>

                  {/* Slider 4: Donation Value */}
                  <div>
                    <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">
                      <span>Valeur Don Unique (Sponsor Or)</span>
                      <span className="text-blue-500 font-mono">${donationVal.toFixed(2)}</span>
                    </div>
                    <input
                      type="range" min="1.00" max="30.00" step="0.50" value={donationVal}
                      aria-label="Valeur Don Unique (Sponsor Or)"
                      onChange={(e) => setDonationVal(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-gray-200 dark:bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                    />
                  </div>
                </div>
              </Card>
            </div>

            {/* Break-even & Recommendations */}
            <div className="space-y-6">
              <Card padding="lg" className="bg-[#0b0c15] text-white border border-blue-500/20">
                <h3 className="text-md font-black italic uppercase text-yellow-500 mb-4 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4" /> SEUIL DE RENTABILITÉ
                </h3>

                {isDeficit ? (
                  <div className="space-y-4">
                    <p className="text-xs text-gray-300 leading-relaxed font-mono">
                      Pour compenser le déficit simulé de <span className="text-red-500 font-bold">${deficitVal.toFixed(2)}</span> avec les taux sélectionnés, le site doit générer au choix :
                    </p>
                    <div className="bg-black/40 p-4 rounded-xl border border-white/5 space-y-3 font-mono">
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-400">Vues Vidéo Recom. :</span>
                        <span className="text-yellow-400 font-bold">{neededVideoImpressions.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-400">OU Clics Pubs :</span>
                        <span className="text-yellow-400 font-bold">{neededClicks.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-green-500/10 border border-green-500/30 p-4 rounded-xl text-green-400 text-xs leading-relaxed font-mono font-bold">
                    Félicitations ! Les paramètres actuels permettent de dégager un bénéfice de <span className="font-bold">${deficitVal.toFixed(2)}</span>. Aucun trafic publicitaire supplémentaire n'est nécessaire pour combler les coûts.
                  </div>
                )}
              </Card>

              <Card padding="lg" className="bg-white dark:bg-[#0f0f1a]">
                <h3 className="text-md font-black italic uppercase text-blue-500 mb-4 flex items-center gap-1.5">
                  <HelpCircle className="w-4 h-4" /> RECOMMANDATION GLOBALE
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed font-mono bg-gray-50 dark:bg-black/30 p-4 rounded-xl border border-gray-100 dark:border-white/5">
                  {data.recommendation}
                </p>
              </Card>
            </div>
          </div>

          {/* Engine Breakdown */}
          <Card padding="lg" className="bg-white dark:bg-[#0f0f1a]">
            <h3 className="text-lg font-black italic uppercase text-black dark:text-white mb-6">
              RÉPARTITION DES COÛTS PAR MOTEUR D'IA
            </h3>
            <div className="space-y-4">
              {Object.entries(data.cost_by_engine).length === 0 ? (
                <p className="text-xs text-gray-500 font-mono">Aucun coût d'IA enregistré.</p>
              ) : (
                Object.entries(data.cost_by_engine).map(([engine, cost]) => {
                  const percentage = data.total_ai_cost > 0 ? (cost / data.total_ai_cost) * 100 : 0;
                  return (
                    <div key={engine} className="space-y-1 font-mono">
                      <div className="flex justify-between text-xs">
                        <span className="text-black dark:text-white font-bold uppercase">{engine}</span>
                        <span className="text-gray-500">${cost.toFixed(2)} ({percentage.toFixed(1)}%)</span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-800 h-2 rounded-full overflow-hidden">
                        <div className="bg-blue-500 h-full" style={{ width: `${percentage}%` }} />
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </Card>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default FinancialDashboardPage;
