import React, { useState } from 'react';
import { BarChart3, Loader2, Activity, ChevronDown, Network, Scale } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { apiClient } from '../../utils/apiClient';
import { MoePrincipleModal } from './components/MoePrincipleModal';
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
  weights?: Record<string, number>;
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

const displayName = (agent: string) => agent.replace(/_/g, ' ');

const SwarmLabPage: React.FC = () => {
  const [swarmFact, setSwarmFact] = useState(
    'Les Poneglyphes gravent l’histoire du Siècle Oublié.',
  );
  const [swarmMedia, setSwarmMedia] = useState('One Piece');
  const [swarmResult, setSwarmResult] = useState<SwarmResult | null>(null);
  const [showPaxos, setShowPaxos] = useState(false);
  const [showPrinciple, setShowPrinciple] = useState(false);

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

  const sortedByWeight = swarmResult?.votes
    ? Object.entries(swarmResult.votes).sort(
        ([a], [b]) => (swarmResult.weights?.[b] ?? 0) - (swarmResult.weights?.[a] ?? 0),
      )
    : [];
  const hasWeights = !!swarmResult?.weights && Object.keys(swarmResult.weights).length > 0;

  return (
    <LabPage>
      <LabHeader
        code="Concept · Mixture-of-Experts"
        title="Mixture"
        accent="of Experts"
        glyph="混成"
        lede="Plutôt qu'un seul modèle qui prétend tout savoir, un Mixture-of-Experts réunit des spécialistes et un « routeur » qui, pour chaque question, décide qui fait autorité. Ce lab en est une démonstration vivante : propose un fait de lore, regarde le routeur pondérer sept experts, puis trancher."
      />

      <MoePrincipleModal isOpen={showPrinciple} onClose={() => setShowPrinciple(false)} />

      <div className="mb-8 flex items-center gap-4">
        <span className="h-6 w-1.5 flex-none bg-[#E8442B]" aria-hidden />
        <h2 className="font-manga text-xl font-black uppercase italic tracking-wide text-[#F4F1E8] md:text-2xl">
          Le MoE en action
        </h2>
        <span className="h-px flex-1 bg-[#F4F1E8]/10" aria-hidden />
        <button
          type="button"
          onClick={() => setShowPrinciple(true)}
          className="group relative inline-flex flex-none cursor-pointer items-center gap-2.5 overflow-hidden rounded-xl border-2 border-[#E8442B] bg-[#E8442B]/[0.07] px-5 py-3 text-left transition-colors hover:bg-[#E8442B]/[0.14] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
        >
          <span
            aria-hidden="true"
            className="font-manga pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 select-none text-5xl font-black italic leading-none text-[#E8442B]/20"
          >
            理
          </span>
          <Network className="relative z-10 h-4 w-4 flex-none text-[#E8442B]" aria-hidden="true" />
          <span className="relative z-10 font-manga text-sm font-black uppercase italic tracking-wide text-[#F4F1E8]">
            Le principe
          </span>
        </button>
      </div>

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
                  'Router & voter'
                )}
              </button>
              <p className="text-xs leading-relaxed text-[#8F94A5]">
                Un <span className="font-bold text-[#5D7FD3]">seul appel</span> au modèle local
                renvoie à la fois les poids du routeur et les votes des experts.
              </p>
            </div>
          </LabPanel>
        </div>

        {/* Résultats — le pipeline MoE, étape par étape */}
        <div className="lg:col-span-8">
          <AnimatePresence mode="wait">
            {swarmMutation.isPending ? (
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <LabPanel
                  title="Routage en cours"
                  corner={
                    <span className="flex items-center gap-1.5 text-[#5D7FD3]">
                      <Network className="h-3.5 w-3.5" aria-hidden="true" /> MoE
                    </span>
                  }
                >
                  <div className="flex min-h-[260px] flex-col items-center justify-center py-8 text-center">
                    <Loader2
                      className="mb-6 h-9 w-9 animate-spin text-[#5D7FD3]"
                      aria-hidden="true"
                    />
                    <p className="font-manga text-lg font-black uppercase italic text-[#F4F1E8]">
                      Le routeur pondère les experts…
                    </p>
                    <p className="mb-8 mt-2 max-w-sm text-xs leading-relaxed text-[#8F94A5]">
                      Un appel au modèle local calcule les poids du routeur, puis les votes des sept
                      experts.
                    </p>
                    <div
                      className="relative h-1.5 w-full max-w-md overflow-hidden rounded-full bg-[#F4F1E8]/10"
                      role="progressbar"
                      aria-label="Chargement du vote de l'essaim"
                    >
                      <motion.div
                        className="absolute inset-y-0 left-0 w-1/3 rounded-full bg-[#5D7FD3]"
                        animate={{ x: ['-110%', '330%'] }}
                        transition={{ duration: 1.3, repeat: Infinity, ease: 'easeInOut' }}
                      />
                    </div>
                  </div>
                </LabPanel>
              </motion.div>
            ) : swarmResult ? (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -16 }}
                className="space-y-8"
              >
                {/* Étape 1 — le routeur pondère */}
                {hasWeights && (
                  <LabPanel
                    title="Étape 1 — Le routeur pondère"
                    corner={
                      <span className="flex items-center gap-1.5 text-[#5D7FD3]">
                        <Network className="h-3.5 w-3.5" aria-hidden="true" /> gating
                      </span>
                    }
                  >
                    <p className="mb-5 text-xs leading-relaxed text-[#8F94A5]">
                      Avant tout vote, le routeur estime la{' '}
                      <span className="text-[#5D7FD3]">pertinence</span> de chaque expert pour ce
                      fait précis. Plus la barre est longue, plus son avis pèsera dans la décision
                      finale.
                    </p>
                    <div className="space-y-2.5">
                      {sortedByWeight.map(([agent]) => {
                        const w = swarmResult.weights?.[agent] ?? 0;
                        return (
                          <div key={agent} className="flex items-center gap-3">
                            <span className="w-36 flex-none truncate text-[10px] font-black uppercase tracking-widest text-[#8F94A5] sm:w-44">
                              {displayName(agent)}
                            </span>
                            <div className="h-2 flex-1 overflow-hidden rounded-full bg-[#F4F1E8]/10">
                              <div
                                className="h-full bg-[#5D7FD3] transition-all duration-700"
                                style={{ width: `${w * 100}%` }}
                              />
                            </div>
                            <span className="w-9 flex-none text-right text-[10px] font-black tabular-nums text-[#5D7FD3]">
                              {Math.round(w * 100)}%
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </LabPanel>
                )}

                {/* Étape 2 — les experts votent */}
                <LabPanel
                  title="Étape 2 — Les experts votent"
                  corner={
                    <span className="flex items-center gap-1.5">
                      <BarChart3 className="h-3.5 w-3.5" aria-hidden="true" /> véracité
                    </span>
                  }
                >
                  <p className="mb-5 text-xs leading-relaxed text-[#8F94A5]">
                    Chaque expert donne sa confiance que le fait soit vrai. Les cartes sont classées
                    par pertinence : celles que le routeur a écartées sont estompées — leur vote
                    comptera peu.
                  </p>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    {sortedByWeight.map(([agent, score]) => {
                      const weight = swarmResult.weights?.[agent];
                      const withWeight = typeof weight === 'number';
                      return (
                        <div
                          key={agent}
                          className="space-y-2 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4 transition-opacity"
                          style={withWeight ? { opacity: 0.45 + 0.55 * weight } : undefined}
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                              {displayName(agent)}
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
                          {withWeight && (
                            <div className="flex items-center gap-2 pt-0.5">
                              <span className="text-[9px] font-black uppercase tracking-widest text-[#5D7FD3]/80">
                                Poids
                              </span>
                              <div className="h-1 flex-1 overflow-hidden rounded-full bg-[#F4F1E8]/10">
                                <div
                                  className="h-full bg-[#5D7FD3] transition-all duration-700"
                                  style={{ width: `${weight * 100}%` }}
                                />
                              </div>
                              <span className="text-[9px] font-black tabular-nums text-[#5D7FD3]">
                                {Math.round(weight * 100)}%
                              </span>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </LabPanel>

                {/* Étape 3 — agrégation pondérée → décision */}
                <LabPanel
                  title="Étape 3 — Agrégation pondérée"
                  corner={
                    <span className="flex items-center gap-1.5">
                      <Scale className="h-3.5 w-3.5" aria-hidden="true" /> seuil 70 %
                    </span>
                  }
                >
                  <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                    <LabStat
                      label="Consensus pondéré"
                      value={`${((swarmResult.consensus_score || 0) * 100).toFixed(1)}%`}
                      tone="gold"
                    />
                    <LabStat
                      label="Décision collective"
                      value={swarmResult.is_recorded ? 'Fait accepté' : 'Fait rejeté'}
                      tone={swarmResult.is_recorded ? 'paper' : 'shu'}
                    />
                    <LabStat
                      label="Experts consultés"
                      value={Object.keys(swarmResult.votes || {}).length || '—'}
                    />
                  </div>
                  <p className="mt-6 text-xs leading-relaxed text-[#8F94A5]">
                    Le consensus n'est pas une simple moyenne : c'est la{' '}
                    <span className="font-bold text-[#F4F1E8]">
                      somme des votes multipliés par leur poids
                    </span>
                    , divisée par la somme des poids —{' '}
                    <span className="font-mono text-[#5D7FD3]">Σ(vote × poids) ⁄ Σ(poids)</span>. Un
                    expert hors sujet ne peut donc ni sauver ni couler un fait. Au-delà de 70 %, le
                    fait entre au Knowledge Graph.
                  </p>
                </LabPanel>

                {/* Comment la décision est scellée (Paxos) */}
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
                        Comment la décision est scellée
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
                          Une fois le consensus calculé, la décision est figée en trois temps
                          (protocole inspiré de « Paxos ») : on ouvre un tour, on vérifie
                          qu&apos;assez d&apos;experts sont d&apos;accord, puis on scelle le
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
                              } experts convaincus pour valider — c'est le « quorum ».`,
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
                key="empty"
                icon={<Network className="h-20 w-20" aria-hidden="true" />}
                title="Routeur en veille"
                hint="Renseigne un média et un fait de lore, puis lance le routage : tu verras le routeur pondérer les sept experts, leurs votes, puis le verdict."
              />
            )}
          </AnimatePresence>
        </div>
      </div>

      <LabGuide
        steps={[
          {
            title: 'Le routeur choisit',
            body: "Pour ton fait, un « gating » attribue à chacun des sept experts un poids de pertinence — c'est le cœur d'un Mixture-of-Experts.",
          },
          {
            title: 'Les experts votent',
            body: 'Chaque spécialiste juge la véracité du fait sous son angle, indépendamment des autres.',
          },
          {
            title: 'La somme pondérée tranche',
            body: 'Les votes sont moyennés en fonction des poids du routeur : au-delà de 70 %, le protocole Paxos-sémantique scelle l’écriture au Knowledge Graph.',
          },
        ]}
        note="La pondération du routeur évite qu'un expert hors sujet fasse dérailler la décision, tout en préservant la robustesse du vote collectif : le consensus filtre hallucinations et biais individuels avant toute écriture permanente."
      />
    </LabPage>
  );
};

export default SwarmLabPage;
