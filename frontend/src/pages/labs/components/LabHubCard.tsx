import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import type { LabEntry } from '../labHubData';

/** Grande carte papier de la grille principale. Chaque lab porte son sceau :
 *  un hanko kanji vermillon en tête et le même glyphe en filigrane géant —
 *  c'est lui qui différencie les cartes, pas une couleur d'accent. Le survol
 *  s'exprime en or. Le lien principal est « étiré » sur toute la carte via un
 *  pseudo-élément — le lien catalogue reste un frère (jamais un descendant)
 *  pour éviter les ancres imbriquées. `featured` : la « une » de la grille,
 *  sur deux colonnes. */
export const LabHubCard: React.FC<{ lab: LabEntry; featured?: boolean }> = ({
  lab,
  featured = false,
}) => {
  const { t } = useTranslation();
  return (
    <article
      className={`group relative flex h-full flex-col justify-between overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 transition-all duration-300 hover:-translate-y-1 hover:border-[#FDB913]/60 ${
        featured ? 'lg:col-span-2' : ''
      }`}
    >
      <span
        aria-hidden
        className={`pointer-events-none absolute -bottom-8 -right-4 select-none font-black leading-none text-[#F4F1E8]/[0.045] transition-colors duration-500 group-hover:text-[#FDB913]/[0.08] ${
          featured ? 'text-[13rem]' : 'text-[8.5rem]'
        }`}
      >
        {lab.glyph}
      </span>

      <Link
        to={lab.url}
        className="block no-underline after:absolute after:inset-0 after:content-['']"
      >
        <div className="mb-8 flex items-start justify-between gap-4">
          <span
            className={`explore-stamp -rotate-2 select-none font-bold not-italic ${
              featured ? 'text-2xl' : 'text-lg'
            }`}
            aria-hidden
          >
            {lab.glyph}
          </span>
          <span className="text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
            {lab.badge}
          </span>
        </div>
        <h3
          className={`font-manga font-black uppercase italic tracking-tight text-[#F4F1E8] ${
            featured ? 'text-3xl md:text-4xl' : 'text-2xl'
          }`}
        >
          {lab.title}
        </h3>
        <p className={`mt-3 text-sm leading-relaxed text-[#8F94A5] ${featured ? 'max-w-xl' : ''}`}>
          {lab.desc}
        </p>
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
