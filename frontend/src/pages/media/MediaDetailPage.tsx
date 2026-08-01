import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Search, Star } from 'lucide-react';
import { useMediaDetail } from '../../features/media/hooks/useMediaDetail';
import { useMediaCharacters } from '../../features/media/hooks/useMediaCharacters';
import { Button } from '../../components/ui/Button';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { ChapterList } from '../../features/manga-reader/components/ChapterList';
import { TrackerLinkCard } from '../../features/media/trackers/TrackerLinkCard';
import { useTranslation } from 'react-i18next';
import { DetailHero } from './components/DetailHero';
import { SectionHeader } from './components/SectionHeader';
import { SeiyuuGrid } from './components/SeiyuuGrid';
import { CharacterGrid } from './components/CharacterGrid';
import { CharacterGraph } from './components/CharacterGraph';
import { RelatedCarousel } from './components/RelatedCarousel';
import { MediaDetail } from '../../types';

/** Bande technique façon achevé d'imprimer : le registre factuel de l'œuvre. */
const Colophon: React.FC<{ item: MediaDetail }> = ({ item }) => {
  const { t } = useTranslation();
  const studio = [...new Set(item.studios ?? [])][0];
  const cells: Array<{ label: string; value: React.ReactNode }> = [];

  if (item.rating != null) {
    cells.push({
      label: t('media.detail.rating', 'Note'),
      value: (
        <span className="flex items-center gap-1.5 font-manga text-lg font-black italic text-[#FDB913]">
          <Star className="h-4 w-4" fill="currentColor" aria-hidden="true" />
          {item.rating.toFixed(1)}
          <span className="text-[10px] font-bold not-italic tracking-widest text-[#8F94A5]">
            / 100
          </span>
        </span>
      ),
    });
  }
  if (item.year) {
    cells.push({ label: t('media.detail.year', 'Année'), value: item.year });
  }
  if (studio) {
    cells.push({ label: 'Studio', value: studio });
  }
  if (item.author) {
    cells.push({ label: t('media.detail.author', 'Auteur'), value: item.author });
  }
  if (item.popularity != null) {
    cells.push({
      label: t('media.detail.popularity', 'Popularité'),
      value: item.popularity.toLocaleString('fr-FR'),
    });
  }

  if (cells.length === 0) return null;

  return (
    <dl
      className="grid gap-px overflow-hidden rounded-xl border border-[#F4F1E8]/10 bg-[#F4F1E8]/10"
      style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))' }}
    >
      {cells.map(({ label, value }) => (
        <div key={label} className="bg-[#0F1016] px-5 py-4">
          <dt className="text-[9px] font-black uppercase tracking-[0.25em] text-[#8F94A5]">
            {label}
          </dt>
          <dd className="mt-1 text-sm font-bold text-[#F4F1E8]">{value}</dd>
        </div>
      ))}
    </dl>
  );
};

const CHARACTERS_PAGE_SIZE = 18;

const normalize = (s: string) => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');

