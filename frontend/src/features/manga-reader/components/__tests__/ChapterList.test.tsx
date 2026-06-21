import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChapterList } from '../ChapterList';

interface ApiChapter {
  id: number;
  number: number;
  title: string;
  pages: unknown[];
}

interface QueryResult {
  data: ApiChapter[] | undefined;
  isLoading: boolean;
  isError: boolean;
}

let queryResult: QueryResult = { data: undefined, isLoading: true, isError: false };

vi.mock('@tanstack/react-query', () => ({
  useQuery: () => queryResult,
}));

vi.mock('../../../utils/apiClient', () => ({
  apiClient: vi.fn(),
}));

vi.mock('../ChapterDownloadButton', () => ({
  ChapterDownloadButton: () => <button type="button">download</button>,
}));

const renderList = () =>
  render(
    <MemoryRouter>
      <ChapterList mediaId="42" mediaTitle="One Piece" />
    </MemoryRouter>,
  );

describe('ChapterList', () => {
  beforeEach(() => {
    queryResult = { data: undefined, isLoading: true, isError: false };
  });

  it('renders a loading message', () => {
    renderList();
    expect(screen.getByText(/Chargement des chapitres/)).toBeInTheDocument();
  });

  it('renders an error message', () => {
    queryResult = { data: undefined, isLoading: false, isError: true };
    renderList();
    expect(screen.getByText(/Erreur lors du chargement/)).toBeInTheDocument();
  });

  it('renders an empty message when there are no chapters', () => {
    queryResult = { data: [], isLoading: false, isError: false };
    renderList();
    expect(screen.getByText(/Aucun chapitre disponible/)).toBeInTheDocument();
  });

  it('renders chapter rows with titles and links', () => {
    queryResult = {
      isLoading: false,
      isError: false,
      data: [
        { id: 1, number: 1, title: 'Romance Dawn', pages: [] },
        { id: 2, number: 2, title: '', pages: [] },
      ],
    };
    renderList();
    expect(screen.getByText('Romance Dawn')).toBeInTheDocument();
    // Falls back to "Chapitre {number}" when no title is provided.
    expect(screen.getByText('Chapitre 2')).toBeInTheDocument();
    expect(screen.getByText('Romance Dawn').closest('a')).toHaveAttribute(
      'href',
      '/media/manga/42/1/',
    );
  });
});
