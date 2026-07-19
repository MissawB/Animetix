import { describe, it, expect } from 'vitest';
import { normalizeText, deriveGenres, filterFeedItems } from '../useExploreFilter';
import type { FeedRowData } from '../../components/FeedRow';

const rows: FeedRowData[] = [
  {
    kind: 'a',
    title: 'Row A',
    reason: '',
    seed: null,
    items: [
      { id: '1', title: 'Pokémon', media_type: 'Anime', genres: ['Action', 'Aventure'] },
      { id: '2', title: 'Naruto', media_type: 'Anime', genres: ['Action'] },
    ],
  },
  {
    kind: 'b',
    title: 'Row B',
    reason: '',
    seed: null,
    items: [
      { id: '2', title: 'Naruto', media_type: 'Anime', genres: ['Action'] }, // dup id
      { id: '3', title: 'Fruits Basket', media_type: 'Anime', genres: ['Romance'] },
    ],
  },
];

describe('normalizeText', () => {
  it('strips diacritics, lowercases, trims', () => {
    expect(normalizeText('  Pokémon ')).toBe('pokemon');
  });
});

describe('deriveGenres', () => {
  it('returns genres ranked by frequency', () => {
    expect(deriveGenres(rows)[0]).toBe('Action');
  });
  it('respects the limit', () => {
    expect(deriveGenres(rows, 1)).toEqual(['Action']);
  });
});

describe('filterFeedItems', () => {
  it('returns all unique items when query and genres are empty', () => {
    const res = filterFeedItems(rows, '', new Set());
    expect(res.map((i) => i.id)).toEqual(['1', '2', '3']);
  });
  it('matches titles accent-insensitively', () => {
    const res = filterFeedItems(rows, 'pokemon', new Set());
    expect(res.map((i) => i.id)).toEqual(['1']);
  });
  it('requires every selected genre', () => {
    const res = filterFeedItems(rows, '', new Set(['Action', 'Aventure']));
    expect(res.map((i) => i.id)).toEqual(['1']);
  });
});
