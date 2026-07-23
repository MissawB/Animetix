import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { SEAL_INKS, type SealInk } from './shared/LabKit';

interface LabHubSectionHeaderProps {
  /** Préfixe du titre, ex. "FORGE". */
  title: string;
  /** Mot accentué (traduit) du titre, ex. "CRÉATIVE" — encré dans l'encre de la famille. */
  accent: string;
  hubUrl: string;
  hubLabel: string;
  /** Encre de la famille de labs (shu par défaut). */
  ink?: SealInk;
}

/** En-tête de section des grilles du hub : même grammaire que le titre de
 *  LabPanel (barre verticale + filet), encré à la couleur de la famille,
 *  avec le lien vers le hub complet en voix or au survol. */
export const LabHubSectionHeader: React.FC<LabHubSectionHeaderProps> = ({
  title,
  accent,
  hubUrl,
  hubLabel,
  ink = 'shu',
}) => {
  const inkColor = SEAL_INKS[ink];
  return (
    <div className="mb-10 flex items-center gap-4">
      <span className="h-6 w-1.5 flex-none" style={{ backgroundColor: inkColor }} aria-hidden />
      <h2 className="font-manga text-xl font-black uppercase italic tracking-wide text-[#F4F1E8] md:text-2xl">
        {title} <span style={{ color: inkColor }}>{accent}</span>
      </h2>
      <span className="h-px flex-1 bg-[#F4F1E8]/10" aria-hidden />
      <Link
        to={hubUrl}
        className="group flex items-center gap-2 whitespace-nowrap text-[10px] font-black uppercase tracking-widest text-[#8F94A5] no-underline transition-colors hover:text-[#F4F1E8]"
      >
        {hubLabel}
        <ArrowRight
          className="h-3 w-3 transition-transform group-hover:translate-x-1"
          aria-hidden="true"
        />
      </Link>
    </div>
  );
};
