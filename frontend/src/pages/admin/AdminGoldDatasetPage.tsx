import React from 'react';
import { 
  Database, 
  CheckCircle2, 
  Trash2, 
  RefreshCw, 
  ShieldCheck, 
  ChevronRight,
  AlertCircle,
  Clock,
  Sparkles
} from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { goldDatasetService } from '../../features/admin/services/goldDatasetService';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Badge } from '../../../components/ui/Badge';
import { AnimatedPage } from '../../../components/ui/AnimatedPage';
import { CardSkeleton } from '../../../components/ui/Skeleton';
import { queryClient } from '../../../utils/queryClient';

const AdminGoldDatasetPage: React.FC = () => {
  const { data: entries, isLoading, refetch } = useQuery<any[]>({
    queryKey: ['gold-dataset'],
    queryFn: goldDatasetService.getList,
  });

  const validateMutation = useMutation({
    mutationFn: (id: number) => goldDatasetService.validateEntry(id),
    onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['gold-dataset'] });
    }
  });

  const syncMutation = useMutation({
    mutationFn: goldDatasetService.syncPositiveFeedback,
    onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['gold-dataset'] });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => goldDatasetService.deleteEntry(id),
    onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['gold-dataset'] });
    }
  });

  if (isLoading) return <div className="p-20 text-center"><CardSkeleton /></div>;

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-16">
        <header className="mb-16 flex flex-col md:flex-row justify-between items-end gap-8">
            <div>
                <h1 className="text-6xl font-black italic manga-font tracking-tighter uppercase mb-2">
                    GOLD <span className="text-amber-500 text-glow">DATASET</span>
                </h1>
                <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em]">
                    Curation des données haute fidélité pour le Fine-Tuning.
                </p>
            </div>
            
            <div className="flex gap-4">
                <Button 
                    onClick={() => syncMutation.mutate()}
                    disabled={syncMutation.isPending}
                    variant="outline" 
                    className="border-amber-500/20 bg-amber-500/5 text-amber-500 hover:bg-amber-500/10 px-8 rounded-2xl font-black italic uppercase"
                >
                    <RefreshCw className={`w-4 h-4 mr-2 ${syncMutation.isPending ? 'animate-spin' : ''}`} /> Sync Positive Feedback
                </Button>
            </div>
        </header>

        {!entries || entries.length === 0 ? (
            <div className="text-center py-32 opacity-20 border-4 border-dashed border-white/5 rounded-[4rem]">
                <Database className="w-24 h-24 mx-auto mb-6" />
                <p className="text-2xl font-black italic manga-font uppercase">Aucune donnée Gold en attente de curation</p>
            </div>
        ) : (
            <div className="space-y-8">
                {entries.map((entry) => (
                    <Card key={entry.id} padding="none" className={`overflow-hidden bg-navy-900/40 border-white/5 relative ${entry.is_validated ? 'border-emerald-500/20' : 'hover:border-amber-500/30'} transition-all duration-300`}>
                        <div className="p-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
                            {/* Metadata */}
                            <div className="lg:col-span-2 space-y-4">
                                <div className="flex items-center gap-2 text-[10px] font-black opacity-30 uppercase tracking-widest">
                                    <Clock className="w-3 h-3" /> {new Date(entry.created_at).toLocaleDateString()}
                                </div>
                                <Badge variant={entry.is_validated ? 'success' : 'neutral'} className="w-fit">
                                    {entry.is_validated ? 'VALIDÉ' : 'À CURER'}
                                </Badge>
                                <div className="pt-4 border-t border-white/5">
                                    <p className="text-[8px] font-black uppercase opacity-20 mb-1">Entry ID</p>
                                    <code className="text-[10px] text-amber-500/50">#G-{entry.id}</code>
                                </div>
                            </div>

                            {/* Content */}
                            <div className="lg:col-span-8 space-y-6">
                                <div>
                                    <h4 className="text-[10px] font-black uppercase text-blue-500 mb-2 tracking-widest flex items-center gap-2">
                                        <ChevronRight className="w-3 h-3" /> Context / Input
                                    </h4>
                                    <div className="p-4 bg-black/40 rounded-xl border border-white/5 text-xs font-medium opacity-80 leading-relaxed italic">
                                        {entry.context || entry.instruction}
                                    </div>
                                </div>
                                <div>
                                    <h4 className="text-[10px] font-black uppercase text-emerald-500 mb-2 tracking-widest flex items-center gap-2">
                                        <Sparkles className="w-3 h-3" /> Ideal Response
                                    </h4>
                                    <div className="p-6 bg-emerald-500/5 rounded-2xl border border-emerald-500/10 text-sm font-bold leading-relaxed text-blue-50">
                                        {entry.response}
                                    </div>
                                </div>
                            </div>

                            {/* Actions */}
                            <div className="lg:col-span-2 flex flex-col gap-4 justify-center">
                                {!entry.is_validated && (
                                    <Button 
                                        onClick={() => validateMutation.mutate(entry.id)}
                                        disabled={validateMutation.isPending}
                                        variant="primary" 
                                        fullWidth 
                                        className="bg-emerald-600 hover:bg-emerald-500 border-none rounded-xl py-6"
                                    >
                                        <ShieldCheck className="w-5 h-5" /> APPROUVER
                                    </Button>
                                )}
                                <Button 
                                    onClick={() => { if(confirm('Supprimer cette entrée ?')) deleteMutation.mutate(entry.id); }}
                                    disabled={deleteMutation.isPending}
                                    variant="outline" 
                                    fullWidth 
                                    className="border-red-500/20 text-red-500 hover:bg-red-500/10 rounded-xl py-4 text-[10px]"
                                >
                                    <Trash2 className="w-4 h-4" /> SUPPRIMER
                                </Button>
                            </div>
                        </div>
                    </Card>
                ))}
            </div>
        )}

        {/* Legend Box */}
        <div className="mt-24 p-12 rounded-[4rem] bg-amber-500/5 border border-amber-500/10 flex flex-col md:flex-row items-center gap-12">
            <div className="p-6 bg-amber-500 rounded-3xl shadow-[0_0_30px_rgba(245,158,11,0.3)]">
                <Database className="w-12 h-12 text-black" />
            </div>
            <div>
                <h4 className="text-3xl font-black italic manga-font uppercase mb-4 tracking-tighter">Nexus Gold Pipeline v1.0</h4>
                <p className="text-sm font-bold opacity-40 uppercase leading-relaxed max-w-3xl italic text-justify">
                    Les entrées validées ici sont injectées dans le pipeline de fine-tuning LoRA. L'IA apprend ainsi des interactions humaines parfaites, réduisant drastiquement les hallucinations sémantiques dans les prochains cycles d'inférence.
                </p>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default AdminGoldDatasetPage;

