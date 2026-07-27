import React, { useState } from 'react';
import { Users, Network, Scale, FileText, type LucideIcon } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Modal } from '../../../components/ui/Modal';

/* ------------------------------------------------------------------ */
/* « Le principe » : un inspecteur explorable du pipeline d'un MoE.     */
/* Rail de gauche = le chemin du signal (4 stations numérotées reliées) */
/* ; panneau de droite = le détail de l'étape choisie, avec un chiffre  */
/* fantôme en filigrane (rappel du sceau kanji de la page).             */
/* ------------------------------------------------------------------ */
interface MoeStation {
  icon: LucideIcon;
  name: string;
  /** Rôle de l'étape dans le vocabulaire ML — c'est une information, pas un ornement. */
  role: string;
  detail: string;
  /** Formule affichée en évidence (uniquement l'agrégation). */
  formula?: string;
}

const FLOW_STATIONS: MoeStation[] = [
  {
    icon: FileText,
    name: 'Le fait',
    role: 'Entrée',
    detail:
      "C'est l'entrée du système — l'équivalent d'un « token » ou d'une requête. À ce stade, rien n'est encore jugé : le fait est simplement présenté à l'essaim. Sa formulation compte : un énoncé clair et vérifiable se route et s'évalue mieux qu'une phrase vague.",
  },
  {
    icon: Network,
    name: 'Le routeur',
    role: 'Gating',
    detail:
      "C'est le cœur d'un Mixture-of-Experts. Un petit réseau appelé « gating » lit l'entrée et attribue à chaque expert un poids de pertinence. Dans les grands MoE (Mixtral, GPT-4…), il n'active que les k meilleurs experts (« top-k ») : le modèle peut être gigantesque tout en restant rapide, car seuls quelques experts calculent. Ici, le routeur pondère nos sept experts selon le sujet — un fait sonore réveille l'Expert Sonore, un fait de lore l'Expert Lore.",
  },
  {
    icon: Users,
    name: 'Les experts',
    role: 'Spécialistes',
    detail:
      "Chaque expert est spécialisé dans un angle : visuel, sonore, lore, combat, émotion, histoire de production, plus un « avocat du diable » volontairement sceptique. Ils évaluent la véracité du fait indépendamment les uns des autres. Un même fait ne se juge pas de la même façon selon l'angle : c'est cette diversité qui rend l'essaim robuste aux erreurs individuelles.",
  },
  {
    icon: Scale,
    name: 'Somme pondérée',
    role: 'Agrégation',
    detail:
      'On ne fait pas une moyenne aveugle : chaque vote est multiplié par le poids que le routeur lui a donné, puis divisé par la somme des poids. Un expert hors sujet (poids proche de 0) ne peut donc ni sauver ni couler un fait. Au-delà de 70 % de consensus, le fait est scellé dans le Knowledge Graph.',
    formula: 'Σ(vote × poids) ⁄ Σ(poids)',
  },
];

