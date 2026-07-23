import React from 'react';
import { useTranslation } from 'react-i18next';
import { Heart, History } from 'lucide-react';
import { CardSkeleton } from '../../../components/ui/Skeleton';
import { VsBattleArenaEntry } from '../../../types';

interface Props {
  feed: VsBattleArenaEntry[] | undefined;
  isLoading: boolean;
  onLike: (id: number) => void;
}

export const VsArenaFeed: React.FC<Props> = ({ feed, isLoading, onLike }) => {
  const { t } = useTranslation();
  return (
    <section>
      <div className="mb-6 flex items-center gap-4">
        <span className="h-5 w-1 flex-none bg-[#E8442B]" aria-hidden />
        <h3 className="font-manga text-sm font-black uppercase italic tracking-wide text-[#F4F1E8] flex items-center gap-2">
          <History className="w-4 h-4 text-[#8F94A5]" aria-hidden="true" />{' '}
          {t('games.vs_battle.public_arena', 'Arène Publique')}
        </h3>
        <span className="rounded-sm border border-[#E8442B]/40 px-2 py-0.5 text-[8px] font-black uppercase tracking-widest text-[#E8442B]">
          LIVE FEED
        </span>
        <span className="h-px flex-1 bg-[#F4F1E8]/10" aria-hidden />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading
          ? [...Array(3)].map((_, i) => <CardSkeleton key={i} />)
          : feed?.map((battle) => (
              <article
                key={battle.id}
                className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-5 transition-colors hover:border-[#F4F1E8]/25"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="text-[10px] font-black uppercase text-[#8F94A5] italic">
                    {new Date(battle.created_at).toLocaleDateString()}
                  </div>
                  <button
                    type="button"
                    onClick={() => onLike(battle.id)}
                    className={`flex items-center gap-1 text-[10px] font-black transition-colors ${battle.is_liked ? 'text-[#E8442B]' : 'text-[#8F94A5] hover:text-[#E8442B]'}`}
                  >
                    <Heart className={`w-3 h-3 ${battle.is_liked ? 'fill-current' : ''}`} />{' '}
                    {battle.likes_count}
                  </button>
                </div>
                <div className="flex items-center justify-between gap-4 mb-4">
                  <div className="flex-1 text-center">
                    <p className="text-[10px] font-black italic manga-font truncate text-[#F4F1E8]">
                      {battle.char_a_name}
                    </p>
                    <p className="text-[8px] text-[#8F94A5] uppercase truncate">
                      {battle.char_a_franchise}
                    </p>
                  </div>
                  <div className="text-[#E8442B] font-black italic text-xs">VS</div>
                  <div className="flex-1 text-center">
                    <p className="text-[10px] font-black italic manga-font truncate text-[#F4F1E8]">
                      {battle.char_b_name}
                    </p>
                    <p className="text-[8px] text-[#8F94A5] uppercase truncate">
                      {battle.char_b_franchise}
                    </p>
                  </div>
                </div>
                <div className="bg-[#0B0C10] p-3 rounded-xl border border-[#F4F1E8]/10">
                  <p className="text-[9px] font-bold text-[#8F94A5] uppercase leading-tight line-clamp-2 italic">
                    Winner: <span className="text-[#FDB913]">{battle.winner}</span> — "
                    {battle.verdict_summary}"
                  </p>
                </div>
              </article>
            ))}
      </div>
    </section>
  );
};
