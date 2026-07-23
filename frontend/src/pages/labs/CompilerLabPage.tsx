import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Cpu, Loader2, ShieldCheck, Zap } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { motion, AnimatePresence } from 'framer-motion';

import { CompilerResult } from '../../types';

import {
  LabPage,
  LabHeader,
  LabPanel,
  LabGuide,
  LAB_INPUT,
  LAB_LABEL,
  LAB_CTA,
} from './components/shared/LabKit';

const CompilerLabPage: React.FC = () => {
  const { t } = useTranslation();
  const [fnName, setFnName] = useState('semantic_cosine_opt');
  const [cCode, setCCode] = useState(
    '// Version optimisée générée à la volée\ndouble semantic_cosine_opt(double* a, double* b, int n) {\n    double dot = 0.0;\n    // ... calcul matriciel vectorisé C ...\n    return dot;\n}',
  );
  const [compilerResult, setCompilerResult] = useState<CompilerResult | null>(null);

  const compileMutation = useMutation<
    CompilerResult,
    Error,
    { action: string; function_name: string }
  >({
    mutationFn: (body: { action: string; function_name: string }) =>
      apiClient('/api/v1/singularity-lab/', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => setCompilerResult(data),
  });

  return (
    <LabPage>
      <LabHeader
        code="Protocole · JIT"
        title="Optimiseur"
        accent="JIT"
        lede={t(
          'labs.compiler.subtitle',
          'Optimisation temps réel du microcode sémantique via compilation JIT SOTA 2035.',
        )}
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Configuration */}
        <div className="space-y-8 lg:col-span-4">
          <LabPanel title="Paramètres d'optimisation">
            <div className="space-y-6">
              <div className="space-y-2">
                <label htmlFor="fn-name" className={LAB_LABEL}>
                  {t('labs.compiler.target_function', 'Fonction Cible')}
                </label>
                <input
                  id="fn-name"
                  type="text"
                  aria-label={t('labs.compiler.target_function', 'Fonction Cible')}
                  value={fnName}
                  onChange={(e) => setFnName(e.target.value)}
                  className={`${LAB_INPUT} font-mono`}
                />
              </div>

              <button
                type="button"
                onClick={() => compileMutation.mutate({ action: 'compile', function_name: fnName })}
                disabled={compileMutation.isPending}
                className={LAB_CTA}
              >
                {compileMutation.isPending ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  t('labs.compiler.submit_btn', "LANCER L'OPTIMISATION")
                )}
              </button>
            </div>
          </LabPanel>

          <LabPanel title="Pipeline JIT">
            <p className="text-sm leading-relaxed text-[#8F94A5]">
              {t(
                'labs.compiler.analysis_desc',
                "L'IA analyse le graphe d'exécution et génère du code C vectorisé pour les calculs de similarité critique.",
              )}
            </p>
            <ul className="mt-5 space-y-3">
              <li className="flex items-center gap-3 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                <span className="h-1.5 w-1.5 flex-none rounded-full bg-[#E8442B]" aria-hidden />
                Vectorisation AVX-512
              </li>
              <li className="flex items-center gap-3 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                <span className="h-1.5 w-1.5 flex-none rounded-full bg-[#E8442B]" aria-hidden />
                Injection de microcode basse latence
              </li>
            </ul>
          </LabPanel>
        </div>

        {/* Microcode & Statut */}
        <div className="lg:col-span-8">
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
            <LabPanel title="Microcode source (C)" corner="lecture seule" className="flex flex-col">
              <div className="relative min-h-[450px] flex-1">
                <textarea
                  readOnly
                  aria-label="Microcode source en C"
                  value={cCode}
                  onChange={(e) => setCCode(e.target.value)}
                  className="h-full w-full resize-none rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-6 font-mono text-sm text-[#FDB913] outline-none transition-colors focus:border-[#FDB913] custom-scrollbar"
                />
              </div>
            </LabPanel>

            <LabPanel
              title="Statut de compilation"
              corner={
                <span className="flex items-center gap-1.5">
                  <Zap className="h-3.5 w-3.5" aria-hidden="true" /> LLVM Backend 18.1
                </span>
              }
              className="flex min-h-[450px] flex-col"
            >
              <AnimatePresence mode="wait">
                {compilerResult ? (
                  <motion.div
                    key="result"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="space-y-6"
                  >
                    <div className="flex items-center gap-3 font-manga text-lg font-black uppercase italic tracking-tight text-[#FDB913]">
                      <ShieldCheck className="h-7 w-7 flex-none" aria-hidden="true" />{' '}
                      {compilerResult.message}
                    </div>

                    <div className="space-y-3 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-6">
                      <p className={LAB_LABEL}>Banc de performance</p>
                      <p className="font-mono text-sm leading-relaxed text-[#F4F1E8]/80">
                        {compilerResult.test_output}
                      </p>
                    </div>

                    <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-6">
                      <span className={`${LAB_LABEL} mb-3 block`}>Signature runtime</span>
                      <code className="block break-all font-mono text-xs text-[#FDB913]">
                        {compilerResult.c_code_generated || 'NO_SIGNATURE_GENERATED'}
                      </code>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div
                    key="empty"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex flex-1 flex-col items-center justify-center py-16 text-center"
                  >
                    <Cpu className="mb-6 h-20 w-20 text-[#8F94A5]/25" aria-hidden="true" />
                    <span className="font-manga text-xl font-black uppercase italic text-[#F4F1E8]/60">
                      {t('labs.compiler.waiting_deploy', 'En attente de déploiement')}
                    </span>
                    <p className="mt-3 max-w-xs text-sm leading-relaxed text-[#8F94A5]">
                      Renseigne une fonction cible puis lance l'optimisation : le verdict de
                      compilation s'affichera ici.
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </LabPanel>
          </div>
        </div>
      </div>

      <LabGuide
        steps={[
          {
            title: 'Le concept',
            body: t(
              'labs.compiler.guide_concept_desc',
              'Les calculs de similarité entre œuvres (cosinus, distance euclidienne) sont lents en Python pur. Cette page montre comment le serveur les accélère en les compilant à la volée.',
            ),
          },
          {
            title: 'La compilation',
            body: t(
              'labs.compiler.guide_compile_desc',
              "Entrez une fonction supportée (cosine_similarity, euclidean_distance, vector_norm) et lancez l'optimisation : le noyau est compilé en code machine puis testé immédiatement.",
            ),
          },
          {
            title: 'Le résultat',
            body: t(
              'labs.compiler.guide_result_desc',
              'Le panneau de droite affiche le statut de compilation, la sortie du test de validation et la signature du code généré. Cette action consomme des Berrix.',
            ),
          },
        ]}
        note={`${t('labs.compiler.guide_footer_1', 'Compilation JIT réelle via Numba (@njit, fastmath) : le kernel numérique Python est traduit en code machine côté serveur, puis validé sur un vecteur de test.')} ${t('labs.compiler.guide_footer_2', "Le code C affiché à gauche est illustratif — le mécanisme effectif est la génération dynamique de kernels Numpy/Numba par l'API singularity-lab.")}`}
      />
    </LabPage>
  );
};

export default CompilerLabPage;
