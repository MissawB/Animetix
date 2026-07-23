import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ShieldCheck,
  Search,
  CheckCircle2,
  Database,
  Network,
  HelpCircle,
  Loader2,
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LabPage,
  LabHeader,
  LabPanel,
  LabEmpty,
  LabGuide,
  LAB_INPUT,
  LAB_LABEL,
  LAB_CTA,
  LAB_BTN_GHOST,
} from './components/shared/LabKit';

interface CoveVerification {
  query: string;
  context_found: boolean;
  result: string;
  entities: string[];
}

interface CoveTrace {
  baseline: string;
  verification_plan: string[];
  verifications: CoveVerification[];
  final_response: string;
}

const CoveOraclePage: React.FC = () => {
  const { t } = useTranslation();
  const [question, setQuestion] = useState('');
  const [mediaType, setMediaType] = useState('anime');
  const [trace, setTrace] = useState<CoveTrace | null>(null);

  const mutation = useMutation<CoveTrace, Error, { question: string; media_type: string }>({
    mutationFn: (data: { question: string; media_type: string }) =>
      apiClient('/api/v1/cognition/cove-oracle/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: (data) => {
      setTrace(data);
    },
  });

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim()) {
      mutation.mutate({ question, media_type: mediaType });
    }
  };

  return (
    <LabPage>
      <LabHeader
        code="Protocole · CoVe"
        title="Oracle de"
        accent="vérification"
        lede="Pose une question de lore : l'oracle rédige un brouillon, se contre-interroge, confronte chaque fait au graphe de connaissances Neo4j puis réécrit une réponse corrigée."
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Requête */}
        <div className="space-y-8 lg:col-span-4">
          <LabPanel title={t('labs.cove_oracle.query_analysis')}>
            <form onSubmit={onSubmit} className="space-y-6">
              <div className="space-y-2">
                <label htmlFor="lore-question" className={LAB_LABEL}>
                  {t('labs.cove_oracle.lore_question')}
                </label>
                <textarea
                  id="lore-question"
                  aria-label={t('labs.cove_oracle.lore_question')}
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  rows={4}
                  placeholder={t('labs.cove_oracle.question_placeholder')}
                  className={`${LAB_INPUT} resize-none`}
                />
              </div>

              <div className="flex gap-3">
                {['anime', 'manga', 'game'].map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setMediaType(type)}
                    className={`flex-1 cursor-pointer rounded-xl border py-3 text-[10px] font-black uppercase tracking-widest transition-colors ${
                      mediaType === type
                        ? 'border-[#E8442B] bg-[#E8442B] text-[#F4F1E8]'
                        : 'border-[#F4F1E8]/15 bg-transparent text-[#8F94A5] hover:border-[#FDB913] hover:text-[#F4F1E8]'
                    }`}
                  >
                    {type}
                  </button>
                ))}
              </div>

              <button
                type="submit"
                disabled={mutation.isPending || !question.trim()}
                className={LAB_CTA}
              >
                {mutation.isPending ? (
                  <Loader2 className="h-6 w-6 animate-spin" aria-hidden="true" />
                ) : (
                  t('labs.cove_oracle.verify_facts')
                )}
              </button>
            </form>
          </LabPanel>

          {/* Pipeline */}
          <LabPanel
            title={t('labs.cove_oracle.verification_pipeline')}
            corner={t('labs.cove_oracle.active')}
          >
            <ul className="space-y-4">
              {[
                t('labs.cove_oracle.multi_claims_decomposition'),
                t('labs.cove_oracle.neo4j_cross_reference'),
                t('labs.cove_oracle.revised_consensus'),
              ].map((stage) => (
                <li key={stage} className="flex items-center gap-3">
                  <CheckCircle2 className="h-4 w-4 flex-none text-[#FDB913]" aria-hidden="true" />
                  <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                    {stage}
                  </span>
                </li>
              ))}
            </ul>
          </LabPanel>
        </div>

        {/* Trace de vérification */}
        <div className="lg:col-span-8">
          <AnimatePresence mode="wait">
            {!trace && !mutation.isPending && (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-full"
              >
                <LabEmpty
                  icon={<HelpCircle className="h-20 w-20" aria-hidden="true" />}
                  title={t('labs.cove_oracle.awaiting_question')}
                  hint={t('labs.cove_oracle.submit_query_prompt')}
                />
              </motion.div>
            )}

            {mutation.isPending && (
              <motion.div
                key="pending"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex min-h-[320px] flex-col items-center justify-center rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] py-20"
              >
                <Loader2 className="h-12 w-12 animate-spin text-[#FDB913]" aria-hidden="true" />
                <p className="mt-6 text-[10px] font-black uppercase tracking-[0.3em] text-[#FDB913]">
                  {t('labs.cove_oracle.processing_cove')}
                </p>
              </motion.div>
            )}

            {trace && (
              <motion.div
                key="trace"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -16 }}
                className="space-y-8"
              >
                {/* 01 — Baseline */}
                <LabPanel
                  title={t('labs.cove_oracle.baseline_response')}
                  corner={t('labs.cove_oracle.potentially_unstable')}
                >
                  <p className="border-l-2 border-[#F4F1E8]/15 pl-5 text-sm italic leading-relaxed text-[#8F94A5]">
                    {trace.baseline}
                  </p>
                </LabPanel>

                {/* 02 — Plan de vérification */}
                <LabPanel
                  title={t('labs.cove_oracle.verification_plan')}
                  corner={t('labs.cove_oracle.decomposition')}
                >
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    {trace.verification_plan.map((q: string, i: number) => (
                      <div
                        key={i}
                        className="flex items-start gap-3 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4"
                      >
                        <Search
                          className="mt-0.5 h-4 w-4 flex-none text-[#FDB913]"
                          aria-hidden="true"
                        />
                        <p className="text-xs font-bold leading-relaxed text-[#F4F1E8]/80">{q}</p>
                      </div>
                    ))}
                  </div>
                </LabPanel>

                {/* 03 — Validation graphe */}
                <LabPanel
                  title={t('labs.cove_oracle.graph_validation')}
                  corner={t('labs.cove_oracle.neo4j_cross_ref')}
                >
                  <div className="space-y-4">
                    {trace.verifications.map((v: CoveVerification, i: number) => (
                      <div
                        key={i}
                        className="overflow-hidden rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10]"
                      >
                        <div className="flex items-center justify-between gap-4 border-b border-[#F4F1E8]/10 p-4">
                          <div className="flex items-center gap-3">
                            <Network
                              className="h-4 w-4 flex-none text-[#FDB913]"
                              aria-hidden="true"
                            />
                            <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                              {v.query}
                            </span>
                          </div>
                          {v.context_found && (
                            <span className="flex-none text-[9px] font-black uppercase tracking-widest text-[#FDB913]">
                              {t('labs.cove_oracle.context_found')}
                            </span>
                          )}
                        </div>
                        <div className="flex items-start gap-4 p-5 text-sm leading-relaxed text-[#F4F1E8]/80">
                          <Database
                            className="h-5 w-5 flex-none text-[#8F94A5]"
                            aria-hidden="true"
                          />
                          <p>{v.result}</p>
                        </div>
                        {v.entities.length > 0 && (
                          <div className="flex flex-wrap gap-2 border-t border-[#F4F1E8]/10 px-5 py-3">
                            {v.entities.map((e: string, j: number) => (
                              <span
                                key={j}
                                className="rounded-full border border-[#FDB913]/30 px-2.5 py-0.5 text-[9px] font-black uppercase tracking-widest text-[#FDB913]"
                              >
                                @{e}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </LabPanel>

                {/* 04 — Réponse finale */}
                <LabPanel
                  title={t('labs.cove_oracle.consolidated_response')}
                  corner={
                    <span className="flex items-center gap-1.5">
                      <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />{' '}
                      {t('labs.cove_oracle.final_verified_response')}
                    </span>
                  }
                  className="border-[#FDB913]/30"
                >
                  <p className="text-lg font-bold leading-relaxed text-[#F4F1E8]">
                    {trace.final_response}
                  </p>
                </LabPanel>

                <div className="pt-4 text-center">
                  <button
                    type="button"
                    onClick={() => {
                      setTrace(null);
                      setQuestion('');
                    }}
                    className={LAB_BTN_GHOST}
                  >
                    {t('labs.cove_oracle.new_analysis')}
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      <LabGuide
        steps={[
          {
            title: 'Pose ta question',
            body: t(
              'labs.cove_oracle.guide_question_desc',
              "Posez une question de lore (anime, manga, jeu). L'Oracle ne se contente pas d'une réponse instinctive : il la vérifie avant de vous la livrer.",
            ),
          },
          {
            title: "L'auto-contrôle",
            body: t(
              'labs.cove_oracle.guide_control_desc',
              'L\'IA rédige d\'abord un brouillon (la "baseline"), puis se pose elle-même des sous-questions pour contrôler chaque fait avancé.',
            ),
          },
          {
            title: 'Le verdict',
            body: t(
              'labs.cove_oracle.guide_verdict_desc',
              'Chaque fait est confronté à la base de connaissances du site, et la réponse finale est réécrite en corrigeant les erreurs détectées.',
            ),
          },
        ]}
        note={`${t('labs.cove_oracle.guide_footer_1', 'Pipeline Chain-of-Verification (CoVe) : la réponse baseline est décomposée en questions de vérification, chacune croisée avec le graphe de connaissances Neo4j (entités et relations).')} ${t('labs.cove_oracle.guide_footer_2', 'La réponse finale est régénérée à partir des faits confirmés, ce qui réduit les hallucinations du modèle.')}`}
      />
    </LabPage>
  );
};

export default CoveOraclePage;
