import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useClub, useClubEvent } from '../useClub';
import { socialService } from '../../services/socialService';
import { DiscoveryClub, ClubEvent } from '../../../../types';

vi.mock('../../services/socialService');

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

const mockClub = (id: number): DiscoveryClub =>
  ({
    id,
    name: 'Otaku Club',
    description: 'desc',
    creator: 1,
    creator_name: 'me',
    members_count: 3,
    is_private: false,
    events: [],
    created_at: '',
    updated_at: '',
  } as DiscoveryClub);

const mockEvent = (id: number): ClubEvent => ({
  id,
  club: 1,
  title: 'Watch party',
  description: 'desc',
  event_date: '2026-01-01',
  created_at: '2026-01-01',
});

describe('useClub', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads club details and events when clubId is set', async () => {
    const club = mockClub(7);
    const events = [mockEvent(1)];
    (socialService.getClubDetails as Mock).mockResolvedValue(club);
    (socialService.getClubEvents as Mock).mockResolvedValue(events);

    const { result } = renderHook(() => useClub(7), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.isLoadingClub).toBe(false));
    await waitFor(() => expect(result.current.isLoadingEvents).toBe(false));

    expect(socialService.getClubDetails).toHaveBeenCalledWith(7);
    expect(socialService.getClubEvents).toHaveBeenCalledWith(7);
    expect(result.current.club).toEqual(club);
    expect(result.current.events).toEqual(events);
  });

  it('does not fetch when clubId is falsy and defaults events to []', async () => {
    (socialService.getClubDetails as Mock).mockResolvedValue(mockClub(0));
    (socialService.getClubEvents as Mock).mockResolvedValue([mockEvent(1)]);

    const { result } = renderHook(() => useClub(0), { wrapper: makeWrapper() });

    expect(result.current.events).toEqual([]);
    await waitFor(() => expect(socialService.getClubDetails).not.toHaveBeenCalled());
    expect(socialService.getClubEvents).not.toHaveBeenCalled();
  });

  it('createEvent triggers the mutation', async () => {
    const club = mockClub(7);
    (socialService.getClubDetails as Mock).mockResolvedValue(club);
    (socialService.getClubEvents as Mock).mockResolvedValue([]);

    const { result } = renderHook(() => useClub(7), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoadingClub).toBe(false));

    (socialService.getClubDetails as Mock).mockClear();
    await act(async () => {
      result.current.createEvent();
    });

    await waitFor(() => expect(socialService.getClubDetails).toHaveBeenCalled());
  });
});

describe('useClubEvent', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads the event when eventId is set', async () => {
    const club = mockClub(3);
    (socialService.getClubDetails as Mock).mockResolvedValue(club);

    const { result } = renderHook(() => useClubEvent(3), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(socialService.getClubDetails).toHaveBeenCalledWith(3);
    expect(result.current.event).toEqual(club);
  });

  it('toggleParticipation triggers the mutation', async () => {
    (socialService.getClubDetails as Mock).mockResolvedValue(mockClub(3));

    const { result } = renderHook(() => useClubEvent(3), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    (socialService.getClubDetails as Mock).mockClear();
    await act(async () => {
      result.current.toggleParticipation();
    });

    await waitFor(() => expect(socialService.getClubDetails).toHaveBeenCalled());
  });
});
