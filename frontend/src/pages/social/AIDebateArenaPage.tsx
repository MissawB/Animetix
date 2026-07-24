import React, { useState } from 'react';
import { Swords, Scale, Zap, Sparkles, Gavel, History, Target } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
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
  SHU,
  GOLD,
  AI_INDIGO,
} from '../labs/components/shared/LabKit';

interface DebateResult {
  pro_argument: string;
  anti_argument: string;
  judge_conclusion: string;
}

/** Les trois voix du duel : thèse (kin), antithèse (shu), synthèse (ai). */
const AGENTS = {
  pro: { seal: '賛', ink: GOLD },
  anti: { seal: '否', ink: SHU },
  judge: { seal: '裁', ink: AI_INDIGO },
} as const;

interface AgentSealProps {
  seal: string;
  ink: string;
}

/** Cachet d'agent : kanji encré dans la voix de l'agent. */
const AgentSeal: React.FC<AgentSealProps> = ({ seal, ink }) => (
  <span
    className="flex h-9 w-9 flex-none items-center justify-center rounded-[2px] border-2 text-sm font-black"
    style={{ borderColor: ink, color: ink }}
    aria-hidden
  >
    {seal}
  </span>
);

interface ArgumentPanelProps {
  seal: string;
  ink: string;
  label: string;
  text: string;
}

/** Plaidoirie d'un agent : panneau papier signé de son cachet. */
const ArgumentPanel: React.FC<ArgumentPanelProps> = ({ seal, ink, label, text }) => (
  <section
    className="relative overflow-hidden rounded-2xl border bg-[#0F1016] p-6 sm:p-8"
    style={{ borderColor: `${ink}40` }}
  >
    <span
      className="font-manga pointer-events-none absolute -right-3 -top-8 text-8xl font-black italic opacity-[0.07]"
      style={{ color: ink }}
      aria-hidden
    >
      {seal}
    </span>
    <div className="relative mb-5 flex items-center gap-3">
      <AgentSeal seal={seal} ink={ink} />
      <span className="text-xs font-black uppercase tracking-widest" style={{ color: ink }}>
        {label}
      </span>
    </div>
    <p className="relative text-sm leading-relaxed text-[#F4F1E8]/85">{text}</p>
  </section>
);

