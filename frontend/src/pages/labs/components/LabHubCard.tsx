import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import type { LabEntry } from '../labHubData';

/** Grande carte papier de la grille principale (tuile d'icône, badge, CTA au
 *  survol, lien catalogue optionnel, statut). Système à deux encres : l'or ne
 *  s'exprime qu'au survol, le vermillon reste éditorial. Le lien principal est
 *  « étiré » sur toute la carte via un pseudo-élément — le lien catalogue reste
 *  un frère (jamais un descendant) pour éviter les ancres imbriquées. */
export const LabHubCard: React.FC<{ lab: LabEntry }> = ({ lab }) => {
  const { t } = useTranslation();
  return (
    <article className="group relative flex h-full flex-col justify-between rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 transition-all duration-300 hover:-translate-y-1 hover:border-[#FDB913]/60">
      <Link
        to={lab.url}
        className="block no-underline after:absolute after:inset-0 after:content-['']"
      >
        <div className="mb-8 flex items-start justify-between gap-4">
          <span className="inline-flex rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-3.5 text-[#F4F1E8] transition-colors group-hover:text-[#FDB913]">
            <lab.icon className="h-7 w-7" aria-hidden="true" />
          </span>
          <span className="text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
            {lab.badge}
          </span>
        </div>
        <h3 className="font-manga text-2xl font-black uppercase italic tracking-tight text-[#F4F1E8]">
          {lab.title}
        </h3>
        <p className="mt-3 text-sm leading-relaxed text-[#8F94A5]">{lab.desc}</p>
      </Link>

      <div className="mt-8 flex items-center justify-between gap-3 border-t border-[#F4F1E8]/10 pt-5">
        <span className="text-[10px] font-black uppercase tracking-[0.2em] text-[#FDB913] opacity-0 transition-opacity duration-300 group-hover:opacity-100">
          Ouvrir le protocole <ArrowRight className="ml-1.5 inline h-3 w-3" aria-hidden="true" />
        </span>
        <div className="flex items-center gap-3">
          {lab.catalogUrl && (
            <Link
              to={lab.catalogUrl}
              className="relative z-10 text-[9px] font-black uppercase tracking-widest text-[#FDB913] no-underline transition-colors hover:text-[#F4F1E8]"
              onClick={(e) => e.stopPropagation()}
            >
              {t('lab_hub.catalog_link', 'Catalogue →')}
            </Link>
          )}
          {lab.status && (
            <span className="text-[9px] font-bold uppercase tracking-widest text-[#8F94A5]">
              {lab.status}
            </span>
          )}
        </div>
      </div>
    </article>
  );
};
