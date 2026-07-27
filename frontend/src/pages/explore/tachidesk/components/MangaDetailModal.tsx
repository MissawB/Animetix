import React, { useMemo, useState } from 'react';
import { Modal } from '../../../../components/ui/Modal';
import { Loader2, ChevronRight, ChevronDown, Heart, ArrowUp, ArrowDown } from 'lucide-react';
import type { Manga, Chapter, MangaDetails } from '../types';

interface MangaDetailModalProps {
  isOpen: boolean;
  selectedManga: Manga | null;
  mangaDetails: MangaDetails | null;
  chapters: Chapter[];
  loadingDetails: boolean;
  importStatus: string | null;
  importingChapter: string | null;
  onClose: () => void;
  onReadChapter: (chapter: Chapter) => void;
  getProxiedImageUrl: (url: string) => string;
  isFavorited?: boolean;
  favoriteStatus?: 'reading' | 'completed' | 'plan_to_read' | null;
  togglingFavorite?: boolean;
  onToggleFavorite?: () => void;
  onUpdateFavoriteStatus?: (status: 'reading' | 'completed' | 'plan_to_read') => void;
}

const STATUS_LABEL: Record<string, string> = {
  ONGOING: 'En cours',
  COMPLETED: 'Terminé',
  LICENSED: 'Licencié',
  PUBLISHING_FINISHED: 'Publication terminée',
  CANCELLED: 'Annulé',
  ON_HIATUS: 'En pause',
  UNKNOWN: '',
};

