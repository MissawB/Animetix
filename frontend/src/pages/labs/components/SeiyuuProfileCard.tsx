import React from 'react';
import { User, Star, Volume2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { VoiceProfile } from '../../../types';

/** A draggable/clickable seiyuu (voice actor) profile card in the Audio Lab
 *  sidebar. All behaviour is delegated to the parent via callbacks so the
 *  page keeps ownership of the selection / audio-playback state. */
export const SeiyuuProfileCard: React.FC<{
  seiyuu: VoiceProfile;
  isSelected: boolean;
  onSelect: () => void;
  onDragStart: (e: React.DragEvent) => void;
  onPlaySample: (e: React.MouseEvent) => void;
}> = ({ seiyuu: s, isSelected, onSelect, onDragStart, onPlaySample }) => {
  const { t } = useTranslation();
  return (
    <div
      draggable
      role="button"
      tabIndex={0}
      aria-label={t('labs.audio.seiyuu_roles_aria', {
        name: s.name,
        defaultValue: 'Sélectionner ou glisser le profil vocal {{name}}',
      })}
      onDragStart={onDragStart}
      className="cursor-grab active:cursor-grabbing"
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect();
        }
      }}
    >
      <div
        className={`group rounded-2xl border bg-[#0F1016] p-4 transition-colors ${
          isSelected ? 'border-[#FDB913]' : 'border-[#F4F1E8]/10 hover:border-[#FDB913]/40'
        }`}
      >
        <div className="mb-3 flex items-start justify-between">
          <div className="rounded-lg bg-[#FDB913]/10 p-2 text-[#FDB913]">
            <User className="h-4 w-4" aria-hidden="true" />
          </div>
          <div className="flex gap-2">
            <span className="text-[8px] font-black uppercase tracking-widest text-[#8F94A5]">
              {s.language === 'japanese' ? '🇯🇵 JP' : s.language === 'french' ? '🇫🇷 FR' : '🌐'}
            </span>
            <span className="text-[8px] font-black uppercase tracking-widest text-[#8F94A5]">
              {s.origin === 'dataset' ? 'Dataset' : 'YouTube'}
            </span>
          </div>
        </div>

        <h4 className="mb-0.5 flex items-center justify-between text-lg font-black uppercase tracking-tight text-[#F4F1E8]">
          {s.name}
          <button
            type="button"
            onClick={onPlaySample}
            className="cursor-pointer rounded-lg border-none bg-[#F4F1E8]/5 p-1.5 text-[#8F94A5] transition-colors hover:bg-[#E8442B] hover:text-[#F4F1E8]"
            title={t('labs.audio.seiyuu_listen_aria', "Écouter l'échantillon")}
          >
            <Volume2 className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
        </h4>
        <p className="mb-4 line-clamp-1 text-[9px] font-bold uppercase tracking-widest leading-relaxed text-[#8F94A5]">
          {s.roles || 'Doubleur'}
        </p>

        <div className="space-y-3">
          <div className="space-y-1">
            <span className="flex items-center gap-1 text-[8px] font-black uppercase tracking-widest text-[#FDB913]">
              <Star className="h-2.5 w-2.5 fill-current" aria-hidden="true" />{' '}
              {t('labs.audio.seiyuu_roles_title', 'Rôles')}
            </span>
            <p className="line-clamp-2 text-[10px] font-medium italic leading-relaxed text-[#F4F1E8]/80">
              {s.roles || t('labs.audio.seiyuu_no_roles', 'Aucun rôle répertorié')}
            </p>
          </div>

          <div className="space-y-1 border-t border-[#F4F1E8]/10 pt-3">
            <p className="line-clamp-2 text-[9px] leading-relaxed text-[#8F94A5]">
              {s.definition || t('labs.audio.seiyuu_definition_fallback', 'Talent vocal certifié.')}
            </p>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
          <div className="h-1 flex-1 overflow-hidden rounded-full bg-[#FDB913]/20">
            <div className="h-full w-full bg-[#FDB913]" />
          </div>
          <span className="text-[7px] font-black uppercase text-[#FDB913]">
            {t('labs.audio.seiyuu_click_drag_note', 'Cliquer ou Glisser pour utiliser')}
          </span>
        </div>
      </div>
    </div>
  );
};
