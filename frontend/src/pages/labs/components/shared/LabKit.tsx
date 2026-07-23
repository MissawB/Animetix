import React from 'react';
import { AnimatedPage } from '../../../../components/ui/AnimatedPage';

/**
 * LabKit — le système visuel commun des pages Labs (« cahier de protocoles »
 * de l'édition de nuit). Encre #0B0C10, papier #F4F1E8, deux encres d'accent :
 * shu #E8442B (voix éditoriale) et or #FDB913 (voix données). Toute page lab
 * se compose de : LabPage > LabHeader + panneaux + LabGuide en pied de page.
 */

export const INK = '#0B0C10';
export const PANEL = '#0F1016';
export const PAPER = '#F4F1E8';
export const SHU = '#E8442B';
export const GOLD = '#FDB913';
export const GRAPHITE = '#8F94A5';

/** Champ de saisie standard (input / textarea / select). */
export const LAB_INPUT =
  'w-full rounded-xl border border-[#F4F1E8]/15 bg-[#0F1016] px-5 py-3.5 text-sm font-medium text-[#F4F1E8] outline-none transition-colors placeholder:text-[#8F94A5]/60 focus:border-[#FDB913]';

/** Libellé de champ. */
export const LAB_LABEL = 'text-[10px] font-black uppercase tracking-[0.2em] text-[#8F94A5]';

/** Action principale (lance le protocole). */
export const LAB_CTA =
  'inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#E8442B] px-6 py-4 font-manga text-base font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] border-none cursor-pointer';

/** Action secondaire (pill discrète). */
export const LAB_BTN_GHOST =
  'inline-flex items-center gap-2 rounded-full border border-[#F4F1E8]/15 px-5 py-2.5 text-xs font-black uppercase tracking-widest text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] bg-transparent cursor-pointer';

/** Coquille de page : fond encre, conteneur, animation d'entrée. */
export const LabPage: React.FC<{ children: React.ReactNode; wide?: boolean }> = ({
  children,
  wide = false,
}) => (
  <div className="min-h-screen w-full bg-[#0B0C10] pt-20 text-[#F4F1E8]">
    <AnimatedPage>
      <div
        className={`relative mx-auto px-4 py-12 sm:px-6 ${wide ? 'max-w-[110rem]' : 'max-w-7xl'}`}
      >
        {children}
      </div>
    </AnimatedPage>
  </div>
);

interface LabHeaderProps {
  /** Code du protocole, ex. "PROTOCOLE · SWARM" — factuel, pas décoratif. */
  code: string;
  /** Titre ; le mot porté par `accent` est encré en vermillon. */
  title: string;
  accent?: string;
  /** Une ou deux phrases en français courant — pas de majuscules criées. */
  lede: string;
  /** Sceau du lab (kanji, cf. labHubData.glyph) ; 実験 par défaut. */
  glyph?: string;
}

/** Plaque de protocole : l'en-tête signature des pages lab. */
export const LabHeader: React.FC<LabHeaderProps> = ({
  code,
  title,
  accent,
  lede,
  glyph = '実験',
}) => (
  <header className="relative mb-14">
    <div
      className="explore-halftone pointer-events-none absolute -inset-x-6 -top-12 h-48"
      aria-hidden
    />
    <div className="relative flex items-center gap-3">
      <span className="explore-stamp -rotate-2" aria-hidden>
        {glyph}
      </span>
      <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
        {code}
      </span>
    </div>
    <h1 className="font-manga relative mt-4 text-4xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-6xl">
      {title} {accent && <span className="text-[#E8442B]">{accent}</span>}
    </h1>
    <p className="relative mt-4 max-w-2xl text-base leading-relaxed text-[#8F94A5]">{lede}</p>
    <span className="relative mt-8 block h-px bg-[#F4F1E8]/10" aria-hidden />
  </header>
);

interface LabPanelProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
  /** Coin annoté du panneau (ex. état, compteur) — voix données, en or. */
  corner?: React.ReactNode;
}

