import React from 'react';
import { 
  Coins, 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  BarChart3, 
  RefreshCw, 
  Database, 
  ShieldCheck,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  Info,
  Scale
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion } from 'framer-motion';

interface EconomicData {
    currency_name: string;
    total_circulation: number;
    avg_balance: number;
    max_balance: number;
    flux_24h: {
        minted: number;
        burned: number;
        net: number;
    };
    repartition: Record<string, number>;
    inflation_index: number;
    status: string;
}

const EconomicAuditPage: React.FC = () => {
  const { data, isLoading } = useQuery<EconomicData>({
    queryKey: ['admin', 'economics'],
    queryFn: () => apiClient('/api/v1/admin/economics/')
  });

  return (
    <div className="min-h-screen w-full bg-[#fafafa] dark:bg-[#0a0a0f] text-black dark:text-white pt-20 pb-32">
      <AnimatedPage>
        <div className="max-w-7xl mx-auto px-6 relative z-10">
          
          {/* Header */}
          <header className="mb-20 relative">
              <div className="absolute -top-24 -left-24 w-96 h-96 bg-amber-500/10 blur-[120px] rounded-full -z-10" />
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-[10px] font-black uppercase tracking-widest text-amber-600 dark:text-amber-500 mb-6">
                  <Coins className="w-3 h-3" /> Macro-Economic Supervision Hub
              </div>
              <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4 leading-none">
                  BERRIX <span className="text-amber-500 text-glow">ECONOMY</span>
              </h1>
              <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                  Surveillance de la masse monétaire, de l'inflation et de la vélocité des jetons.
              </p>
          </header>

          {isLoading ? (
              <div className="py-32 text-center"><RefreshCw className="w-12 h-12 animate-spin mx-auto opacity-20 text-amber-500" /></div>
          ) : data ? (
              <div className="space-y-12">
                  
                  {/* Top Metrics Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                      <EconomicMetricCard 
                        label="Masse Monétaire" 
                        value={`${data.total_circulation.toLocaleString()} Bx`} 
                        icon={Database} 
                        color="text-amber-500"
                        desc="Total en circulation"
                      />
                      <EconomicMetricCard 
                        label="Solde Moyen" 
                        value={`${data.avg_balance.toLocaleString()} Bx`} 
                        icon={Scale} 
                        color="text-blue-500"
                        desc="Par profil actif"
                      />
                      <EconomicMetricCard 
                        label="Flux Net (24h)" 
                        value={`${data.flux_24h.net > 0 ? '+' : ''}${data.flux_24h.net.toLocaleString()} Bx`} 
                        icon={data.flux_24h.net >= 0 ? TrendingUp : TrendingDown} 
                        color={data.flux_24h.net >= 0 ? "text-emerald-500" : "text-red-500"}
                        desc="Mint vs Burn"
                      />
                      <EconomicMetricCard 
                        label="Inflation Index" 
                        value={data.inflation_index.toFixed(2)} 
                        icon={Activity} 
                        color={data.status === 'Stable' ? "text-emerald-500" : "text-amber-500"}
                        desc={`Status: ${data.status.toUpperCase()}`}
                      />
                  </div>

                  {/* Detailed Analysis Section */}
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                      
                      {/* Left: Sources & Sinks */}
                      <div className="lg:col-span-7 space-y-8">
                          <Card padding="lg" className="bg-white dark:bg-navy-950/40 border-none shadow-2xl rounded-[3rem] relative overflow-hidden group">
                              <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none group-hover:opacity-10 transition-opacity">
                                  <BarChart3 className="w-48 h-48 text-amber-500" />
                              </div>
                              
                              <h3 className="text-xs font-black uppercase tracking-widest flex items-center gap-2 opacity-40 mb-10">
                                  <TrendingUp className="w-4 h-4 text-amber-500" /> Répartition des Flux Historiques
                              </h3>

                              <div className="space-y-6 relative z-10">
                                  {Object.entries(data.repartition).map(([type, amount]) => (
                                      <div key={type} className="group/item">
                                          <div className="flex justify-between items-end mb-2">
                                              <span className="text-[10px] font-black uppercase tracking-widest opacity-40">{type.replace('_', ' ')}</span>
                                              <span className={`text-sm font-black italic manga-font ${amount >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                                  {amount >= 0 ? '+' : ''}{amount.toLocaleString()} Bx
                                              </span>
                                          </div>
                                          <div className="w-full h-2 bg-black/5 dark:bg-white/5 rounded-full overflow-hidden">
                                              <motion.div 
                                                initial={{ width: 0 }}
                                                animate={{ width: `${Math.min(100, (Math.abs(amount) / data.total_circulation) * 1000)}%` }}
                                                className={`h-full ${amount >= 0 ? 'bg-emerald-500' : 'bg-red-500'}`}
                                              />
                                          </div>
                                      </div>
                                  ))}
                              </div>
                          </Card>

                          {/* Economy Insights */}
                          <Card padding="lg" className="bg-amber-600 text-white border-none shadow-2xl rounded-[3rem] flex flex-col justify-between min-h-[250px]">
                              <div>
                                  <ShieldCheck className="w-12 h-12 mb-8 opacity-40" />
                                  <h3 className="text-3xl font-black italic manga-font uppercase mb-4 leading-tight">Berrix Policy Engine</h3>
                                  <p className="text-sm font-bold italic opacity-90 leading-relaxed uppercase">
                                      Le taux d'inflation actuel ({data.inflation_index}) indique un écosystème {data.status.toLowerCase()}. {data.inflation_index > 1.5 ? "Attention : Sur-émission de tokens détectée via le minage passif." : "L'équilibre entre la consommation IA et les revenus publicitaires est maintenu."}
                                  </p>
                              </div>
                              <div className="mt-8 flex justify-between items-center text-[10px] font-black uppercase tracking-widest opacity-60">
                                  <span>Protocol Standard v2.1</span>
                                  <span>Verified on-chain (Simulated)</span>
                              </div>
                          </Card>
                      </div>

                      {/* Right: Real-time Flux 24h */}
                      <div className="lg:col-span-5 space-y-8">
                          <Card padding="lg" className="bg-white dark:bg-navy-950 border-none shadow-2xl rounded-[3rem] h-full">
                              <h3 className="text-xs font-black uppercase tracking-widest flex items-center gap-2 opacity-40 mb-10">
                                  <Zap className="w-4 h-4 text-amber-500" /> Flux 24h (Live)
                              </h3>

                              <div className="space-y-12">
                                  <div className="flex items-center gap-8">
                                      <div className="w-16 h-16 rounded-3xl bg-emerald-500/10 flex items-center justify-center shrink-0">
                                          <ArrowUpRight className="w-8 h-8 text-emerald-500" />
                                      </div>
                                      <div>
                                          <p className="text-[10px] font-black uppercase opacity-30 tracking-widest mb-1">Berrix Minted</p>
                                          <p className="text-4xl font-black italic manga-font text-emerald-500">+{data.flux_24h.minted.toLocaleString()}</p>
                                      </div>
                                  </div>

                                  <div className="flex items-center gap-8">
                                      <div className="w-16 h-16 rounded-3xl bg-red-500/10 flex items-center justify-center shrink-0">
                                          <ArrowDownRight className="w-8 h-8 text-red-500" />
                                      </div>
                                      <div>
                                          <p className="text-[10px] font-black uppercase opacity-30 tracking-widest mb-1">Berrix Burned</p>
                                          <p className="text-4xl font-black italic manga-font text-red-500">-{data.flux_24h.burned.toLocaleString()}</p>
                                      </div>
                                  </div>

                                  <div className="pt-12 border-t border-black/5 dark:border-white/5">
                                      <div className="p-8 bg-gray-50 dark:bg-white/[0.03] rounded-[2.5rem] border border-black/5 dark:border-white/5">
                                          <div className="flex justify-between items-center mb-4">
                                              <span className="text-[10px] font-black uppercase tracking-widest opacity-30">Plafond de Richesse</span>
                                              <Badge variant="neutral" className="bg-amber-500/10 text-amber-600 dark:text-amber-500 border-none text-[8px] font-black italic">TOP_WHALE</Badge>
                                          </div>
                                          <p className="text-2xl font-black italic manga-font">{data.max_balance.toLocaleString()} Bx</p>
                                          <p className="text-[8px] font-bold opacity-30 uppercase mt-2">Plus gros portefeuille de l'écosystème</p>
                                      </div>
                                  </div>
                              </div>
                          </Card>
                      </div>

                  </div>

                  {/* Warning Footer */}
                  <div className="mt-20 p-12 bg-black text-white rounded-[4rem] border border-white/5 flex flex-col md:flex-row items-center gap-12 text-center md:text-left">
                      <div className="w-20 h-20 rounded-full bg-amber-500/10 flex items-center justify-center shrink-0">
                          <Info className="w-10 h-10 text-amber-500" />
                      </div>
                      <div className="flex-grow">
                          <h4 className="text-xl font-black italic manga-font uppercase mb-2">Note sur la Valeur Intrinsèque</h4>
                          <p className="text-[10px] font-bold opacity-40 uppercase leading-relaxed max-w-3xl">
                              Le Berrix (Bx) est un jeton utilitaire de plateforme sans valeur monétaire externe. Les flux macro-économiques sont ajustés via les algorithmes de la Power Station pour garantir l'accès gratuit aux services IA via le visionnage publicitaire.
                          </p>
                      </div>
                      <Button variant="outline" className="border-white/10 text-[10px] font-black uppercase tracking-widest whitespace-nowrap px-8 py-4 hover:bg-white/5 transition-all">
                          Ajuster Monetary Policy
                      </Button>
                  </div>
              </div>
          ) : (
              <div className="py-32 text-center opacity-20">Erreur de chargement des données.</div>
          )}

        </div>
      </AnimatedPage>
    </div>
  );
};

interface EconomicMetricCardProps {
    label: string;
    value: string;
    icon: React.ElementType;
    color: string;
    desc: string;
}

const EconomicMetricCard: React.FC<EconomicMetricCardProps> = ({ label, value, icon: Icon, color, desc }) => (
    <Card padding="lg" className="bg-white dark:bg-navy-950 border-none shadow-xl rounded-[2.5rem] relative overflow-hidden group hover:scale-105 transition-all duration-300">
        <div className={`absolute -right-2 -bottom-2 opacity-5 ${color}`}>
            <Icon size={64} />
        </div>
        <p className="text-[8px] font-black uppercase opacity-30 tracking-[0.2em] mb-2">{label}</p>
        <p className={`text-3xl font-black italic manga-font mb-4 ${color}`}>{value}</p>
        <div className="flex items-center gap-2">
            <div className={`w-1 h-1 rounded-full bg-current ${color}`} />
            <span className="text-[9px] font-bold opacity-40 uppercase tracking-wider">{desc}</span>
        </div>
    </Card>
);

export default EconomicAuditPage;
