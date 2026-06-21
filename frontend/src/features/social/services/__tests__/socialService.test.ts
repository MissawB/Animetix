import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { SocialDashboardData, DiscoveryClub, ClubEvent } from '../../../../types';
import { apiClient } from '../../../../utils/apiClient';
import { socialService } from '../socialService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

const mocked = vi.mocked(apiClient);

const makeClub = (id: number): DiscoveryClub => ({ id } as DiscoveryClub);

describe('socialService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getDashboard fetches the dashboard endpoint', async () => {
    const data = {} as SocialDashboardData;
    mocked.mockResolvedValue(data);

    const result = await socialService.getDashboard();

    expect(mocked).toHaveBeenCalledWith('/api/v1/social/dashboard/');
    expect(result).toBe(data);
  });

  it('toggleFollow posts to the toggle_follow endpoint', async () => {
    mocked.mockResolvedValue(null);

    await socialService.toggleFollow(7);

    expect(mocked).toHaveBeenCalledWith('/api/v1/social/7/toggle_follow/', { method: 'POST' });
  });

  it('createClub posts the club payload', async () => {
    const club = makeClub(1);
    mocked.mockResolvedValue(club);
    const payload = { name: 'C', description: 'd', theme: 't', is_private: true };

    const result = await socialService.createClub(payload);

    expect(mocked).toHaveBeenCalledWith('/api/v1/clubs/', {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    });
    expect(result).toBe(club);
  });

  it('getClubDetails fetches the club by id', async () => {
    const club = makeClub(2);
    mocked.mockResolvedValue(club);

    const result = await socialService.getClubDetails(2);

    expect(mocked).toHaveBeenCalledWith('/api/v1/clubs/2/');
    expect(result).toBe(club);
  });

  it('getClubEvents fetches events filtered by club', async () => {
    const events: ClubEvent[] = [];
    mocked.mockResolvedValue(events);

    const result = await socialService.getClubEvents(3);

    expect(mocked).toHaveBeenCalledWith('/api/v1/club-events/?club=3');
    expect(result).toBe(events);
  });
});
