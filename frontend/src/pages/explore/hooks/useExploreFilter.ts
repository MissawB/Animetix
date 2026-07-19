import { useMemo } from 'react';
import type { FeedItem } from '../components/MediaCard';
import type { FeedRowData } from '../components/FeedRow';

export const normalizeText = (value: string): string =>
  value.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();

export const deriveGenres = (rows: FeedRowData[], limit = 12): string[] => {
  const counts = new Map<string, number>();
  for (const row of rows) {
    for (const item of row.items) {
      for (const genre of item.genres ?? []) {
        counts.set(genre, (counts.get(genre) ?? 0) + 1);
      }
    }
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([genre]) => genre);
};

export const filterFeedItems = (
  rows: FeedRowData[],
  query: string,
  selectedGenres: Set<string>,
): FeedItem[] => {
  const q = normalizeText(query);
  const genres = [...selectedGenres];
  const seen = new Set<string>();
  const result: FeedItem[] = [];
  for (const row of rows) {
    for (const item of row.items) {
      if (seen.has(item.id)) continue;
      seen.add(item.id);
      const titleOk = q === '' || normalizeText(item.title).includes(q);
      const genresOk = genres.length === 0 || genres.every((g) => (item.genres ?? []).includes(g));
      if (titleOk && genresOk) result.push(item);
    }
  }
  return result;
};

export const useExploreFilter = (
  rows: FeedRowData[],
  query: string,
  selectedGenres: Set<string>,
): { derivedGenres: string[]; results: FeedItem[] } => {
  const derivedGenres = useMemo(() => deriveGenres(rows), [rows]);
  const results = useMemo(
    () => filterFeedItems(rows, query, selectedGenres),
    [rows, query, selectedGenres],
  );
  return { derivedGenres, results };
};