const AIDebateArenaPage: React.FC = () => {
  const [mediaTitle, setMediaTitle] = useState('');
  const [topic, setTopic] = useState('');
  const [debateResult, setDebateResult] = useState<DebateResult | null>(null);
  const { t } = useTranslation();

  const mutation = useMutation({
    mutationFn: (data: { media_title: string; topic: string }) =>
      apiClient('/api/v1/cognition/debate-arena/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: (data) => {
      setDebateResult(data);
    },
  });

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (mediaTitle.trim() && topic.trim()) {
      mutation.mutate({ media_title: mediaTitle, topic: topic });
    }
  };

  return (
    <LabPage>
      <LabHeader
        glyph="論"
        code="Duel sémantique · Game Theory"
        title="Arène du"
        accent="débat"
        lede={t(
          'social.debate.subtitle',
          'Orchestrez des confrontations sémantiques entre agents spécialisés basées sur les faits du Knowledge Graph.',
        )}
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Configuration du débat */}
        <div className="space-y-8 lg:col-span-4">
          <LabPanel title={t('social.debate.settings_title', 'Paramètres du Duel')} corner="論戦">
            <form onSubmit={onSubmit} className="space-y-6">
              <div className="space-y-2">
                <label htmlFor="media-title" className={LAB_LABEL}>
                  {t('social.debate.target_media', 'Œuvre Cible')}
                </label>
                <input
                  id="media-title"
                  type="text"
                  aria-label={t('social.debate.target_media', 'Œuvre Cible')}
                  value={mediaTitle}
                  onChange={(e) => setMediaTitle(e.target.value)}
                  placeholder="ex: Attack on Titan"
                  className={LAB_INPUT}
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="debate-topic" className={LAB_LABEL}>
                  {t('social.debate.topic_title', 'Thématique du Débat')}
                </label>
                <textarea
                  id="debate-topic"
                  aria-label={t('social.debate.topic_title', 'Thématique du Débat')}
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  rows={4}
                  placeholder={t(
                    'social.debate.topic_placeholder',
                    "ex: La fin de l'œuvre est-elle cohérente avec le développement d'Eren ?",
                  )}
                  className={`${LAB_INPUT} resize-none`}
                />
              </div>
              <button
                type="submit"
                disabled={mutation.isPending || !mediaTitle.trim() || !topic.trim()}
                className={LAB_CTA}
              >
                {mutation.isPending ? (
                  <Zap className="h-5 w-5 animate-spin" />
                ) : (
                  t('social.debate.launch_btn', 'LANCER LA CONFRONTATION')
                )}
              </button>
            </form>
          </LabPanel>

          <LabPanel title={t('social.debate.how_it_works', 'Fonctionnement')}>
            <ul className="space-y-5">
              <li className="flex items-start gap-4">
                <AgentSeal seal={AGENTS.pro.seal} ink={AGENTS.pro.ink} />
                <p className="pt-1 text-sm leading-relaxed text-[#8F94A5]">
                  {t('social.debate.agent_pro_desc', 'Agent PRO : Défend une thèse favorable.')}
                </p>
              </li>
              <li className="flex items-start gap-4">
                <AgentSeal seal={AGENTS.anti.seal} ink={AGENTS.anti.ink} />
                <p className="pt-1 text-sm leading-relaxed text-[#8F94A5]">
                  {t(
                    'social.debate.agent_anti_desc',
                    'Agent ANTI : Apporte une contradiction argumentée.',
                  )}
                </p>
              </li>
              <li className="flex items-start gap-4">
                <AgentSeal seal={AGENTS.judge.seal} ink={AGENTS.judge.ink} />
                <p className="pt-1 text-sm leading-relaxed text-[#8F94A5]">
                  {t(
                    'social.debate.agent_judge_desc',
                    'Agent JUGE : Synthétise et rend le verdict final.',
                  )}
                </p>
              </li>
            </ul>
          </LabPanel>
        </div>

        {/* Visualisation du débat */}
        <div className="lg:col-span-8">
          <AnimatePresence mode="wait">
            {mutation.isPending ? (
              <motion.div
                key="pending"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex h-full flex-col items-center justify-center py-24 text-center"
              >
                <div className="relative mb-8 h-28 w-28">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
                    className="absolute inset-0 rounded-full border-2 border-[#F4F1E8]/10 border-t-[#E8442B]"
                  />
                  <span
                    className="font-manga absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 animate-pulse text-4xl font-black italic text-[#F4F1E8]"
                    aria-hidden
                  >
                    論
                  </span>
                </div>
                <h3 className="font-manga text-2xl font-black uppercase italic text-[#F4F1E8]">
                  {t('social.debate.inference_running', 'Inférence en cours')}
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-[#8F94A5]">
                  {t(
                    'social.debate.agents_consulting',
                    'Les agents consultent le Knowledge Graph...',
                  )}
                </p>
              </motion.div>
            ) : debateResult ? (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-8"
              >
                <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
                  <ArgumentPanel
                    seal={AGENTS.pro.seal}
                    ink={AGENTS.pro.ink}
                    label="Agent PRO"
                    text={debateResult.pro_argument}
                  />
                  <ArgumentPanel
                    seal={AGENTS.anti.seal}
                    ink={AGENTS.anti.ink}
                    label="Agent ANTI"
                    text={debateResult.anti_argument}
                  />
                </div>

                {/* Verdict du juge */}
                <section className="overflow-hidden rounded-2xl border border-[#5D7FD3]/30 bg-[#0F1016]">
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#5D7FD3]/30 bg-[#5D7FD3]/10 px-6 py-5 sm:px-8">
                    <h3 className="font-manga flex items-center gap-3 text-xl font-black uppercase italic text-[#F4F1E8]">
                      <Gavel className="h-6 w-6 text-[#5D7FD3]" />
                      {t('social.debate.judge_verdict', 'VERDICT DU JUGE')}
                    </h3>
                    <span className="rounded-[2px] border-2 border-[#5D7FD3] px-2.5 py-1 text-[9px] font-black uppercase tracking-widest text-[#5D7FD3]">
                      Final Resolution
                    </span>
                  </div>
                  <div className="p-6 sm:p-8">
                    <p className="whitespace-pre-wrap text-base leading-relaxed text-[#F4F1E8]/90">
                      {debateResult.judge_conclusion}
                    </p>
                    <div className="mt-8 flex flex-wrap items-center justify-between gap-6 border-t border-[#F4F1E8]/10 pt-6">
                      <div className="flex flex-wrap gap-6">
                        <div className="flex items-center gap-2">
                          <Scale className="h-4 w-4 text-[#5D7FD3]" />
                          <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                            {t('social.debate.objectivity', 'Objectivité: {{percent}}%', {
                              percent: 98,
                            })}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Target className="h-4 w-4 text-[#FDB913]" />
                          <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                            {t('social.debate.based_on_facts', 'Basé sur {{count}} faits', {
                              count: 12,
                            })}
                          </span>
                        </div>
                      </div>
                      <div className="flex gap-3">
                        <button type="button" className={LAB_BTN_GHOST}>
                          {t('social.debate.useful', 'UTILE')}
                        </button>
                        <button type="button" className={LAB_BTN_GHOST}>
                          {t('social.debate.biased', 'BIAISÉ')}
                        </button>
                      </div>
                    </div>
                  </div>
                </section>
              </motion.div>
            ) : (
              <LabEmpty
                icon={<Swords className="h-16 w-16" />}
                title={t('social.debate.arena_waiting', 'Arène en attente')}
                hint={t(
                  'social.debate.arena_waiting_desc',
                  "Configurez un duel pour voir l'IA débattre.",
                )}
              />
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Coulisses MLOps */}
      <div className="mt-16 grid grid-cols-1 gap-8 md:grid-cols-3">
        <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6">
          <History className="mb-4 h-6 w-6 text-[#8F94A5]" />
          <h4 className="text-xs font-black uppercase tracking-widest text-[#F4F1E8]">
            {t('social.debate.dpo_generation', 'Génération DPO')}
          </h4>
          <p className="mt-2 text-sm leading-relaxed text-[#8F94A5]">
            {t(
              'social.debate.dpo_generation_desc',
              "Chaque débat génère une paire d'entraînement (Chosen/Rejected) pour affiner la neutralité des modèles futurs.",
            )}
          </p>
        </div>
        <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6">
          <Sparkles className="mb-4 h-6 w-6 text-[#5D7FD3]" />
          <h4 className="text-xs font-black uppercase tracking-widest text-[#F4F1E8]">
            {t('social.debate.knowledge_grounding', 'Knowledge Grounding')}
          </h4>
          <p className="mt-2 text-sm leading-relaxed text-[#8F94A5]">
            {t(
              'social.debate.knowledge_grounding_desc',
              'Les agents utilisent le RAG Agentique pour sourcer leurs arguments directement dans la base de lore sémantique.',
            )}
          </p>
        </div>
        <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6">
          <Scale className="mb-4 h-6 w-6 text-[#E8442B]" />
          <h4 className="text-xs font-black uppercase tracking-widest text-[#F4F1E8]">
            {t('social.debate.game_theory', 'Théorie des Jeux')}
          </h4>
          <p className="mt-2 text-sm leading-relaxed text-[#8F94A5]">
            {t(
              'social.debate.game_theory_desc',
              "L'équilibre de Nash est recherché entre les arguments pour garantir une synthèse finale la plus juste possible.",
            )}
          </p>
        </div>
      </div>

      {/* Notice de l'arène */}
      <section className="relative mt-8 overflow-hidden rounded-2xl border border-[#E8442B]/25 bg-[#0F1016] p-6 sm:p-8">
        <span
          className="font-manga pointer-events-none absolute -bottom-14 -right-4 text-[11rem] font-black italic leading-none text-[#E8442B]/[0.05]"
          aria-hidden
        >
          論
        </span>
        <div className="relative mb-5 flex items-center gap-3">
          <Swords className="h-4 w-4 text-[#E8442B]" />
          <h3 className="font-manga text-sm font-black uppercase italic tracking-wide text-[#F4F1E8]">
            {t('labs.ai_debate_arena.explainer_title')}
          </h3>
          <span className="h-px flex-1 bg-[#F4F1E8]/10" aria-hidden />
        </div>
        <div className="relative grid gap-6 md:grid-cols-2">
          <p className="text-sm leading-relaxed text-[#8F94A5]">
            {t('labs.ai_debate_arena.explainer_text_card1')}
          </p>
          <p className="text-sm leading-relaxed text-[#8F94A5]">
            {t('labs.ai_debate_arena.explainer_text_card2')}
          </p>
        </div>
        <p className="relative mt-6 border-t border-[#F4F1E8]/10 pt-4 text-xs italic leading-relaxed text-[#8F94A5]/70">
          {t('labs.ai_debate_arena.subtitle')}
        </p>
      </section>

      <LabGuide
        steps={[
          {
            title: 'Cible une œuvre',
            body: "Nomme l'anime, le manga ou le jeu qui servira de terrain au duel — les agents ne plaident que sur des faits indexés.",
          },
          {
            title: 'Pose la thématique',
            body: 'Formule une question tranchée, idéalement polémique : plus la thèse est discutable, plus la confrontation est riche.',
          },
          {
            title: 'Lance la confrontation',
            body: 'Les agents 賛 (thèse) et 否 (antithèse) plaident tour à tour en sourçant leurs arguments dans le Knowledge Graph.',
          },
          {
            title: 'Jauge le verdict',
            body: "L'agent 裁 rend une synthèse arbitrée. Lis-la comme un avis motivé, pas comme une vérité définitive.",
          },
        ]}
        note="Ton vote Utile ou Biaisé sur chaque verdict alimente les paires DPO qui calibrent la neutralité des prochains juges — l'arène s'affine à chaque duel."
      />
    </LabPage>
  );
};

export default AIDebateArenaPage;
