import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../../../../utils/apiClient';
import { adminService } from '../adminService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

const mocked = vi.mocked(apiClient);

describe('adminService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getEval fetches the eval endpoint', async () => {
    const data = { eval: true };
    mocked.mockResolvedValue(data);

    const result = await adminService.getEval();

    expect(mocked).toHaveBeenCalledWith('/api/v1/admin/eval/');
    expect(result).toBe(data);
  });

  it('getHealth fetches the health endpoint', async () => {
    const data = { health: 'ok' };
    mocked.mockResolvedValue(data);

    const result = await adminService.getHealth();

    expect(mocked).toHaveBeenCalledWith('/api/v1/admin/health/');
    expect(result).toBe(data);
  });

  it('getUsers fetches the users endpoint', async () => {
    const data = [{ id: 1 }];
    mocked.mockResolvedValue(data);

    const result = await adminService.getUsers();

    expect(mocked).toHaveBeenCalledWith('/api/v1/admin/users/');
    expect(result).toBe(data);
  });

  it('toggleStaff posts to the toggle-staff endpoint', async () => {
    const data = { ok: true };
    mocked.mockResolvedValue(data);

    const result = await adminService.toggleStaff(5);

    expect(mocked).toHaveBeenCalledWith('/api/v1/admin/users/5/toggle-staff/', { method: 'POST' });
    expect(result).toBe(data);
  });

  it('toggleActive posts to the toggle-active endpoint', async () => {
    const data = { ok: true };
    mocked.mockResolvedValue(data);

    const result = await adminService.toggleActive(5);

    expect(mocked).toHaveBeenCalledWith('/api/v1/admin/users/5/toggle-active/', { method: 'POST' });
    expect(result).toBe(data);
  });
});