/** Panneau papier : le conteneur standard des instruments d'un lab. */
export const LabPanel: React.FC<LabPanelProps> = ({ title, children, className = '', corner }) => (
  <section
    className={`rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 sm:p-8 ${className}`}
  >
    {(title || corner) && (
      <div className="mb-6 flex items-center gap-3">
        {title && (
          <>
            <span className="h-4 w-1 flex-none bg-[#E8442B]" aria-hidden />
            <h3 className="font-manga text-sm font-black uppercase italic tracking-wide text-[#F4F1E8]">
              {title}
            </h3>
          </>
        )}
        <span className="h-px flex-1 bg-[#F4F1E8]/10" aria-hidden />
        {corner && (
          <span className="text-[10px] font-black uppercase tracking-widest text-[#FDB913]">
            {corner}
          </span>
        )}
      </div>
    )}
    {children}
  </section>
);

interface LabStatProps {
  label: string;
  value: React.ReactNode;
  /** gold = mesure clé, paper = neutre, shu = alerte/verdict. */
  tone?: 'gold' | 'paper' | 'shu';
  className?: string;
}

/** Tuile de mesure : un chiffre, son étiquette, rien d'autre. */
export const LabStat: React.FC<LabStatProps> = ({
  label,
  value,
  tone = 'paper',
  className = '',
}) => {
  const toneClass =
    tone === 'gold' ? 'text-[#FDB913]' : tone === 'shu' ? 'text-[#E8442B]' : 'text-[#F4F1E8]';
  return (
    <div className={`rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] px-6 py-5 ${className}`}>
      <p className="text-[9px] font-black uppercase tracking-[0.25em] text-[#8F94A5]">{label}</p>
      <p className={`font-manga mt-2 text-3xl font-black italic leading-none ${toneClass}`}>
        {value}
      </p>
    </div>
  );
};

interface LabEmptyProps {
  icon?: React.ReactNode;
  title: string;
  /** Dit quoi faire pour démarrer — un écran vide est une invitation à agir. */
  hint: string;
}

/** État vide : sobre, directif. */
export const LabEmpty: React.FC<LabEmptyProps> = ({ icon, title, hint }) => (
  <div className="flex h-full min-h-[320px] flex-col items-center justify-center rounded-2xl border border-dashed border-[#F4F1E8]/15 px-8 py-16 text-center">
    {icon && <div className="mb-6 text-[#8F94A5]/40">{icon}</div>}
    <h3 className="font-manga text-2xl font-black uppercase italic text-[#F4F1E8]/60">{title}</h3>
    <p className="mt-3 max-w-md text-sm leading-relaxed text-[#8F94A5]">{hint}</p>
  </div>
);

interface LabGuideStep {
  title: string;
  body: string;
}

interface LabGuideProps {
  /** Étapes du protocole, dans l'ordre réel d'utilisation du lab. */
  steps: LabGuideStep[];
  /** Note de bas de protocole (ce que le système fait des résultats). */
  note?: string;
}

/**
 * Guide & Protocole : la section de pied de page commune à tous les labs
 * (pattern SwarmLab). La numérotation est une vraie séquence : l'ordre des
 * étapes est l'ordre d'utilisation.
 */
export const LabGuide: React.FC<LabGuideProps> = ({ steps, note }) => (
  <div className="mt-24">
    <div className="mb-8 flex items-center gap-4">
      <span className="h-6 w-1.5 flex-none bg-[#E8442B]" aria-hidden />
      <h2 className="font-manga text-xl font-black uppercase italic tracking-wide text-[#F4F1E8] md:text-2xl">
        Guide &amp; Protocole
      </h2>
      <span
        className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]/60"
        aria-hidden
      >
        手順
      </span>
      <span className="h-px flex-1 bg-[#F4F1E8]/10" aria-hidden />
    </div>
    <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
      <ol className="space-y-6">
        {steps.map((step, i) => (
          <li key={step.title} className="flex gap-5">
            <span
              className="font-manga flex-none text-2xl font-black italic leading-none text-[#E8442B]"
              aria-hidden
            >
              {String(i + 1).padStart(2, '0')}
            </span>
            <div>
              <h3 className="text-xs font-black uppercase tracking-widest text-[#F4F1E8]">
                {step.title}
              </h3>
              <p className="mt-1.5 text-sm leading-relaxed text-[#8F94A5]">{step.body}</p>
            </div>
          </li>
        ))}
      </ol>
      {note && (
        <div className="flex items-center rounded-2xl border border-[#E8442B]/25 bg-[#E8442B]/[0.05] p-8">
          <p className="text-sm leading-relaxed text-[#F4F1E8]/80">{note}</p>
        </div>
      )}
    </div>
  </div>
);
