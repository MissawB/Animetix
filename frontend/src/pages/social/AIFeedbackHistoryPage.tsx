import React, { useState, useEffect } from 'react';
import { labService } from '../../features/labs/services/labService';
import { MessageSquare, ThumbsUp, ThumbsDown, Calendar, ChevronLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { AIFeedback } from '../../types';
import { useTranslation } from 'react-i18next';

const AIFeedbackHistoryPage: React.FC = () => {
  const { t } = useTranslation();
  const [feedbacks, setFeedbacks] = useState<AIFeedback[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await labService.getAIFeedbackHistory();
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
      <div className="flex min-h-screen w-full items-center justify-center bg-[#0B0C10] px-6">
        <p className="animate-pulse text-center text-xs font-black uppercase tracking-[0.3em] text-[#8F94A5]">
          {t('social.feedback.loading', "Accès à l'archive neuronale...")}
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-[#0B0C10] pt-20 text-[#F4F1E8]">
      <div className="mx-auto max-w-5xl px-6 py-16">
        <header className="relative mb-12">
          <div
            className="explore-halftone pointer-events-none absolute -inset-x-6 -top-10 h-40"
            aria-hidden
          />
          <div className="relative flex items-center justify-between gap-6">
            <div>
              <Link
                to="/auth/settings/"
                className="mb-4 inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-[#8F94A5] no-underline transition-colors hover:text-[#F4F1E8]"
              >
                <ChevronLeft className="h-4 w-4" /> {t('social.feedback.settings', 'Paramètres')}
              </Link>
              <div className="flex items-center gap-3">
                <span className="explore-stamp -rotate-2" aria-hidden>
                  声
                </span>
                <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                  {t('social.feedback.eyebrow', 'Registre · Retours IA')}
                </span>
              </div>
              <h1 className="font-manga mt-4 flex items-center gap-3 text-4xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-5xl">
                <MessageSquare className="h-8 w-8 text-[#E8442B]" aria-hidden="true" />{' '}
                {t('social.feedback.title', 'HISTORIQUE DES FEEDBACKS IA')}
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-relaxed text-[#8F94A5]">
                {t(
                  'social.feedback.subtitle',
                  "Consultez vos interactions et aidez-nous à raffiner l'intelligence du système.",
                )}
              </p>
            </div>
            <div className="hidden text-right md:block">
              <div className="font-manga text-4xl font-black italic leading-none text-[#FDB913]">
                {feedbacks.length}
              </div>
              <div className="mt-1 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                {t('social.feedback.total_returns', 'Retours Totaux')}
              </div>
            </div>
          </div>
          <span className="relative mt-8 block h-px bg-[#F4F1E8]/10" aria-hidden />
        </header>

        {feedbacks.length === 0 ? (
          <div className="flex flex-col items-center rounded-2xl border border-dashed border-[#F4F1E8]/15 py-20 text-center">
            <MessageSquare className="mx-auto mb-4 h-12 w-12 text-[#8F94A5]/30" />
            <p className="font-bold italic text-[#8F94A5]">
              {t(
                'social.feedback.no_feedback',
                "Vous n'avez pas encore soumis de feedback à l'IA.",
              )}
            </p>
            <p className="mt-2 text-xs uppercase tracking-widest text-[#8F94A5]/70">
              {t(
                'social.feedback.vote_instruction',
                'Utilisez les boutons de vote lors de vos prochaines interactions !',
              )}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {feedbacks.map((fb) => (
              <div
                key={fb.id}
                className={`rounded-2xl border border-[#F4F1E8]/10 border-l-4 bg-[#0F1016] p-5 ${
                  fb.is_positive ? 'border-l-[#FDB913]' : 'border-l-[#E8442B]'
                }`}
              >
                <div className="flex flex-col gap-6 md:flex-row">
                  {/* Status Column */}
                  <div className="flex shrink-0 items-start gap-3">
                    <div
                      className={`rounded-xl p-3 ${
                        fb.is_positive
                          ? 'bg-[#FDB913]/10 text-[#FDB913]'
                          : 'bg-[#E8442B]/10 text-[#E8442B]'
                      }`}
                    >
                      {fb.is_positive ? (
                        <ThumbsUp className="h-5 w-5" />
                      ) : (
                        <ThumbsDown className="h-5 w-5" />
                      )}
                    </div>
                    <div className="flex-1 md:hidden">
                      <span className="block text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                        {new Date(fb.created_at).toLocaleDateString()}
                      </span>
                      <span className="text-xs font-black uppercase tracking-widest text-[#F4F1E8]">
                        {fb.feedback_type}
                      </span>
                    </div>
                  </div>

                  {/* Content Column */}
                  <div className="flex-1 space-y-4">
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <div className="space-y-1">
                        <span className="block text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                          {t('social.feedback.your_request', 'Votre Requête / Contexte')}
                        </span>
                        <div className="line-clamp-3 rounded-lg border border-[#F4F1E8]/10 bg-[#0B0C10] p-3 text-xs font-bold italic text-[#F4F1E8]/90">
                          {fb.input_context || 'N/A'}
                        </div>
                      </div>
                      <div className="space-y-1">
                        <span className="block text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                          {t('social.feedback.ia_response', "Réponse de l'IA")}
                        </span>
                        <div className="line-clamp-3 rounded-lg border border-[#F4F1E8]/10 bg-[#0B0C10] p-3 text-xs font-bold text-[#8F94A5]">
                          {fb.output_text || 'N/A'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Date Column (Desktop) */}
                  <div className="hidden shrink-0 flex-col items-end justify-between text-right md:flex">
                    <span className="text-[10px] font-black uppercase tracking-widest text-[#E8442B]">
                      {fb.feedback_type}
                    </span>
                    <div className="flex items-center gap-1.5 text-[10px] font-bold text-[#8F94A5]">
                      <Calendar className="h-3 w-3" />
                      {new Date(fb.created_at).toLocaleDateString('fr-FR', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                      })}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AIFeedbackHistoryPage;