/** Grille des personnages : recherche + pagination, liste complète à la demande. */
const CharactersSection: React.FC<{ mediaType?: string; itemId?: string }> = ({
  mediaType,
  itemId,
}) => {
  const { t } = useTranslation();
  const [showAll, setShowAll] = React.useState(false);
  const [query, setQuery] = React.useState('');
  const [page, setPage] = React.useState(0);
  const [view, setView] = React.useState<'grid' | 'graph'>('grid');
  const { data } = useMediaCharacters(mediaType, itemId, showAll ? 500 : undefined);
  const characters = data?.characters ?? [];
  const total = data?.total ?? characters.length;

  if (characters.length === 0) return null;

  const filtered = query.trim()
    ? characters.filter((c) => normalize(c.name).includes(normalize(query)))
    : characters;
  const pageCount = Math.max(1, Math.ceil(filtered.length / CHARACTERS_PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);
  const visible = filtered.slice(
    safePage * CHARACTERS_PAGE_SIZE,
    (safePage + 1) * CHARACTERS_PAGE_SIZE,
  );

  const onQueryChange = (value: string) => {
    setQuery(value);
    setPage(0);
    // chercher implique chercher parmi TOUS les personnages
    if (value.trim() && !showAll) setShowAll(true);
  };

  const pagerButton =
    'rounded-full border border-[#F4F1E8]/15 px-4 py-2 text-xs font-black uppercase tracking-widest text-[#8F94A5] transition-colors hover:border-[#F4F1E8]/40 hover:text-[#F4F1E8] disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:border-[#F4F1E8]/15 disabled:hover:text-[#8F94A5] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]';

  return (
    <section>
      <SectionHeader title={t('media.detail.characters', 'Personnages')} />
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-4">
          <div
            role="group"
            aria-label={t('media.detail.characters_view', 'Affichage des personnages')}
            className="flex overflow-hidden rounded-full border border-[#F4F1E8]/15"
          >
            {(
              [
                { key: 'grid', label: t('media.detail.view_grid', 'Grille') },
                { key: 'graph', label: t('media.detail.view_graph', 'Graphe') },
              ] as const
            ).map(({ key, label }) => (
              <button
                key={key}
                type="button"
                onClick={() => setView(key)}
                aria-pressed={view === key}
                className={`px-5 py-2 text-xs font-black uppercase tracking-widest transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-[#FDB913] ${
                  view === key
                    ? 'bg-[#E8442B] text-[#F4F1E8]'
                    : 'text-[#8F94A5] hover:text-[#F4F1E8]'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          {view === 'grid' && (
            <div className="flex items-center gap-2 border-b border-[#F4F1E8]/20 px-1 py-2 transition-colors focus-within:border-[#FDB913]">
              <Search className="h-4 w-4 text-[#8F94A5]" aria-hidden="true" />
              <input
                type="search"
                value={query}
                onChange={(e) => onQueryChange(e.target.value)}
                placeholder={t('media.detail.search_character', 'Rechercher un personnage…')}
                aria-label={t('media.detail.search_character_label', 'Rechercher un personnage')}
                className="w-52 bg-transparent text-sm text-[#F4F1E8] outline-none placeholder:text-[#8F94A5]/70"
              />
            </div>
          )}
        </div>
        {view === 'grid' && !showAll && total > characters.length && (
          <button
            type="button"
            onClick={() => setShowAll(true)}
            className="rounded-full border border-[#F4F1E8]/15 px-6 py-2.5 text-xs font-black uppercase tracking-widest text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
          >
            {t('media.detail.show_all_characters', 'Voir les {{count}} personnages', {
              count: total,
            })}
          </button>
        )}
      </div>

      {view === 'graph' ? (
        <CharacterGraph mediaType={mediaType} itemId={itemId} />
      ) : visible.length > 0 ? (
        <CharacterGrid characters={visible} />
      ) : (
        <p className="py-12 text-center text-sm text-[#8F94A5]">
          {t(
            'media.detail.no_character_match',
            'Aucun personnage ne correspond. Modifie ta recherche.',
          )}
        </p>
      )}

      {view === 'grid' && pageCount > 1 && (
        <nav
          aria-label={t('media.detail.characters_pagination', 'Pagination des personnages')}
          className="mt-6 flex items-center justify-center gap-4"
        >
          <button
            type="button"
            onClick={() => setPage(safePage - 1)}
            disabled={safePage === 0}
            aria-label={t('media.detail.previous_page', 'Page précédente')}
            className={pagerButton}
          >
            ←
          </button>
          <span className="text-xs font-black uppercase tracking-widest text-[#8F94A5]">
            {safePage + 1} <span className="text-[#F4F1E8]/40">/ {pageCount}</span>
          </span>
          <button
            type="button"
            onClick={() => setPage(safePage + 1)}
            disabled={safePage >= pageCount - 1}
            aria-label={t('media.detail.next_page', 'Page suivante')}
            className={pagerButton}
          >
            →
          </button>
        </nav>
      )}
    </section>
  );
};

const MediaDetailPage: React.FC = () => {
  const { t } = useTranslation();
  const { mediaType, itemId } = useParams<{ mediaType: string; itemId: string }>();
  const {
    data: item,
    isLoading,
    isError,
  } = useMediaDetail(mediaType || 'Anime', itemId || '') as {
    data: MediaDetail | undefined;
    isLoading: boolean;
    isError: boolean;
  };

  if (isLoading)
    return (
      <div className="mx-auto max-w-7xl px-6 py-16">
        <CardSkeleton />
      </div>
    );

  if (isError || !item)
    return (
      <div className="mx-auto max-w-7xl px-6 py-32 text-center">
        <h2 className="mb-6 font-manga text-4xl font-black uppercase italic text-[#E8442B]">
          {t('media.detail.not_found', 'Œuvre introuvable')}
        </h2>
        <p className="mb-12 font-bold uppercase tracking-widest text-[#8F94A5]">
          {t('media.detail.not_found_desc', 'Le Nexus s’est peut-être effondré…')}
        </p>
        <Button as={Link} to="/explore/" variant="outline">
          {t('media.detail.back_nexus', 'RETOURNER AU NEXUS')}
        </Button>
      </div>
    );

  return (
    <AnimatedPage>
      <DetailHero item={item} mediaType={mediaType || 'Anime'} itemId={itemId || ''} />

      <div className="relative z-10 mx-auto max-w-7xl space-y-12 px-4 pb-24 sm:px-6">
        <section className="pt-8">
          <Colophon item={item} />
        </section>

        <section>
          <SectionHeader title="Synopsis" />
          <p className="max-w-3xl text-sm font-medium leading-relaxed">
            {item.description ||
              t('media.detail.no_synopsis', 'Aucun synopsis disponible dans le Nexus.')}
          </p>
        </section>

        <CharactersSection key={`${mediaType}-${itemId}`} mediaType={mediaType} itemId={itemId} />

        {mediaType?.toLowerCase() === 'manga' && itemId && (
          <>
            <ChapterList mediaId={itemId} mediaTitle={item.title} />
            <TrackerLinkCard mediaId={itemId} />
          </>
        )}

        {item.seiyuu && item.seiyuu.length > 0 && (
          <section>
            <SectionHeader title={t('media.detail.seiyuu', 'Seiyuu')} />
            <SeiyuuGrid seiyuu={item.seiyuu} />
          </section>
        )}

        {item.micro_tags && item.micro_tags.length > 0 && (
          <section>
            <SectionHeader title={t('media.detail.micro_tags', 'Micro-Tags IA')} />
            <div className="flex flex-wrap gap-2">
              {item.micro_tags.slice(0, 10).map((tag: string) => (
                <span
                  key={tag}
                  className="rounded-sm border border-[#E8442B]/40 px-2.5 py-1 text-[9px] font-bold uppercase tracking-widest text-[#E8442B]"
                >
                  {tag}
                </span>
              ))}
            </div>
          </section>
        )}

        {item.related_items && item.related_items.length > 0 && (
          <section className="!mt-20">
            <SectionHeader title={t('media.detail.related_works', 'Œuvres Liées dans le Graphe')} />
            <RelatedCarousel items={item.related_items} mediaType={mediaType || 'Anime'} />
          </section>
        )}
      </div>

      <style>{`
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
      `}</style>
    </AnimatedPage>
  );
};

export default MediaDetailPage;
