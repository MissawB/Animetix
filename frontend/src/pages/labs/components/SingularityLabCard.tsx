import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { SEAL_INKS, type SealInk } from './shared/LabKit';
import type { LabEntry } from '../labHubData';

/** Carte « vitrée » d'un protocole, posée sur le vide de la scène Singularity :
 *  fond translucide + flou, sceau kanji encré, filigrane géant, point de statut
 *  vivant, lueur or au survol. Le lien principal est étiré sur toute la carte ;
 *  le lien catalogue reste un frère (jamais imbriqué). `featured` = « une ». */
export const SingularityLabCard: React.FC<{
  lab: LabEntry;
  index: number;
  featured?: boolean;
  ink?: SealInk;
}> = ({ lab, index, featured = false, ink = 'shu' }) => {
  const { t } = useTranslation();
  const inkColor = SEAL_INKS[ink];
  const operational = /oper/i.test(lab.status ?? '');

  return (
    <article
      className={`group relative flex h-full flex-col justify-between overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#F4F1E8]/[0.02] p-7 backdrop-blur-sm transition-all duration-300 hover:-translate-y-1.5 hover:border-[#FDB913]/60 hover:bg-[#F4F1E8]/[0.04] hover:shadow-[0_24px_70px_-24px_rgba(253,185,19,0.25)] ${
        featured ? 'lg:col-span-2' : ''
      }`}
    >
      {/* Filet supérieur qui s'allume au survol. */}
      <span
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#FDB913]/0 to-transparent transition-all duration-500 group-hover:via-[#FDB913]/60"
      />
      {/* Sceau kanji géant en filigrane. */}
      <span
        aria-hidden
        className={`pointer-events-none absolute -bottom-6 -right-3 select-none font-black leading-none text-[#F4F1E8]/[0.05] transition-colors duration-500 group-hover:text-[#FDB913]/[0.09] ${
          featured ? 'text-[12rem]' : 'text-[7.5rem]'
        }`}
      >
        {lab.glyph}
      </span>

      <Link
        to={lab.url}
        className="block no-underline after:absolute after:inset-0 after:content-['']"
      >
        <div className="mb-7 flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <span
              className={`-rotate-2 inline-block select-none rounded-[2px] border-2 px-1.5 py-0.5 font-bold not-italic leading-none ${
                featured ? 'text-2xl' : 'text-lg'
              }`}
              style={{ borderColor: inkColor, color: inkColor }}
              aria-hidden
            >
              {lab.glyph}
            </span>
            <span className="font-mono text-[10px] font-black tracking-widest text-[#8F94A5]">
              {String(index + 1).padStart(2, '0')}
            </span>
          </div>
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

      <div className="mt-7 flex items-center justify-between gap-3 border-t border-[#F4F1E8]/10 pt-5">
        <span className="text-[10px] font-black uppercase tracking-[0.2em] text-[#FDB913] opacity-0 transition-opacity duration-300 group-hover:opacity-100">
          Ouvrir <ArrowRight className="ml-1 inline h-3 w-3" aria-hidden="true" />
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
            <span className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-widest text-[#8F94A5]">
              <span
                className={`h-1.5 w-1.5 rounded-full motion-safe:animate-pulse ${
                  operational ? 'bg-[#34D399]' : 'bg-[#FDB913]'
                }`}
                aria-hidden
              />
              {lab.status}
            </span>
          )}
        </div>
      </div>
    </article>
  );
};