const MangaDetailModalComponent: React.FC<MangaDetailModalProps> = ({
  isOpen,
  selectedManga,
  mangaDetails,
  chapters,
  loadingDetails,
  importStatus,
  importingChapter,
  onClose,
  onReadChapter,
  getProxiedImageUrl,
  isFavorited = false,
  favoriteStatus = null,
  togglingFavorite = false,
  onToggleFavorite,
  onUpdateFavoriteStatus,
}) => {
  // Tri des chapitres : croissant (1→N) par défaut, ou décroissant.
  const [sortDesc, setSortDesc] = useState(false);

  const titles = useMemo(() => {
    const list = [selectedManga?.title, mangaDetails?.title].filter(Boolean) as string[];
    return Array.from(new Set(list.map((t) => t.trim())));
  }, [selectedManga?.title, mangaDetails?.title]);

  const sortedChapters = useMemo(() => {
    const arr = [...chapters];
    arr.sort((a, b) =>
      sortDesc ? b.chapterNumber - a.chapterNumber : a.chapterNumber - b.chapterNumber,
    );
    return arr;
  }, [chapters, sortDesc]);

  const rawStatus = mangaDetails?.status || '';
  const status = rawStatus ? (STATUS_LABEL[rawStatus] ?? rawStatus) : '';
  const genres = mangaDetails?.genre ?? [];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      size="xl"
      title={
        <span className="font-manga uppercase italic tracking-tight">
          {titles[0] || selectedManga?.title || 'Œuvre'}
        </span>
      }
      ariaDescription="Détails de l'œuvre : titre, description et liste des chapitres."
      contentClassName="!bg-[#0F1016] !border-[#F4F1E8]/10"
    >
      <div className="space-y-6">
        {/* Affiche + informations */}
        <div className="flex flex-col gap-6 sm:flex-row">
          <div className="mx-auto w-40 flex-shrink-0 self-start overflow-hidden rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] sm:mx-0">
            <img
              src={getProxiedImageUrl(selectedManga?.thumbnailUrl || '')}
              alt={titles[0] || ''}
              className="block h-auto w-full"
              loading="lazy"
              decoding="async"
            />
          </div>

          <div className="min-w-0 flex-1 space-y-3">
            {/* Titre(s) */}
            <div className="space-y-0.5">
              {titles.map((t, i) => (
                <h3
                  key={t}
                  className={
                    i === 0
                      ? 'font-manga text-xl font-black uppercase italic leading-tight text-[#F4F1E8]'
                      : 'text-sm font-bold italic text-[#8F94A5]'
                  }
                >
                  {t}
                </h3>
              ))}
            </div>

            {/* Méta */}
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-[#8F94A5]">
              {mangaDetails?.author && (
                <span>
                  <span className="text-[#8F94A5]/60">Auteur : </span>
                  <span className="text-[#F4F1E8]/90">{mangaDetails.author}</span>
                </span>
              )}
              {status && (
                <span>
                  <span className="text-[#8F94A5]/60">Statut : </span>
                  <span className="text-[#F4F1E8]/90">{status}</span>
                </span>
              )}
              <span>
                <span className="text-[#8F94A5]/60">Chapitres : </span>
                <span className="tabular-nums text-[#F4F1E8]/90">{chapters.length}</span>
              </span>
            </div>

            {/* Genres */}
            {genres.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {genres.slice(0, 14).map((g) => (
                  <span
                    key={g}
                    className="rounded-full border border-[#F4F1E8]/10 bg-[#F4F1E8]/[0.04] px-2.5 py-0.5 text-[10px] font-bold text-[#8F94A5]"
                  >
                    {g}
                  </span>
                ))}
              </div>
            )}

            {/* Suivi (favori) */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              {onToggleFavorite && (
                <button
                  type="button"
                  onClick={onToggleFavorite}
                  disabled={togglingFavorite}
                  className={`flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-[10px] font-black uppercase italic tracking-wider transition-colors ${
                    isFavorited
                      ? 'border-[#FDB913]/40 bg-[#FDB913]/10 text-[#FDB913] hover:bg-[#FDB913]/20'
                      : 'border-[#F4F1E8]/15 bg-[#F4F1E8]/[0.04] text-[#8F94A5] hover:text-[#F4F1E8]'
                  }`}
                >
                  {togglingFavorite ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <Heart
                      className={`h-3 w-3 ${isFavorited ? 'fill-current text-[#FDB913]' : ''}`}
                    />
                  )}
                  {isFavorited ? 'Suivi' : 'Suivre'}
                </button>
              )}
              {isFavorited && onUpdateFavoriteStatus && (
                <div className="relative">
                  <select
                    value={favoriteStatus || 'plan_to_read'}
                    disabled={togglingFavorite}
                    onChange={(e) =>
                      onUpdateFavoriteStatus(
                        e.target.value as 'reading' | 'completed' | 'plan_to_read',
                      )
                    }
                    className="cursor-pointer appearance-none rounded-xl border border-[#F4F1E8]/10 bg-[#F4F1E8]/[0.04] py-1.5 pl-3 pr-8 text-[10px] font-black uppercase tracking-wider text-[#F4F1E8]/80 outline-none transition-colors hover:bg-[#F4F1E8]/[0.08]"
                  >
                    <option value="reading" className="bg-[#0F1016] text-[#F4F1E8]">
                      En cours
                    </option>
                    <option value="plan_to_read" className="bg-[#0F1016] text-[#F4F1E8]">
                      À lire
                    </option>
                    <option value="completed" className="bg-[#0F1016] text-[#F4F1E8]">
                      Terminé
                    </option>
                  </select>
                  <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 h-3 w-3 -translate-y-1/2 text-[#8F94A5]" />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Description */}
        <div>
          <h4 className="mb-2 flex items-center gap-2 font-manga text-xs font-black uppercase tracking-widest text-[#8F94A5]">
            <span className="h-3 w-1 flex-none bg-[#E8442B]" aria-hidden />
            Description
          </h4>
          {mangaDetails?.description ? (
            <p className="whitespace-pre-line text-sm leading-relaxed text-[#F4F1E8]/75">
              {mangaDetails.description}
            </p>
          ) : loadingDetails ? (
            <p className="text-sm text-[#8F94A5]">Chargement de la description…</p>
          ) : (
            <p className="text-sm italic text-[#8F94A5]">Aucune description disponible.</p>
          )}
        </div>

        {importStatus && (
          <div className="flex items-center gap-3 rounded-xl border border-[#FDB913]/25 bg-[#FDB913]/10 p-3.5 text-xs font-semibold text-[#FDB913]">
            <Loader2 className="h-4 w-4 flex-shrink-0 animate-spin" />
            <div>{importStatus}</div>
          </div>
        )}

        {/* Chapitres */}
        <div>
          <div className="mb-3 flex items-center justify-between gap-3">
            <h4 className="flex items-center gap-2 font-manga text-xs font-black uppercase tracking-widest text-[#8F94A5]">
              <span className="h-3 w-1 flex-none bg-[#E8442B]" aria-hidden />
              Chapitres
              <span className="rounded-full bg-[#F4F1E8]/5 px-2 py-0.5 text-[10px] tabular-nums text-[#8F94A5]">
                {chapters.length}
              </span>
            </h4>
            <button
              type="button"
              onClick={() => setSortDesc((v) => !v)}
              disabled={chapters.length === 0}
              title="Inverser l'ordre des chapitres"
              className="inline-flex items-center gap-1.5 rounded-lg border border-[#F4F1E8]/15 px-3 py-1.5 text-[10px] font-black uppercase tracking-wider text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8] disabled:opacity-40"
            >
              {sortDesc ? (
                <ArrowDown className="h-3.5 w-3.5" />
              ) : (
                <ArrowUp className="h-3.5 w-3.5" />
              )}
              {sortDesc ? 'Décroissant' : 'Croissant'}
            </button>
          </div>

          {loadingDetails ? (
            <div className="flex flex-col items-center justify-center gap-3 py-12 text-[#8F94A5]">
              <Loader2 className="h-6 w-6 animate-spin text-[#FDB913]" />
              <p className="text-xs font-medium">Récupération des chapitres…</p>
            </div>
          ) : chapters.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-[#F4F1E8]/10 py-12 text-center text-xs font-semibold text-[#8F94A5]">
              Aucun chapitre indexé pour ce manga.
            </div>
          ) : (
            <div className="max-h-[45vh] space-y-2 overflow-y-auto pr-1">
              {sortedChapters.map((ch) => (
                <div
                  key={ch.id}
                  className="group flex items-center justify-between rounded-xl border border-[#F4F1E8]/5 bg-[#0B0C10] p-3 transition-colors hover:border-[#F4F1E8]/15"
                >
                  <div className="flex min-w-0 flex-col pr-4">
                    <span className="line-clamp-1 text-xs font-bold text-[#F4F1E8]/90 transition-colors group-hover:text-[#FDB913]">
                      {ch.name}
                    </span>
                    <span className="text-[9px] font-medium tabular-nums text-[#8F94A5]">
                      Numéro {ch.chapterNumber}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => onReadChapter(ch)}
                    disabled={!!importingChapter}
                    className="flex items-center gap-1 rounded-lg border border-[#FDB913]/25 bg-[#FDB913]/10 px-3 py-1.5 text-[10px] font-black uppercase italic tracking-wider text-[#FDB913] transition-colors hover:bg-[#FDB913] hover:text-[#0B0C10] disabled:opacity-50"
                  >
                    {importingChapter === ch.id ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <>
                        Lire <ChevronRight className="h-3 w-3" />
                      </>
                    )}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
};

export const MangaDetailModal = React.memo(MangaDetailModalComponent);
