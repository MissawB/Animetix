import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import type { LabEntry } from '../labHubData';

/** Large primary-grid lab card (icon tile, badge, INITIALIZE hover CTA, optional
 *  catalogue sub-link, status). */
export const LabHubCard: React.FC<{ lab: LabEntry }> = ({ lab }) => {
  const { t } = useTranslation();
  return (
    <Link to={lab.url} className="no-underline group">
      <Card
        padding="none"
        className="h-full bg-navy-950/40 border-white/5 hover:border-red-600/30 transition-all duration-500 overflow-hidden relative group shadow-2xl"
      >
        {/* Interactive BG hover effect */}
        <div
          className={`absolute inset-0 bg-gradient-to-br ${lab.bg} opacity-0 group-hover:opacity-100 transition-opacity duration-700`}
        />

        <div className="p-10 relative z-10 flex flex-col h-full justify-between">
          <div>
            <div className="flex justify-between items-start mb-10">
              <div
                className={`p-4 rounded-2xl bg-white/5 group-hover:scale-110 group-hover:rotate-6 transition-all duration-500 ${lab.color}`}
              >
                <lab.icon className="w-8 h-8" />
              </div>
              <Badge
                variant="neutral"
                className="bg-white/5 border-none text-[8px] font-black italic uppercase tracking-widest"
              >
                {lab.badge}
              </Badge>
            </div>
            <h3 className="text-3xl font-black italic manga-font uppercase mb-4 tracking-tighter group-hover:text-white transition-colors">
              {lab.title}
            </h3>
            <p className="text-xs font-bold opacity-40 uppercase leading-relaxed tracking-wider mb-10 group-hover:opacity-60 transition-opacity">
              {lab.desc}
            </p>
          </div>

          <div className="flex items-center justify-between mt-auto pt-8 border-t border-white/5">
            <span
              className={`text-[10px] font-black uppercase tracking-[0.2em] ${lab.color} opacity-0 group-hover:opacity-100 transition-all transform translate-x-[-10px] group-hover:translate-x-0 duration-500`}
            >
              INITIALIZE <ArrowRight className="inline w-3 h-3 ml-2" />
            </span>
            <div className="flex items-center gap-3">
              {lab.catalogUrl && (
                <Link
                  to={lab.catalogUrl}
                  className="text-[9px] font-black uppercase text-amber-700 dark:text-amber-400 hover:text-white transition-colors tracking-widest z-20"
                  onClick={(e) => e.stopPropagation()}
                >
                  {t('lab_hub.catalog_link', 'Catalogue →')}
                </Link>
              )}
              <span className="text-[9px] font-bold opacity-20 uppercase">{lab.status}</span>
            </div>
          </div>
        </div>
      </Card>
    </Link>
  );
};
