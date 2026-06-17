import React, { useState, useEffect } from 'react';
import { getAIFeedbackHistory } from '../../api';
import { Card } from "../../components/ui/Card";
import { MessageSquare, ThumbsUp, ThumbsDown, Calendar, ChevronLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import {AIFeedback} from "../../types";

const AIFeedbackHistoryPage: React.FC = () => {
  const [feedbacks, setFeedbacks] = useState<AIFeedback[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await getAIFeedbackHistory();
        setFeedbacks(data);
      } catch (err) {
        console.error("Erreur lors de la récupération de l'historique :", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchHistory().then();
  }, []);

  if (isLoading) {
    return (
      <div className="p-20 text-center text-white font-black animate-pulse uppercase tracking-[0.3em]">
        Accès à l'archive neuronale...
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-16 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between mb-12">
        <div>
          <Link to="/settings" className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-gray-500 hover:text-brand-primary mb-4 no-underline transition-colors">
            <ChevronLeft className="w-4 h-4" /> Paramètres
          </Link>
          <h1 className="text-4xl font-black italic manga-font tracking-tighter uppercase flex items-center gap-3">
            <MessageSquare className="w-8 h-8 text-purple-500" /> HISTORIQUE DES FEEDBACKS IA
          </h1>
          <p className="text-xs text-gray-400 font-bold uppercase tracking-wider mt-2">
            Consultez vos interactions et aidez-nous à raffiner l'intelligence du système.
          </p>
        </div>
        <div className="text-right hidden md:block">
          <div className="text-3xl font-black text-brand-primary leading-none">{feedbacks.length}</div>
          <div className="text-[10px] font-black uppercase opacity-40">Retours Totaux</div>
        </div>
      </div>

      {feedbacks.length === 0 ? (
        <Card padding="lg" className="text-center py-20">
          <MessageSquare className="w-12 h-12 text-gray-200 dark:text-navy-800 mx-auto mb-4" />
          <p className="font-bold text-gray-500 italic">Vous n'avez pas encore soumis de feedback à l'IA.</p>
          <p className="text-xs text-gray-400 mt-2 uppercase tracking-widest">Utilisez les boutons de vote lors de vos prochaines interactions !</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {feedbacks.map((fb) => (
            <Card key={fb.id} padding="md" className={`border-l-4 ${fb.is_positive ? 'border-l-green-500' : 'border-l-red-500'}`}>
              <div className="flex flex-col md:flex-row gap-6">
                {/* Status Column */}
                <div className="flex items-start gap-3 shrink-0">
                  <div className={`p-3 rounded-xl ${fb.is_positive ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                    {fb.is_positive ? <ThumbsUp className="w-5 h-5" /> : <ThumbsDown className="w-5 h-5" />}
                  </div>
                  <div className="md:hidden flex-1">
                    <span className="text-[10px] font-black uppercase opacity-40 block">{new Date(fb.created_at).toLocaleDateString()}</span>
                    <span className="text-xs font-black uppercase tracking-widest">{fb.feedback_type}</span>
                  </div>
                </div>

                {/* Content Column */}
                <div className="flex-1 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <span className="text-[9px] font-black uppercase opacity-40 tracking-widest block">Votre Requête / Contexte</span>
                      <div className="bg-gray-50 dark:bg-navy-950 p-3 rounded-lg text-xs font-bold italic line-clamp-3">
                        {fb.input_context || 'N/A'}
                      </div>
                    </div>
                    <div className="space-y-1">
                      <span className="text-[9px] font-black uppercase opacity-40 tracking-widest block">Réponse de l'IA</span>
                      <div className="bg-gray-50 dark:bg-navy-950 p-3 rounded-lg text-xs font-bold opacity-80 line-clamp-3">
                        {fb.output_text || 'N/A'}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Date Column (Desktop) */}
                <div className="hidden md:flex flex-col items-end justify-between shrink-0 text-right">
                  <span className="text-[10px] font-black uppercase tracking-widest text-brand-primary">{fb.feedback_type}</span>
                  <div className="text-[10px] font-bold text-gray-400 flex items-center gap-1.5">
                    <Calendar className="w-3 h-3" />
                    {new Date(fb.created_at).toLocaleDateString('fr-FR', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric'
                    })}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default AIFeedbackHistoryPage;