export const MoePrincipleModal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({
  isOpen,
  onClose,
}) => {
  const [selected, setSelected] = useState(1); // le routeur, cœur du MoE, par défaut
  const active = FLOW_STATIONS[selected];
  const ActiveIcon = active.icon;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      size="xl"
      title={<span className="font-manga uppercase italic tracking-wide">Mixture-of-Experts</span>}
      ariaDescription="Explication du fonctionnement d'un Mixture-of-Experts en quatre étapes cliquables."
      contentClassName="!bg-[#0F1016] !border-[#F4F1E8]/10"
    >
      <p className="mb-8 max-w-2xl text-sm leading-relaxed text-[#8F94A5] sm:text-base">
        Un modèle unique doit tout savoir, et le fait mal. Un{' '}
        <span className="font-bold text-[#F4F1E8]">Mixture-of-Experts</span> délègue à des{' '}
        <span className="font-bold text-[#F4F1E8]">spécialistes</span> — et un{' '}
        <span className="font-bold text-[#5D7FD3]">routeur</span> décide, pour chaque question, qui
        mérite qu'on l'écoute.
      </p>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-[minmax(0,1fr)_minmax(0,1.45fr)] md:gap-8">
        {/* Rail : le chemin du signal */}
        <div>
          <p className="mb-4 text-[10px] font-black uppercase tracking-[0.3em] text-[#8F94A5]">
            Le pipeline
          </p>
          <div className="relative">
            {/* ligne verticale reliant les stations */}
            <span
              className="absolute bottom-6 left-[18px] top-6 w-px -translate-x-1/2 bg-[#F4F1E8]/10"
              aria-hidden="true"
            />
            <div className="space-y-1.5">
              {FLOW_STATIONS.map((station, i) => {
                const Icon = station.icon;
                const isSel = i === selected;
                return (
                  <button
                    key={station.name}
                    type="button"
                    onClick={() => setSelected(i)}
                    aria-pressed={isSel}
                    className={`group relative flex w-full cursor-pointer items-center gap-3 rounded-xl py-2 pl-0 pr-3 text-left transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#5D7FD3] ${
                      isSel ? 'bg-[#5D7FD3]/[0.08]' : 'hover:bg-[#F4F1E8]/[0.03]'
                    }`}
                  >
                    <span
                      className={`relative z-10 flex h-9 w-9 flex-none items-center justify-center rounded-lg border font-manga text-sm font-black italic transition-colors ${
                        isSel
                          ? 'border-[#5D7FD3] bg-[#5D7FD3]/15 text-[#5D7FD3]'
                          : 'border-[#F4F1E8]/15 bg-[#0F1016] text-[#8F94A5] group-hover:border-[#5D7FD3]/40'
                      }`}
                    >
                      {String(i + 1).padStart(2, '0')}
                    </span>
                    <Icon
                      className={`h-4 w-4 flex-none transition-colors ${
                        isSel ? 'text-[#5D7FD3]' : 'text-[#8F94A5]'
                      }`}
                      aria-hidden="true"
                    />
                    <span
                      className={`font-manga text-sm font-black uppercase italic tracking-wide transition-colors ${
                        isSel ? 'text-[#F4F1E8]' : 'text-[#F4F1E8]/70 group-hover:text-[#F4F1E8]'
                      }`}
                    >
                      {station.name}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Panneau de détail */}
        <div
          className="relative min-h-[240px] overflow-hidden rounded-2xl border border-[#5D7FD3]/20 bg-[#5D7FD3]/[0.04] p-6 sm:p-8"
          aria-live="polite"
        >
          {/* Chiffre fantôme — le sceau de l'étape */}
          <span
            key={`ghost-${selected}`}
            className="font-manga pointer-events-none absolute -right-4 -top-8 select-none text-[9rem] font-black italic leading-none text-[#5D7FD3]/[0.07]"
            aria-hidden="true"
          >
            {String(selected + 1).padStart(2, '0')}
          </span>

          <AnimatePresence mode="wait">
            <motion.div
              key={selected}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.22 }}
              className="relative"
            >
              <div className="mb-2 flex items-center gap-2">
                <ActiveIcon className="h-4 w-4 text-[#5D7FD3]" aria-hidden="true" />
                <span className="text-[10px] font-black uppercase tracking-[0.25em] text-[#E8442B]">
                  {active.role}
                </span>
              </div>
              <h3 className="font-manga mb-4 text-2xl font-black uppercase italic leading-none text-[#F4F1E8]">
                {active.name}
              </h3>
              <p className="max-w-prose text-sm leading-relaxed text-[#F4F1E8]/75">
                {active.detail}
              </p>
              {active.formula && (
                <div className="mt-5 inline-flex items-center gap-2 rounded-lg border border-[#FDB913]/30 bg-[#FDB913]/[0.06] px-3.5 py-2 font-mono text-sm text-[#FDB913]">
                  {active.formula}
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </Modal>
  );
};
