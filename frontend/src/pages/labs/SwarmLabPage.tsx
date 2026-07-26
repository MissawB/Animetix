import React, { useState } from 'react';
import { Users, BarChart3, Loader2, Activity, ChevronDown } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { apiClient } from '../../utils/apiClient';
import {
  LabPage,
  LabHeader,
  LabPanel,
  LabStat,
  LabEmpty,
  LabGuide,
  LAB_INPUT,
  LAB_LABEL,
  LAB_CTA,
} from './components/shared/LabKit';

interface SwarmResult {
  consensus_score: number;
  is_recorded: boolean;
  votes: Record<string, number>;
  phases?: {
    prepare?: {
      proposal_id: number;
      promises_received: string[];
    };
    accept?: {
      quorum_required: number;
      threshold: number;
    };
    learn?: {
      paxos_state: string;
      message: string;
    };
  };
}

const PHASE_TONES = ['text-[#FDB913]', 'text-[#F4F1E8]', 'text-[#E8442B]'] as const;

const SwarmLabPage: React.FC = () => {
  const [swarmFact, setSwarmFact] = useState('Luffy est plus fort que Naruto.');
  const [swarmMedia, setSwarmMedia] = useState('One Piece');
  const [swarmResult, setSwarmResult] = useState<SwarmResult | null>(null);
  const [showPaxos, setShowPaxos] = useState(false);

  const swarmMutation = useMutation<
    SwarmResult,
    Error,
    { action: string; fact: string; media: string }
  >({
    mutationFn: (body: { action: string; fact: string; media: string }) =>
      apiClient('/api/v1/singularity-lab/', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => setSwarmResult(data),
  });

  return (
    <LabPage>
      <LabHeader
        code="Protocole · Swarm"
        title="Consensus"
        accent="d'essaim"
        lede="Sept agents IA spécialisés votent sur tes propositions de lore. Un fait n'entre au Knowledge Graph que si l'essaim atteint 70 % de consensus sémantique."
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Proposition */}
        <div className="lg:col-span-4">
          <LabPanel title="Proposition">
            <div className="space-y-6">
              <div className="space-y-2">
                <label htmlFor="swarm-media" className={LAB_LABEL}>
                  Média cible
                </label>
                <input
                  id="swarm-media"
                  aria-label="Média cible"
                  type="text"
                  value={swarmMedia}
                  onChange={(e) => setSwarmMedia(e.target.value)}
                  placeholder="Nom de l'anime ou du manga…"
                  className={LAB_INPUT}
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="swarm-fact" className={LAB_LABEL}>
                  Fait à soumettre
                </label>
                <textarea
                  id="swarm-fact"
                  aria-label="Fait sémantique"
                  value={swarmFact}
                  onChange={(e) => setSwarmFact(e.target.value)}
                  rows={4}
                  placeholder="Ex. : le Gear 5 représente la liberté absolue…"
                  className={`${LAB_INPUT} resize-none`}
                />
              </div>
              <button
                type="button"
                onClick={() =>
                  swarmMutation.mutate({ action: 'swarm', fact: swarmFact, media: swarmMedia })
                }
                disabled={swarmMutation.isPending}
                className={LAB_CTA}
              >
                {swarmMutation.isPending ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  'Lancer le vote'
                )}
              </button>
            </div>
          </LabPanel>
        </div>

        {/* Résultats */}
        <div className="lg:col-span-8">
          <AnimatePresence mode="wait">
            {swarmResult ? (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -16 }}
                className="space-y-10"
              >
                <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                  <LabStat
                    label="Consensus"
                    value={`${((swarmResult.consensus_score || 0) * 100).toFixed(1)}%`}
                    tone="gold"
                  />
                  <LabStat
                    label="Décision collective"
                    value={swarmResult.is_recorded ? 'Fait accepté' : 'Fait rejeté'}
                    tone={swarmResult.is_recorded ? 'paper' : 'shu'}
                  />
                  <LabStat
                    label="Experts votants"
                    value={Object.keys(swarmResult.votes || {}).length || '—'}
                  />
                </div>

                <LabPanel
                  title="Votes individuels"
                  corner={
                    <span className="flex items-center gap-1.5">
                      <BarChart3 className="h-3.5 w-3.5" aria-hidden="true" /> seuil 70 %
                    </span>
                  }
                >
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    {swarmResult.votes &&
                      Object.entries(swarmResult.votes).map(([agent, score]) => (
                        <div
                          key={agent}
                          className="space-y-2 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                              {agent.replace('_', ' ')}
                            </span>
                            <span
                              className={`text-xs font-black ${
                                score >= 0.7 ? 'text-[#FDB913]' : 'text-[#E8442B]'
                              }`}
                            >
                              {Math.round(score * 100)}%
                            </span>
                          </div>
                          <div className="h-1.5 overflow-hidden rounded-full bg-[#F4F1E8]/10">
                            <div
                              className={`h-full transition-all duration-700 ${
                                score >= 0.7 ? 'bg-[#FDB913]' : 'bg-[#E8442B]'
                              }`}
                              style={{ width: `${score * 100}%` }}
                            />
                          </div>
                        </div>
                      ))}
                  </div>
                </LabPanel>

                {swarmResult.phases && (
                  <div className="overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016]">
                    <button
                      type="button"
                      onClick={() => setShowPaxos((v) => !v)}
                      aria-expanded={showPaxos}
                      className="flex w-full items-center gap-3 p-6 text-left transition-colors hover:bg-[#F4F1E8]/[0.02] sm:p-8"
                    >
                      <span className="h-4 w-1 flex-none bg-[#E8442B]" aria-hidden />
                      <h3 className="font-manga text-sm font-black uppercase italic tracking-wide text-[#F4F1E8]">
                        Comment la décision est prise
                      </h3>
                      <span className="ml-auto flex items-center gap-3">
                        <span className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest text-[#FDB913]">
                          <Activity className="h-3.5 w-3.5" aria-hidden="true" />{' '}
                          {swarmResult.phases?.learn?.paxos_state}
                        </span>
                        <ChevronDown
                          className={`h-4 w-4 text-[#8F94A5] transition-transform ${showPaxos ? 'rotate-180' : ''}`}
                          aria-hidden="true"
                        />
                      </span>
                    </button>
                    {showPaxos && (
                      <div className="px-6 pb-8 sm:px-8">
                        <p className="mb-6 text-sm leading-relaxed text-[#8F94A5]">
                          Pour éviter qu&apos;un seul expert impose son avis, la décision suit un
                          vote en 3 étapes (protocole inspiré de « Paxos ») : on ouvre un tour, on
                          vérifie qu&apos;assez d&apos;experts sont d&apos;accord, puis on scelle le
                          résultat.
                        </p>
                        <ol className="grid grid-cols-1 gap-6 md:grid-cols-3">
                          {[
                            {
                              name: 'Ouverture du tour',
                              detail: `réf. ${swarmResult.phases?.prepare?.proposal_id ?? '—'}`,
                              body: `Chaque vote reçoit une référence unique. Les experts disponibles acceptent d'y participer : ${
                                swarmResult.phases?.prepare?.promises_received?.join(', ') || '—'
                              }.`,
                            },
                            {
                              name: 'Vérification',
                              detail: `Quorum ${swarmResult.phases?.accept?.quorum_required ?? '—'} / ${
                                Object.keys(swarmResult.votes || {}).length || '—'
                              }`,
                              body: `Il faut au moins ${
                                swarmResult.phases?.accept?.quorum_required ?? '—'
                              } experts convaincus (score ≥ ${
                                (swarmResult.phases?.accept?.threshold || 0.7) * 100
                              } %) pour valider — c'est le « quorum ».`,
                            },
                            {
                              name: 'Décision',
                              detail: swarmResult.phases?.learn?.paxos_state ?? '—',
                              body: swarmResult.phases?.learn?.message ?? '—',
                            },
                          ].map((phase, i) => (
                            <li key={phase.name} className="flex gap-4">
                              <span
                                className={`font-manga flex-none text-xl font-black italic leading-none ${PHASE_TONES[i]}`}
                                aria-hidden
                              >
                                {String(i + 1).padStart(2, '0')}
                              </span>
                              <div>
                                <h4 className="text-[10px] font-black uppercase tracking-widest text-[#F4F1E8]">
                                  {phase.name}
                                  <span className="ml-2 font-bold text-[#8F94A5]">
                                    {phase.detail}
                                  </span>
                                </h4>
                                <p className="mt-1.5 text-xs leading-relaxed text-[#8F94A5]">
                                  {phase.body}
                                </p>
                              </div>
                            </li>
                          ))}
                        </ol>
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            ) : (
              <LabEmpty
                icon={<Users className="h-20 w-20" aria-hidden="true" />}
                title="Essaim en veille"
                hint="Renseigne un média et un fait de lore, puis lance le vote : les sept agents rendront leur verdict ici."
              />
            )}
          </AnimatePresence>
        </div>
      </div>

      <LabGuide
        steps={[
          {
            title: 'Propose un fait',
            body: "Choisis une œuvre et formule une affirmation de lore — l'essaim juge le fond, pas la forme.",
          },
          {
            title: "L'essaim vote",
            body: 'Sept IA expertes analysent la proposition sous des angles différents et votent indépendamment.',
          },
          {
            title: 'Le consensus tranche',
            body: 'À 70 % de votes favorables, le protocole Paxos-sémantique scelle la décision en trois phases (prepare, accept, learn).',
          },
        ]}
        note="Les faits validés sont injectés de manière permanente dans le Knowledge Graph : le consensus filtre les hallucinations et les biais individuels des agents avant toute écriture."
      />
    </LabPage>
  );
};

export default SwarmLabPage;
