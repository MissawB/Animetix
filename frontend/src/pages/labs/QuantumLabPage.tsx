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
import { ThemeCombobox } from './components/ThemeCombobox';

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
  { value: 'shojo', label: 'Shōjo' },
  { value: 'josei', label: 'Josei' },
  { value: 'isekai', label: 'Isekai' },
  { value: 'mecha', label: 'Mecha' },
  { value: 'fantasy', label: 'Fantasy' },
  { value: 'dark_fantasy', label: 'Dark Fantasy' },
  { value: 'sci-fi', label: 'Science-fiction' },
  { value: 'cyberpunk', label: 'Cyberpunk' },
  { value: 'slice_of_life', label: 'Tranche de vie' },
  { value: 'comedy', label: 'Comédie' },
  { value: 'romance', label: 'Romance' },
  { value: 'drama', label: 'Drame' },
  { value: 'horror', label: 'Horreur' },
  { value: 'psychological', label: 'Psychologique' },
  { value: 'thriller', label: 'Thriller' },
  { value: 'mystery', label: 'Mystère' },
  { value: 'sports', label: 'Sport' },
  { value: 'mahou_shoujo', label: 'Magical Girl' },
  { value: 'supernatural', label: 'Surnaturel' },
  { value: 'historical', label: 'Historique' },
  { value: 'post_apocalyptic', label: 'Post-apocalyptique' },
  { value: 'ghibli', label: 'Ghibli' },
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
  const themeLabel = THEME_OPTIONS.find((o) => o.value === quantumTheme)?.label ?? quantumTheme;

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
        code="Le goût, version quantique"
        title="Cognition"
        accent="quantique"
        lede="À la manière de la physique quantique, le moteur estime la probabilité que tu aimes un thème donné. Choisis un thème et lance une mesure : tu obtiens un pourcentage de « chances d'aimer » et un verdict oui / non."
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Mesure */}
        <div className="lg:col-span-4">
          <LabPanel title="Mesure">
            <div className="space-y-6">
              <div className="space-y-2">
                <span id="theme-label" className={`${LAB_LABEL} block`}>
                  Thème à tester
                </span>
                <ThemeCombobox
                  value={quantumTheme}
                  onChange={setQuantumTheme}
                  options={THEME_OPTIONS}
                  labelId="theme-label"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="jit-level" className={LAB_LABEL}>
                  Niveau d&apos;optimisation
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
                  Souplesse du modèle
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
                  t('labs.quantum.run_measure', 'Lancer la mesure')
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
                    label={`Chances d'aimer « ${themeLabel} »`}
                    value={`${Math.round(quantumResult.probability * 100)}%`}
                    tone="gold"
                  />
                  <LabStat
                    label="Verdict"
                    value={quantumResult.outcome ? 'Plutôt oui' : 'Plutôt non'}
                    tone={quantumResult.outcome ? 'paper' : 'shu'}
                  />
                </div>

                {/* Jauge de probabilité : la même info, en un coup d'œil. */}
                <div>
                  <div className="mb-2 flex items-center justify-between text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                    <span>Peu probable</span>
                    <span>Très probable</span>
                  </div>
                  <div className="h-2.5 w-full overflow-hidden rounded-full bg-[#F4F1E8]/10">
                    <div
                      className="h-full rounded-full bg-[#FDB913] transition-all duration-500"
                      style={{ width: `${Math.round(quantumResult.probability * 100)}%` }}
                    />
                  </div>
                </div>

                <LabPanel title="Ce que ça veut dire">
                  <p className="text-sm leading-relaxed text-[#8F94A5]">
                    L&apos;IA estime{' '}
                    <span className="font-black text-[#F4F1E8]">
                      {Math.round(quantumResult.probability * 100)}%
                    </span>{' '}
                    de chances que le thème «{' '}
                    <span className="font-black uppercase text-[#F4F1E8]">{themeLabel}</span> » te
                    plaise. Plutôt que de trancher tout de suite, elle traite tes goûts comme
                    incertains — comme une pièce encore en l&apos;air — jusqu&apos;à ce que la «
                    mesure » les fixe sur un oui ou un non. Les thèmes proches peuvent aussi être
                    influencés par ce choix.
                  </p>
                </LabPanel>

                <LabPanel
                  title="Sous le capot · le détail quantique"
                  corner={
                    <span className="flex items-center gap-1.5">
                      <Activity className="h-3.5 w-3.5" aria-hidden="true" />{' '}
                      {quantumResult.state_vector.length} amplitudes
                    </span>
                  }
                >
                  <p className="mb-5 text-xs leading-relaxed text-[#8F94A5]/70">
                    Le détail mathématique de la mesure (le « vecteur d&apos;état »). Tu peux
                    l&apos;ignorer sans souci : c&apos;est la mécanique interne qui produit le
                    pourcentage ci-dessus.
                  </p>
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
              </motion.div>
            ) : (
              <LabEmpty
                icon={<Atom className="h-20 w-20" aria-hidden="true" />}
                title="En attente de mesure"
                hint="Choisis un thème et lance une mesure : ton pourcentage de « chances d'aimer » et le verdict s'afficheront ici."
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
            body: "Tu obtiens un pourcentage de « chances d'aimer » et un verdict oui / non. Les deux réglages (optimisation, souplesse) ne font qu'ajuster finement le calcul — inutile d'y toucher pour comprendre le résultat.",
          },
        ]}
        note="Simulation de préférence inspirée du formalisme quantique : elle modélise l'incertitude de nos goûts et révèle des liens inattendus entre genres. C'est une modélisation probabiliste des goûts, pas un vrai ordinateur quantique."
      />
    </LabPage>
  );
};

export default QuantumLabPage;
