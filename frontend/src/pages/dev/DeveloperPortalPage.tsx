import React, { useState } from 'react';
import { 
  Terminal, 
  Key, 
  Book, 
  Activity, 
  Copy, 
  RefreshCw, 
  ShieldAlert, 
  CheckCircle2, 
  ExternalLink,
  Cpu,
  Zap,
  Lock,
  Code2,
  ChevronRight,
  ArrowRight
} from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { useAuthStore } from "../../store/authStore";

const DeveloperPortalPage: React.FC = () => {
  const { user } = useAuthStore();
  const [showKey, setShowKey] = useState(false);
  const [copySuccess, setCopyKeySuccess] = useState(false);

  // Fetch API Key Metadata
  const { data: apiData, isLoading, refetch } = useQuery({
    queryKey: ['developer-api-key'],
    queryFn: () => apiClient('/api/v1/developer/api-key/'),
    enabled: !!user,
  });

  // Generate Key Mutation
  const generateMutation = useMutation({
    mutationFn: () => apiClient('/api/v1/developer/api-key/', { method: 'POST' }),
    onSuccess: (data) => {
        refetch();
        // Here we could handle displaying the one-time raw key
    }
  });

  // Mock Subscription Mutation (Test Mode)
  const subscribeMutation = useMutation({
    mutationFn: () => apiClient('/api/v1/developer/subscribe-mock/', { method: 'POST' }),
    onSuccess: () => refetch()
  });

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopyKeySuccess(true);
    setTimeout(() => setCopyKeySuccess(false), 2000);
  };

  if (isLoading) return <div className="min-h-screen bg-[#05050a] flex items-center justify-center text-blue-500 font-black animate-pulse">ACCÈS AU TERMINAL DÉVELOPPEUR...</div>;

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#05050a] text-white">
        {/* Technical Header */}
        <section className="relative py-24 border-b border-white/5 overflow-hidden">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-blue-900/10 via-transparent to-transparent" />
            <div className="max-w-7xl mx-auto px-6 relative z-10 flex flex-col md:flex-row md:items-end justify-between gap-8">
                <div className="text-left">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[9px] font-black uppercase tracking-widest mb-6">
                        <Terminal className="w-3 h-3" /> Animetix Developer Portal v1.2
                    </div>
                    <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase leading-none mb-4">
                        BUILD THE <span className="text-blue-500">FUTURE</span>
                    </h1>
                    <p className="text-gray-500 font-bold uppercase tracking-widest text-xs italic">
                        Intégrez l'intelligence du Nexus dans vos propres applications via notre API REST robuste.
                    </p>
                </div>
                
                <div className="flex gap-4">
                    <Badge variant="neutral" className="bg-white/5 border-white/10 px-4 py-2 uppercase text-[10px] font-black italic">
                        User Tier: <span className={apiData?.tier === 'pro' ? 'text-blue-400' : 'text-gray-400'}>{apiData?.tier?.toUpperCase()}</span>
                    </Badge>
                    <Badge variant="neutral" className="bg-white/5 border-white/10 px-4 py-2 uppercase text-[10px] font-black italic">
                        Status: <span className="text-emerald-500">ONLINE</span>
                    </Badge>
                </div>
            </div>
        </section>

        <main className="max-w-7xl mx-auto px-6 py-20">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-16">
                {/* Left: Key Management & Usage */}
                <div className="lg:col-span-8 space-y-16">
                    {/* API Key Management */}
                    <section>
                        <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-[0.2em] flex items-center gap-2">
                            <Key className="w-4 h-4 text-blue-500" /> Authentification API
                        </h3>
                        
                        <Card className="bg-navy-900/20 border-white/5 p-10 overflow-hidden relative group">
                            <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
                                <Lock className="w-32 h-32 text-blue-500" />
                            </div>

                            {apiData?.tier !== 'pro' ? (
                                <div className="text-center py-10 space-y-8">
                                    <ShieldAlert className="w-16 h-16 text-yellow-500 mx-auto opacity-40" />
                                    <div>
                                        <h4 className="text-2xl font-black italic uppercase mb-2">Accès Restreint</h4>
                                        <p className="text-sm text-gray-500 font-bold uppercase tracking-widest leading-relaxed">
                                            La génération de clés API est réservée aux développeurs du tier <span className="text-blue-400">PRO</span>.
                                        </p>
                                    </div>
                                    <Button 
                                        onClick={() => subscribeMutation.mutate()}
                                        disabled={subscribeMutation.isPending}
                                        variant="primary" 
                                        className="bg-blue-600 border-none px-10 py-6 rounded-2xl shadow-xl"
                                    >
                                        ACTIVER L'ACCÈS DÉVELOPPEUR PRO
                                    </Button>
                                </div>
                            ) : (
                                <div className="space-y-10">
                                    <div>
                                        <p className="text-[10px] font-black opacity-30 uppercase mb-4 tracking-widest">Clé API Active</p>
                                        <div className="flex items-center gap-4 bg-black/40 border border-white/10 p-5 rounded-2xl font-mono text-sm group/key">
                                            <span className="flex-grow opacity-60">
                                                {apiData.has_api_key ? 'ax_pro_********************************' : 'AUCUNE CLÉ GÉNÉRÉE'}
                                            </span>
                                            {apiData.has_api_key && (
                                                <button 
                                                    onClick={() => handleCopy('ax_pro_...') }
                                                    className="p-2 hover:bg-white/5 rounded-lg transition-colors text-blue-400"
                                                >
                                                    {copySuccess ? <CheckCircle2 className="w-5 h-5 text-emerald-500" /> : <Copy className="w-5 h-5" />}
                                                </button>
                                            )}
                                        </div>
                                    </div>

                                    <div className="flex flex-col sm:flex-row gap-4 pt-6 border-t border-white/5">
                                        <Button 
                                            onClick={() => generateMutation.mutate()}
                                            disabled={generateMutation.isPending}
                                            variant="primary" 
                                            className="bg-blue-600 border-none flex-grow"
                                        >
                                            <RefreshCw className={`w-4 h-4 mr-2 ${generateMutation.isPending ? 'animate-spin' : ''}`} /> 
                                            {apiData.has_api_key ? 'RÉGÉNÉRER LA CLÉ' : 'GÉNÉRER MA PREMIÈRE CLÉ'}
                                        </Button>
                                        <Button variant="outline" className="border-red-500/20 text-red-500 hover:bg-red-500/10">
                                            RÉVOQUER TOUT L'ACCÈS
                                        </Button>
                                    </div>
                                    
                                    <div className="flex items-start gap-4 p-5 rounded-2xl bg-yellow-500/5 border border-yellow-500/10">
                                        <ShieldAlert className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                                        <p className="text-[10px] text-yellow-500/60 font-bold uppercase leading-relaxed">
                                            Attention: Votre clé API permet un accès direct à vos Berrix (Bx). Ne la partagez jamais et ne l'exposez pas dans du code frontend public.
                                        </p>
                                    </div>
                                </div>
                            )}
                        </Card>
                    </section>

                    {/* Quick Documentation (Snippet) */}
                    <section>
                        <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-[0.2em] flex items-center gap-2">
                            <Book className="w-4 h-4 text-purple-500" /> Documentation Rapide
                        </h3>
                        
                        <div className="space-y-6">
                            <div className="p-8 rounded-3xl bg-navy-900/20 border border-white/5 space-y-6">
                                <div className="flex items-center justify-between">
                                    <h4 className="text-lg font-black italic uppercase flex items-center gap-2">
                                        <Badge className="bg-emerald-500 text-white border-none">POST</Badge>
                                        /api/v1/developer/rag/
                                    </h4>
                                    <Badge variant="neutral" className="bg-white/5 border-white/10 opacity-40">100 Bx / request</Badge>
                                </div>
                                <p className="text-xs text-gray-500 font-bold uppercase tracking-wide italic">
                                    Interrogez le moteur Agentic RAG d'Animetix pour obtenir des réponses expertes basées sur le Lore actuel.
                                </p>
                                 <div className="bg-black/60 rounded-2xl p-6 font-mono text-[11px] text-gray-300 leading-relaxed border border-white/5 my-4">
                                    <p className="text-blue-400 mb-2">// Requête cURL</p>
                                    curl -X POST https://animetix.com/api/v1/developer/rag/ \<br />
                                    &nbsp;&nbsp;-H "X-API-Key: YOUR_API_KEY" \<br />
                                    &nbsp;&nbsp;-H "Content-Type: application/json" \<br />
                                    &nbsp;&nbsp;-d '&#123;"query": "Explique moi le passé de Guts dans Berserk", "media_type": "Manga"&#125;'
                                </div>
                                 <Button variant="outline" fullWidth className="border-white/5 bg-white/5 text-[10px] font-black uppercase tracking-widest hover:bg-white/10">
                                    <ExternalLink className="w-3 h-3 mr-2" /> Documentation Complète (OpenAPI)
                                </Button>
                            </div>
                        </div>
                    </section>
                </div>

                {/* Right Sidebar: Stats & Health */}
                <div className="lg:col-span-4 space-y-12">
                    {/* Monitoring */}
                    <section>
                        <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-[0.2em] flex items-center gap-2">
                            <Activity className="w-4 h-4 text-emerald-500" /> System Health
                        </h3>
                        <Card className="bg-navy-900/20 border-white/5 p-8 space-y-8">
                            <HealthMetric label="API Latency" value="124ms" status="optimal" />
                            <HealthMetric label="Inference Availability" value="99.9%" status="optimal" />
                            <HealthMetric label="Model Load" value="12%" status="healthy" />
                            
                            <div className="pt-6 border-t border-white/5">
                                 <div className="flex flex-col gap-2">
                                     <span className="text-[10px] font-black opacity-30 uppercase tracking-widest">Consumption (24h)</span>
                                     <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                                         <div className="h-full bg-blue-500 w-1/3 shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
                                     </div>
                                     <div className="flex justify-between text-[9px] font-black italic text-blue-400 uppercase mt-1">
                                         <span>1.2K Tokens used</span>
                                         <span>5K Limit</span>
                                     </div>
                                 </div>
                            </div>
                        </Card>
                    </section>

                    {/* SDKs & Tools */}
                    <section>
                        <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-[0.2em] flex items-center gap-2">
                            <Code2 className="w-4 h-4 text-yellow-500" /> SDKs & Resources
                        </h3>
                        <div className="space-y-4">
                            <SDKCard label="Python Client" icon={<Cpu className="w-5 h-5 text-blue-400" />} version="v0.9.2" />
                            <SDKCard label="Node.js SDK" icon={<Zap className="w-5 h-5 text-yellow-400" />} version="v1.0.1" />
                            <SDKCard label="React Hooks" icon={<Code2 className="w-5 h-5 text-purple-400" />} version="v2.4.0" />
                        </div>
                    </section>
                </div>
            </div>

            {/* Support CTA */}
            <section className="mt-40 p-16 rounded-[4rem] border border-white/5 bg-gradient-to-br from-navy-900/20 to-transparent flex flex-col md:flex-row items-center justify-between gap-12">
                <div className="text-left max-w-2xl">
                    <h2 className="text-4xl font-black italic manga-font uppercase mb-4 tracking-tighter">Besoin d'une limite étendue ?</h2>
                    <p className="text-gray-500 font-bold uppercase tracking-widest text-xs leading-relaxed italic">
                        Si votre projet nécessite des quotas d'inférence massifs ou des modèles fine-tunés sur-mesure, contactez notre équipe pour un accès Enterprise.
                    </p>
                </div>
                <Button variant="outline" className="px-12 py-6 rounded-2xl border-white/20 text-white font-black italic uppercase hover:bg-blue-600 hover:border-blue-600 transition-all">
                    CONTACTER LE SUPPORT TECH <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
            </section>
        </main>
      </div>
    </AnimatedPage>
  );
};

