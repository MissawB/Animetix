import React from 'react';
import { Link } from 'react-router-dom';
import type { LabEntry } from '../labHubData';

/** Carte papier compacte partagée par les sections Forge créative et
 *  Cognition core. Même système à deux encres que la grande carte : le
 *  survol s'exprime uniquement en or. */
export const LabHubCompactCard: React.FC<{ lab: LabEntry }> = ({ lab }) => (
  <Link to={lab.url} className="group block h-full no-underline">
    <article className="h-full rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 transition-all duration-300 group-hover:-translate-y-1 group-hover:border-[#FDB913]/60">
      <div className="mb-6 flex items-start justify-between gap-3">
        <span className="inline-flex rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-3 text-[#F4F1E8] transition-colors group-hover:text-[#FDB913]">
          <lab.icon className="h-6 w-6" aria-hidden="true" />
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
