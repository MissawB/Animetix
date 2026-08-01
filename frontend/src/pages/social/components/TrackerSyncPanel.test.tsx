import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { socialService } from '../../../features/social/services/socialService';
import { TrackerSyncPanel } from './TrackerSyncPanel';

const wrap = (ui: React.ReactNode) => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(React.createElement(QueryClientProvider, { client }, ui));
};

beforeEach(() => vi.restoreAllMocks());

describe('TrackerSyncPanel', () => {
  it('lists the works linked to a connected tracker', async () => {
    vi.spyOn(socialService, 'getTrackerLinks').mockResolvedValue([
      {
        tracker: 'anilist',
        manga_id: 'suwayomi:1:809',
        manga_title: 'One Punch-Man',
        remote_id: '809',
        remote_title: 'One Punch-Man',
        remote_progress: 164,
        status: 'confirmed',
      },
    ]);

    wrap(
      <TrackerSyncPanel
        connections={[{ tracker: 'anilist', username: 'missaw', id: 1 } as never]}
      />,
    );

    expect(await screen.findByText('One Punch-Man')).toBeInTheDocument();
    expect(screen.getByText(/164/)).toBeInTheDocument();
  });
});