const HealthMetric = ({ label, value, status }: { label: string, value: string, status: 'optimal' | 'healthy' | 'warning' }) => (
    <div className="flex items-center justify-between">
        <div>
            <p className="text-[10px] font-black opacity-30 uppercase mb-1 tracking-widest">{label}</p>
            <p className="text-xl font-black italic manga-font">{value}</p>
        </div>
        <div className={`w-2 h-2 rounded-full ${status === 'optimal' ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]' : 'bg-blue-500'}`} />
    </div>
);

const SDKCard = ({ label, icon, version }: { label: string, icon: React.ReactNode, version: string }) => (
    <div className="p-5 rounded-2xl bg-white/5 border border-white/5 flex items-center justify-between group hover:bg-white/10 transition-all cursor-pointer">
        <div className="flex items-center gap-4">
            <div className="p-3 bg-black/40 rounded-xl">{icon}</div>
            <div>
                <h4 className="text-xs font-black uppercase tracking-widest">{label}</h4>
                <p className="text-[9px] opacity-30 font-bold uppercase">{version}</p>
            </div>
        </div>
        <ChevronRight className="w-4 h-4 opacity-0 group-hover:opacity-100 translate-x-[-10px] group-hover:translate-x-0 transition-all" />
    </div>
);

export default DeveloperPortalPage;
