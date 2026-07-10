import React, { ReactNode } from 'react';
import { AnimatedPage } from './AnimatedPage';

type Accent = 'yellow' | 'red' | 'orange';

// Déclinaisons par page d'erreur : 404 = jaune (univers Ghost), 403 = orange
// (interdit), 500 = rouge (panne). Classes complètes (pas de concaténation :
// le JIT Tailwind ne compilerait pas des classes construites dynamiquement).
const ACCENTS: Record<Accent, { glow: string; box: string; accentText: string }> = {
  yellow: {
    glow: 'bg-yellow-400/10',
    box: 'from-yellow-400 to-orange-500',
    accentText: 'text-yellow-700 dark:text-yellow-400',
  },
  orange: {
    glow: 'bg-orange-500/10',
    box: 'from-orange-400 to-red-500',
    accentText: 'text-orange-600 dark:text-orange-400',
  },
  red: {
    glow: 'bg-red-500/10',
    box: 'from-red-500 to-rose-600',
    accentText: 'text-red-600 dark:text-red-500',
  },
};

interface ErrorPageShellProps {
  code: string;
  icon: ReactNode;
  title: string;
  titleAccent: string;
  description: string;
  accent?: Accent;
  actions?: ReactNode;
}

/**
 * Gabarit commun des pages d'erreur (404, 403, 500…) : icône lumineuse,
 * code géant, titre bicolore et actions — l'univers visuel de la page
 * « Dimension inconnue ».
 */
export const ErrorPageShell: React.FC<ErrorPageShellProps> = ({
  code,
  icon,
  title,
  titleAccent,
  description,
  accent = 'yellow',
  actions,
}) => {
  const colors = ACCENTS[accent];

  return (
    <AnimatedPage>
      <div className="min-h-[70vh] flex items-center justify-center px-6">
        <div className="text-center space-y-8 max-w-xl">
          <div className="relative inline-block">
            <div
              className={`absolute -inset-8 ${colors.glow} rounded-full blur-3xl animate-pulse`}
            />
            <div
              className={`relative w-32 h-32 bg-gradient-to-br ${colors.box} rounded-[2rem] flex items-center justify-center rotate-12 shadow-2xl mx-auto`}
            >
              {icon}
            </div>
          </div>

          <div>
            <h1 className="text-[10rem] leading-none font-black italic manga-font tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white/20 to-white/5 select-none">
              {code}
            </h1>
          </div>

          <div className="space-y-3">
            <h2 className="text-3xl font-black italic manga-font uppercase tracking-tight">
              {title} <span className={`${colors.accentText} text-glow`}>{titleAccent}</span>
            </h2>
            <p className="text-sm font-bold text-gray-600 dark:text-gray-400 uppercase tracking-[0.2em] max-w-md mx-auto">
              {description}
            </p>
          </div>

          {actions && (
            <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">{actions}</div>
          )}
        </div>
      </div>
    </AnimatedPage>
  );
};
