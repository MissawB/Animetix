import React from 'react';
import {
  ShieldCheck,
  Trash2,
  Activity,
  Zap,
  RefreshCw,
  Lock,
  Fingerprint,
  Target,
  Scale,
  Loader2,
} from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import {
  LabPage,
  LabHeader,
  LabPanel,
  LabEmpty,
  LabGuide,
  LAB_CTA,
  LAB_BTN_GHOST,
} from '../labs/components/shared/LabKit';

import { NeuroMemoryData, DeducedRule, NeuralSignal } from '../../types';

const NeuroMemoryPage: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading, refetch } = useQuery<NeuroMemoryData>({
    queryKey: ['neuro-memory'],
    queryFn: () => apiClient('/api/v1/cognition/neuro-memory/'),
  });

  const resetMutation = useMutation({
    mutationFn: () =>
      apiClient('/api/v1/cognition/neuro-memory/', {
        method: 'POST',
        body: JSON.stringify({ action: 'reset' }),
      }),
    onSuccess: () => refetch(),
  });

  const signalMutation = useMutation({
    mutationFn: (body: { action: string; feedback_id: number; weight?: number }) =>
      apiClient('/api/v1/cognition/neuro-memory/', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: () => refetch(),
  });

  if (isLoading)
    return (
      <div className="flex min-h-screen w-full flex-col items-center justify-center bg-[#0B0C10]">
        <Loader2 className="mb-8 h-12 w-12 animate-spin text-[#FDB913]" aria-hidden="true" />
        <p className="text-sm font-black uppercase tracking-[0.3em] text-[#8F94A5]">
          {t('social.neuro.loading', 'Accessing Neural Engrams...')}
        </p>
      </div>
    );

  return (
    <LabPage>
      <LabHeader
        glyph="憶"
        code="Synapse · Mémoire"
        title="Neuro"
        accent="Memory"
        lede={t(
          'social.neuro.subtitle',
          "Gérez les règles logiques déduites par l'IA et contrôlez votre empreinte cognitive.",
        )}
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Logic Profile Summary */}
        <div className="space-y-8 lg:col-span-4">
          <LabPanel
            title="Trust center"
            corner={
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />{' '}
                {t('social.neuro.privacy_badge', 'Cognitive Privacy Protocol')}
              </span>
            }
          >
            <p className="mb-8 text-sm leading-relaxed text-[#8F94A5]">
              {t(
                'social.neuro.trust_desc',
                'Vous avez un contrôle total sur ce que le solveur Z3 déduit de vos interactions. Vous pouvez réinitialiser votre profil logique à tout moment.',
              )}
            </p>
            <div className="mb-8 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-6">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                  Signaux neuronaux
                </span>
                <span className="font-manga text-xl font-black italic text-[#FDB913]">
                  {data?.total_signals || 0}
                </span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#F4F1E8]/10">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: '75%' }}
                  className="h-full bg-[#FDB913]"
                />
              </div>
            </div>
            <button
              type="button"
              onClick={() => resetMutation.mutate()}
              disabled={resetMutation.isPending}
              className={LAB_CTA}
            >
              {resetMutation.isPending ? (
                <Loader2 className="h-6 w-6 animate-spin" aria-hidden="true" />
              ) : (
                'Réinitialiser le profil logique'
              )}
            </button>
          </LabPanel>

          <LabPanel title={t('social.neuro.deduction_system', 'Système de Déduction')}>
            <ul className="space-y-4">
              <li className="flex gap-3 text-xs leading-relaxed text-[#8F94A5]">
                <Target className="h-4 w-4 shrink-0 text-[#FDB913]" aria-hidden="true" /> Solveur
                formel : Z3 theorem prover.
              </li>
              <li className="flex gap-3 text-xs leading-relaxed text-[#8F94A5]">
                <Scale className="h-4 w-4 shrink-0 text-[#FDB913]" aria-hidden="true" />{' '}
                {t('social.neuro.constraints', 'Contraintes: Logique SAT binaire.')}
              </li>
              <li className="flex gap-3 text-xs leading-relaxed text-[#8F94A5]">
                <Lock className="h-4 w-4 shrink-0 text-[#FDB913]" aria-hidden="true" />{' '}
                Confidentialité : inférence local-first.
              </li>
            </ul>
          </LabPanel>
        </div>

        {/* Deduced Rules List */}
        <div className="lg:col-span-8">
          <LabPanel title="Engrammes neuronaux" corner="règles actives">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {data?.deduced_rules && data.deduced_rules.length > 0 ? (
                data.deduced_rules.map((item: DeducedRule) => (
                  <div
                    key={item.id}
                    className="flex flex-col justify-between rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-5 transition-colors hover:border-[#FDB913]/40"
                  >
                    <div>
                      <div className="mb-4 flex items-start justify-between">
                        <div className="rounded-lg bg-[#FDB913]/10 p-2.5 text-[#FDB913]">
                          <Zap className="h-4 w-4 fill-current" aria-hidden="true" />
                        </div>
                        <span className="text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                          {item.source}
                        </span>
                      </div>
                      <h4 className="font-manga mb-2 text-lg font-black uppercase italic tracking-tighter text-[#F4F1E8]">
                        {item.rule.replace(' == ', ': ')}
                      </h4>
                      <p className="text-[10px] leading-relaxed text-[#8F94A5]">
                        {t(
                          'social.neuro.deduced_via',
                          'Déduit via analyse sémantique des feedbacks récents.',
                        )}
                      </p>
                    </div>
                    <div className="mt-6 flex items-center justify-between border-t border-[#F4F1E8]/10 pt-4">
                      <span className="text-[10px] font-black uppercase tracking-widest text-[#FDB913]">
                        Confiance : {item.confidence * 100}%
                      </span>
                      <button className="text-[#E8442B]/50 transition-colors hover:text-[#E8442B]">
                        <Trash2 className="h-4 w-4" aria-hidden="true" />
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="col-span-full">
                  <LabEmpty
                    icon={<Activity className="h-16 w-16" aria-hidden="true" />}
                    title="Données insuffisantes"
                    hint="Interagis avec Animetix (forge, débats, feedbacks) pour que le solveur Z3 puisse déduire tes premières règles logiques."
                  />
                </div>
              )}
            </div>
          </LabPanel>
        </div>
      </div>

      {/* Granular Signal Management */}
      <div className="mt-16">
        <LabPanel
          title="Gestion des signaux bruts"
          corner={
            <span className="flex items-center gap-1.5">
              <Activity className="h-3.5 w-3.5" aria-hidden="true" /> contrôle granulaire
            </span>
          }
        >
          <p className="mb-6 text-xs leading-relaxed text-[#8F94A5]">
            {t(
              'social.neuro.signal_desc',
              'Ajustez le poids de chaque interaction ou révoquez les signaux obsolètes.',
            )}
          </p>
          <div className="grid grid-cols-1 gap-4">
            {data?.signals && data.signals.length > 0 ? (
              data.signals.map((signal: NeuralSignal) => (
                <div
                  key={signal.id}
                  className={`flex flex-col items-center gap-8 rounded-xl border p-6 transition-colors md:flex-row ${
                    signal.is_ignored
                      ? 'border-[#F4F1E8]/5 bg-[#0B0C10] opacity-40'
                      : 'border-[#F4F1E8]/10 bg-[#0B0C10] hover:border-[#FDB913]/30'
                  }`}
                >
                  <div className="flex shrink-0 items-center gap-4">
                    <div
                      className={`rounded-lg p-2.5 ${
                        signal.is_positive
                          ? 'bg-[#FDB913]/10 text-[#FDB913]'
                          : 'bg-[#E8442B]/10 text-[#E8442B]'
                      }`}
                    >
                      {signal.is_positive ? (
                        <Zap className="h-4 w-4 fill-current" aria-hidden="true" />
                      ) : (
                        <ShieldCheck className="h-4 w-4" aria-hidden="true" />
                      )}
                    </div>
                    <div className="text-right">
                      <p className="text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                        Poids
                      </p>
                      <p className="font-manga text-sm font-black italic text-[#F4F1E8]">
                        x{signal.weight.toFixed(1)}
                      </p>
                    </div>
                  </div>

                  <div className="flex-grow">
                    <p className="text-xs font-bold italic text-[#F4F1E8]/70">
                      "{signal.input_context}"
                    </p>
                    <p className="mt-1 text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                      {new Date(signal.created_at).toLocaleDateString()} • {signal.feedback_type}
                    </p>
                  </div>

                  <div className="flex shrink-0 items-center gap-6">
                    <div className="flex w-32 flex-col gap-1">
                      <input
                        type="range"
                        aria-label={t('social.neuro.signal_weight_label', 'Poids du signal')}
                        min="0.1"
                        max="2.0"
                        step="0.1"
                        defaultValue={signal.weight}
                        onChange={(e) =>
                          signalMutation.mutate({
                            action: 'update_weight',
                            feedback_id: signal.id,
                            weight: parseFloat(e.target.value),
                          })
                        }
                        className="h-1 w-full cursor-pointer appearance-none rounded-lg bg-[#F4F1E8]/10 accent-[#FDB913]"
                      />
                      <div className="flex justify-between text-[8px] font-black uppercase text-[#8F94A5]">
                        <span>Faible</span>
                        <span>Dominant</span>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() =>
                        signalMutation.mutate({
                          action: signal.is_ignored ? 'restore' : 'revoke',
                          feedback_id: signal.id,
                        })
                      }
                      className={`${LAB_BTN_GHOST} ${
                        signal.is_ignored
                          ? 'hover:border-[#FDB913] hover:text-[#FDB913]'
                          : 'hover:border-[#E8442B] hover:text-[#E8442B]'
                      }`}
                    >
                      {signal.is_ignored ? (
                        <>
                          <RefreshCw className="h-3 w-3" aria-hidden="true" /> Restaurer
                        </>
                      ) : (
                        <>
                          <Trash2 className="h-3 w-3" aria-hidden="true" /> Révoquer
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <LabEmpty
                icon={<Fingerprint className="h-16 w-16" aria-hidden="true" />}
                title="Aucun signal archivé"
                hint="Chaque feedback que tu donnes à l'IA laisse un signal cognitif : ils apparaîtront ici, prêts à être pondérés ou révoqués."
              />
            )}
          </div>
        </LabPanel>
      </div>

      {/* Guide & Protocole */}
      <LabGuide
        steps={[
          {
            title: t('social.neuro.guide_what_title', "Qu'est-ce que c'est ?"),
            body: t(
              'social.neuro.guide_what_desc',
              'Cette page est votre "Panneau de Contrôle Cognitif". À chaque fois que vous interagissez avec Animetix, notre IA essaie de comprendre vos goûts, vos valeurs et vos habitudes.',
            ),
          },
          {
            title: t('social.neuro.guide_engrams_title', 'Les Engrammes :'),
            body: t(
              'social.neuro.guide_engrams_desc',
              'Ce sont les "règles" que l\'IA a déduites sur vous (ex: "Vous préférez les héros solitaires"). Vous pouvez voir ces règles à droite et décider de les garder ou de les supprimer.',
            ),
          },
          {
            title: t('social.neuro.guide_reset_title', 'Pourquoi réinitialiser ?'),
            body: t(
              'social.neuro.guide_reset_desc',
              'Si vous sentez que l\'IA se trompe sur vous ou que vous voulez repartir de zéro pour changer d\'archétype, utilisez le bouton "RESET" en haut à gauche.',
            ),
          },
        ]}
        note={`${t(
          'social.neuro.warning_line1',
          'Avertissement : Les déductions neuro-symboliques sont basées sur des modèles stochastiques résolus en temps réel.',
        )} ${t(
          'social.neuro.warning_line2',
          'Le profil logique est synchronisé avec votre Archétype Nexus.',
        )}`}
      />
    </LabPage>
  );
};

export default NeuroMemoryPage;
