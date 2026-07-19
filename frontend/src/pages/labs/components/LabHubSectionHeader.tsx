import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

interface LabHubSectionHeaderProps {
  /** Non-accented title prefix, e.g. "FORGE". */
  title: string;
  /** Accented (translated) title word, e.g. "CRÉATIVE". */
  accent: string;
  accentColor: string;
  dividerFrom: string;
  hubUrl: string;
  hubLabel: string;
  hubLinkColor: string;
}

/** Section header shared by the Creative and Cognition sections: title with an
 *  accented word, a gradient divider, and a "full hub" link. */
export const LabHubSectionHeader: React.FC<LabHubSectionHeaderProps> = ({
  title,
  accent,
  accentColor,
  dividerFrom,
  hubUrl,
  hubLabel,
  hubLinkColor,
}) => (
  <div className="mb-12 flex items-center justify-between gap-4">
    <h2 className="text-4xl font-black italic manga-font uppercase tracking-tighter">
      {title} <span className={accentColor}>{accent}</span>
    </h2>
    <div className={`h-px flex-1 bg-gradient-to-r ${dividerFrom} to-transparent`} />
    <Link
      to={hubUrl}
      className={`text-[10px] font-black uppercase tracking-widest ${hubLinkColor} hover:text-white transition-colors flex items-center gap-2 group whitespace-nowrap`}
    >
      {hubLabel} <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
    </Link>
  </div>
);
