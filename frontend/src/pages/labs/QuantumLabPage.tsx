import React, { useState } from 'react';
import { Atom, Loader2, Activity } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
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

interface QuantumResult {
  probability: number;
  outcome: boolean;
  state_vector: string[];
}

interface QuantumMutationBody {
  action: 'quantum';
  theme: string;
  jitLevel: string;
  plasticity: string;
}

const THEME_OPTIONS = [
  { value: 'shonen', label: 'Shōnen' },
  { value: 'seinen', label: 'Seinen' },
  { value: 'ghibli', label: 'Ghibli' },
  { value: 'comedy', label: 'Comédie' },
  { value: 'cyberpunk', label: 'Cyberpunk' },
];

const JIT_OPTIONS = [
  { value: 'none', label: 'Aucun' },
  { value: 'basic', label: 'Basique' },
  { value: 'aggressive', label: 'Agressif' },
];

const PLASTICITY_OPTIONS = [
  { value: 'low', label: 'Faible' },
  { value: 'medium', label: 'Moyenne' },
  { value: 'high', label: 'Forte' },
  { value: 'dynamic', label: 'Dynamique' },
];

const QuantumLabPage: React.FC = () => {
  const { t } = useTranslation();
  const [quantumTheme, setQuantumTheme] = useState('shonen');
  const [jitLevel, setJitLevel] = useState('basic');
  const [plasticity, setPlasticity] = useState('medium');
  const [quantumResult, setQuantumResult] = useState<QuantumResult | null>(null);

  const quantumMutation = useMutation({
    mutationFn: (body: QuantumMutationBody) =>
      apiClient('/api/v1/singularity-lab/', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: (data: QuantumResult) => setQuantumResult(data),
  });

  return (
    <LabPage>
      <LabHeader
        code="Protocole · Quantum"
        title="Cognition"
        accent="quantique"
        lede="Le moteur modélise tes préférences comme des états en superposition. Choisis un thème, lance une mesure : la fonction d'onde s'effondre sur un verdict, positif ou négatif."
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Mesure */}
        <div className="lg:col-span-4">
          <LabPanel title="Mesure">
            <div className="space-y-6">
              <div className="space-y-2">
                <label htmlFor="theme" className={LAB_LABEL}>
                  Thème observé
                </label>
                <select
                  id="theme"
                  value={quantumTheme}
                  onChange={(e) => setQuantumTheme(e.target.value)}
                  className={LAB_INPUT}
                >
                  {THEME_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label htmlFor="jit-level" className={LAB_LABEL}>
                  JIT Level
                </label>
                <select
                  id="jit-level"
                  value={jitLevel}
                  onChange={(e) => setJitLevel(e.target.value)}
                  className={LAB_INPUT}
                >
                  {JIT_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label htmlFor="plasticity" className={LAB_LABEL}>
                  Plasticity
                </label>
                <select
                  id="plasticity"
                  value={plasticity}
                  onChange={(e) => setPlasticity(e.target.value)}
                  className={LAB_INPUT}
                >
                  {PLASTICITY_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <button
                type="button"
                onClick={() =>
                  quantumMutation.mutate({
                    action: 'quantum',
                    theme: quantumTheme,
                    jitLevel,
                    plasticity,
                  })
                }
                disabled={quantumMutation.isPending}
                className={LAB_CTA}
              >
                {quantumMutation.isPending ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  t('labs.quantum.run_measure', 'EFFECTUER MESURE')
                )}
              </button>
            </div>
          </LabPanel>
        </div>

        {/* Résultats */}
        <div className="lg:col-span-8">
          <AnimatePresence mode="wait">
            {quantumResult ? (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -16 }}
                className="space-y-10"
              >
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                  <LabStat
                    label="Probabilité mesurée"
                    value={`${Math.round(quantumResult.probability * 100)}%`}
                    tone="gold"
                  />
                  <LabStat
                    label="Effondrement"
                    value={quantumResult.outcome ? 'Verdict positif' : 'Verdict négatif'}
                    tone={quantumResult.outcome ? 'paper' : 'shu'}
                  />
                </div>

                <LabPanel
                  title="Vecteur d'état"
                  corner={
                    <span className="flex items-center gap-1.5">
                      <Activity className="h-3.5 w-3.5" aria-hidden="true" />{' '}
                      {quantumResult.state_vector.length} amplitudes
                    </span>
                  }
                >
                  <div className="grid grid-cols-1 gap-4">
                    {quantumResult.state_vector.map((val: string, i: number) => (
                      <div
                        key={i}
                        className="flex items-center justify-between rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4"
                      >
                        <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                          Amplitude {i}
                        </span>
                        <code className="max-w-[220px] truncate font-mono text-sm text-[#FDB913]">
                          {val}
                        </code>
                      </div>
                    ))}
                  </div>
                </LabPanel>

                <LabPanel title="Interprétation de Born">
                  <p className="text-sm leading-relaxed text-[#8F94A5]">
                    La mesure a forcé le système à sortir de sa superposition pour valider (ou
                    rejeter) l'observable «{' '}
                    <span className="font-black uppercase text-[#F4F1E8]">{quantumTheme}</span> ».
                    Les thèmes intriqués restent influencés par cet effondrement.
                  </p>
                </LabPanel>
              </motion.div>
            ) : (
              <LabEmpty
                icon={<Atom className="h-20 w-20" aria-hidden="true" />}
                title="Système en superposition"
                hint="Choisis un thème et lance une mesure : le verdict et le vecteur d'état s'afficheront ici."
              />
            )}
          </AnimatePresence>
        </div>
      </div>

      <LabGuide
        steps={[
          {
            title: 'La superposition',
            body: "Pour le moteur, tes goûts ne sont pas des cases figées : tu aimes potentiellement tout à la fois, jusqu'à ce qu'une décision soit prise.",
          },
          {
            title: "L'effondrement",
            body: "Quand tu sélectionnes un thème et lances une mesure, l'IA force tes probabilités à se fixer — c'est l'effondrement de la fonction d'onde de tes préférences.",
          },
          {
            title: 'La lecture',
            body: "Le backend calcule une probabilité pour le thème choisi, en déduit un verdict binaire et renvoie le vecteur d'amplitudes affiché. Les réglages JIT et Plasticity modulent ce calcul.",
          },
        ]}
        note="Simulation de préférence inspirée du formalisme quantique : elle modélise l'incertitude humaine et révèle des liens invisibles entre genres sans rapport apparent. C'est une modélisation probabiliste des goûts, pas un ordinateur quantique."
      />
    </LabPage>
  );
};

export default QuantumLabPage;
