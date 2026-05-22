import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, Mock } from 'vitest';
import { useSocialDashboard } from '../hooks/useSocialDashboard';
import { socialService } from '../services/socialService';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

vi.mock('../services/socialService');

const queryClient = new QueryClient();
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('useSocialDashboard Hook', () => {
  it('devrait charger les données du dashboard social', async () => {
    const mockData = { following: [], followers: [] };
    (socialService.getDashboard as Mock).mockResolvedValue(mockData);

    const { result } = renderHook(() => useSocialDashboard(), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.data).toEqual(mockData);
  });
});
