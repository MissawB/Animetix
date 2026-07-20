import React from 'react';
import { useTranslation } from 'react-i18next';
import { Heart, History } from 'lucide-react';
import { Card } from '../../../components/ui/Card';
import { CardSkeleton } from '../../../components/ui/Skeleton';
import { Badge } from '../../../components/ui/Badge';
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
      <div className="flex items-center justify-center gap-3 mb-6">
        <h3 className="text-xs font-black uppercase opacity-40 tracking-widest flex items-center gap-2">
          <History className="w-4 h-4" /> {t('games.vs_battle.public_arena', 'Arène Publique')}
        </h3>
        <Badge
          variant="neutral"
          className="bg-red-500/10 text-red-500 border-red-500/20 text-[8px]"
        >
          LIVE FEED
        </Badge>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading
          ? [...Array(3)].map((_, i) => <CardSkeleton key={i} />)
          : feed?.map((battle) => (
              <Card
                key={battle.id}
                padding="md"
                className="bg-navy-900/50 border-white/5 hover:border-white/10 transition-all group"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="text-[10px] font-black uppercase opacity-30 italic">
                    {new Date(battle.created_at).toLocaleDateString()}
                  </div>
                  <button
                    type="button"
                    onClick={() => onLike(battle.id)}
                    className={`flex items-center gap-1 text-[10px] font-black transition-colors ${battle.is_liked ? 'text-red-500' : 'text-white/20 hover:text-red-400'}`}
                  >
                    <Heart className={`w-3 h-3 ${battle.is_liked ? 'fill-current' : ''}`} />{' '}
                    {battle.likes_count}
                  </button>
                </div>
                <div className="flex items-center justify-between gap-4 mb-4">
                  <div className="flex-1 text-center">
                    <p className="text-[10px] font-black italic manga-font truncate text-white">
                      {battle.char_a_name}
                    </p>
                    <p className="text-[8px] opacity-30 uppercase truncate">
                      {battle.char_a_franchise}
                    </p>
                  </div>
                  <div className="text-red-500 font-black italic text-xs">VS</div>
                  <div className="flex-1 text-center">
                    <p className="text-[10px] font-black italic manga-font truncate text-white">
                      {battle.char_b_name}
                    </p>
                    <p className="text-[8px] opacity-30 uppercase truncate">
                      {battle.char_b_franchise}
                    </p>
                  </div>
                </div>
                <div className="bg-black/40 p-3 rounded-xl border border-white/5">
                  <p className="text-[9px] font-bold text-white/50 uppercase leading-tight line-clamp-2 italic">
                    Winner: <span className="text-red-500">{battle.winner}</span> — "
                    {battle.verdict_summary}"
                  </p>
                </div>
              </Card>
            ))}
      </div>
    </section>
  );
};
