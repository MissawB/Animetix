import React, { useState } from 'react';
import { ShieldAlert, Edit3, Save, X, Info, Check } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { useDPO } from '../../features/admin/hooks/useDPO';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import { Badge } from '../../../components/ui/Badge';
import { CardSkeleton } from '../../../components/ui/Skeleton';

import { useTranslation } from 'react-i18next';

const AdminDPOPage: React.FC = () => {
  const { t } = useTranslation();
  const { feedbacks, isLoading, curate, isSubmitting } = useDPO();
  const [editingId, setEditingId] = useState<number | null>(null);
  
  const { register, handleSubmit, reset } = useForm<{ chosen_text: string }>();

  const onSubmit = async (data: { chosen_text: string }, feedbackId: number) => {
    await curate({ feedback_id: feedbackId, chosen_text: data.chosen_text });
    setEditingId(null);
    reset();
  };

  if (isLoading) return (
    <div className="max-w-6xl mx-auto px-6 py-16">
        <CardSkeleton />
    </div>
  );

  return (
    
        <div className="max-w-6xl mx-auto px-6 py-16">
            <div className="flex items-center justify-between mb-12">
                <div>
                    <h1 className="text-5xl font-black italic manga-font tracking-tighter uppercase mb-2">
                        DPO <span className="text-red-500">CURATION</span>
                    </h1>
                    <p className="text-xs font-black opacity-40 uppercase tracking-[0.3em]">Alignement du Modèle par Correction Humaine</p>
                </div>
                <Badge variant="danger" className="p-4 px-6 text-sm">
                    <ShieldAlert className="w-5 h-5 mr-2" /> {feedbacks.length} Erreurs à traiter
                </Badge>
            </div>

            <div className="space-y-8">
                {feedbacks.map((fb: any) => (
                    <Card key={fb.id} padding="lg" className="relative overflow-hidden group">
                        <div className="absolute top-0 left-0 w-1.5 h-full bg-red-500 opacity-20 group-hover:opacity-100 transition-opacity" />
                        
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
                            <div className="space-y-6">
                                <div>
                                    <h4 className="text-[10px] font-black uppercase opacity-30 mb-3 flex items-center gap-2">
                                        <Info className="w-3 h-3" /> Contexte Utilisateur
                                    </h4>
                                    <div className="bg-surface-text/5 p-5 rounded-2xl text-xs font-medium italic border border-surface-text/5">
                                        "{fb.context}"
                                    </div>
                                </div>
                                <div>
                                    <h4 className="text-[10px] font-black uppercase text-red-500/50 mb-3">Réponse Rejetée</h4>
                                    <div className="bg-red-500/5 p-5 rounded-2xl text-xs font-bold border border-red-500/10 text-red-600 dark:text-red-400">
                                        {fb.output}
                                    </div>
                                </div>
                            </div>

                            <div className="flex flex-col justify-center">
                                {editingId === fb.id ? (
                                    <form onSubmit={handleSubmit((d) => onSubmit(d, fb.id))} className="space-y-4">
                                        <h4 className="text-[10px] font-black uppercase text-green-500/50">Réponse Idéale (Chosen)</h4>
                                        <textarea 
                                            {...register('chosen_text', { required: true })}
                                            className="w-full p-6 rounded-2xl bg-green-500/5 border-2 border-green-500/20 focus:border-green-500 outline-none text-xs font-bold min-h-[150px]"
                                            placeholder="Tapez la réponse parfaite..."
                                        />
                                        <div className="flex gap-3">
                                            <Button type="submit" variant="success" size="sm" disabled={isSubmitting}>
                                                <Save className="w-4 h-4" /> Valider
                                            </Button>
                                            <Button variant="outline" size="sm" onClick={() => setEditingId(null)}>
                                                <X className="w-4 h-4" />
                                            </Button>
                                        </div>
                                    </form>
                                ) : (
                                    <div className="text-center py-8 space-y-6">
                                        <div className="w-16 h-16 bg-red-500/10 text-red-500 rounded-full flex items-center justify-center mx-auto shadow-inner">
                                            <ShieldAlert className="w-8 h-8" />
                                        </div>
                                        <Button variant="primary" onClick={() => setEditingId(fb.id)}>
                                            <Edit3 className="w-4 h-4" /> RÉPARER LE RAISONNEMENT
                                        </Button>
                                    </div>
                                )}
                            </div>
                        </div>
                    </Card>
                ))}

                {feedbacks.length === 0 && (
                    <div className="text-center py-24 opacity-20 uppercase font-black tracking-widest animate-pulse italic">
                        <Check className="w-20 h-20 mx-auto mb-4" />
                        Toutes les erreurs ont été corrigées. <br />
                        Nexus de connaissance synchronisé.
                    </div>
                )}
            </div>
        </div>
    
  );
};

export default AdminDPOPage;

