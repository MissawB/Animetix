import React from 'react';
import { User, Star, Volume2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
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
      <Card
        padding="md"
        className={`group border-none relative overflow-hidden transition-all hover:ring-2 hover:ring-blue-500/50 ${isSelected ? 'ring-2 ring-blue-500' : ''}`}
      >
        <div className="flex justify-between items-start mb-3">
          <div className="p-2 rounded-lg bg-blue-500/10 text-blue-500 group-hover:bg-blue-500 group-hover:text-white transition-colors">
            <User className="w-4 h-4" />
          </div>
          <div className="flex gap-2">
            <Badge
              variant="neutral"
              className="text-[7px] font-black uppercase tracking-tighter opacity-50 bg-black/40"
            >
              {s.language === 'japanese' ? '🇯🇵 JP' : s.language === 'french' ? '🇫🇷 FR' : '🌐'}
            </Badge>
            <Badge
              variant="neutral"
              className="text-[7px] font-black uppercase tracking-tighter opacity-40"
            >
              {s.origin === 'dataset' ? 'Dataset' : 'YouTube'}
            </Badge>
          </div>
        </div>

        <h4 className="text-lg font-black uppercase tracking-tight mb-0.5 flex items-center justify-between">
          {s.name}
          <button
            onClick={onPlaySample}
            className="p-1.5 rounded-lg bg-white/5 text-gray-400 hover:text-white hover:bg-blue-600 transition-colors"
            title={t('labs.audio.seiyuu_listen_aria', "Écouter l'échantillon")}
          >
            <Volume2 className="w-3.5 h-3.5" />
          </button>
        </h4>
        <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest mb-4 leading-relaxed line-clamp-1">
          {s.roles || 'Doubleur'}
        </p>

        <div className="space-y-3">
          <div className="space-y-1">
            <span className="text-[8px] font-black uppercase text-blue-500 tracking-widest flex items-center gap-1">
              <Star className="w-2.5 h-2.5 fill-current" />{' '}
              {t('labs.audio.seiyuu_roles_title', 'Rôles')}
            </span>
            <p className="text-[10px] font-medium leading-relaxed italic opacity-80 line-clamp-2">
              {s.roles || t('labs.audio.seiyuu_no_roles', 'Aucun rôle répertorié')}
            </p>
          </div>

          <div className="pt-3 border-t border-black/5 dark:border-white/5 space-y-1">
            <p className="text-[9px] leading-relaxed opacity-60 line-clamp-2">
              {s.definition || t('labs.audio.seiyuu_definition_fallback', 'Talent vocal certifié.')}
            </p>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <div className="flex-1 h-1 bg-blue-500/20 rounded-full overflow-hidden">
            <div className="h-full bg-blue-500 w-full animate-pulse" />
          </div>
          <span className="text-[7px] font-black uppercase text-blue-500">
            {t('labs.audio.seiyuu_click_drag_note', 'Cliquer ou Glisser pour utiliser')}
          </span>
        </div>
      </Card>
    </div>
  );
};
