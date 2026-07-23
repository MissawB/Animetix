import React from 'react';
import { Link } from 'react-router-dom';
import { SEAL_INKS, type SealInk } from './shared/LabKit';
import type { LabEntry } from '../labHubData';

/** Carte papier compacte partagée par les sections Forge créative et
 *  Cognition core. Même langage de sceau que la grande carte : le kanji du
 *  lab, encré à la couleur de sa famille, tient lieu d'identité ; le survol
 *  s'exprime en or. */
export const LabHubCompactCard: React.FC<{ lab: LabEntry; ink?: SealInk }> = ({
  lab,
  ink = 'shu',
}) => (
  <Link to={lab.url} className="group block h-full no-underline">
    <article className="relative h-full overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 transition-all duration-300 group-hover:-translate-y-1 group-hover:border-[#FDB913]/60">
      <span
        aria-hidden
        className="pointer-events-none absolute -bottom-5 -right-2 select-none text-[5.5rem] font-black leading-none text-[#F4F1E8]/[0.045] transition-colors duration-500 group-hover:text-[#FDB913]/[0.08]"
      >
        {lab.glyph}
      </span>
      <div className="mb-6 flex items-start justify-between gap-3">
        <span
          className="select-none text-2xl font-bold leading-none"
          style={{ color: SEAL_INKS[ink] }}
          aria-hidden
        >
          {lab.glyph}
        </span>
        <span className="text-[8px] font-black uppercase tracking-widest text-[#8F94A5]">
          {lab.badge}
        </span>
      </div>
      <h3 className="font-manga text-lg font-black uppercase italic tracking-tight text-[#F4F1E8]">
        {lab.title}
      </h3>
      <p className="mt-2 text-xs leading-relaxed text-[#8F94A5]">{lab.desc}</p>
    </article>
  </Link>
);
