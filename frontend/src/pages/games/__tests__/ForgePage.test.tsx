import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import ForgePage from '../ForgePage';

vi.mock('../../hooks/useForge', () => ({
  FUSION_COST: 50,
  useForge: () => ({
    itemA: null,
    setItemA: vi.fn(),
    itemB: null,
    setItemB: vi.fn(),
    chaosLevel: 50,
    setChaosLevel: vi.fn(),
    balance: 50,
    setBalance: vi.fn(),
    artStyle: 'Cyberpunk',
    setArtStyle: vi.fn(),
    styleDir: 1,
    setStyleDir: vi.fn(),
    isGenerating: false,
    fusionData: null,
    status: '',
    error: null,
    walletBalance: 100,
    isAuthenticated: true,
    handleStartFusion: vi.fn(),
    resetForge: vi.fn(),
  }),
}));

describe('ForgePage', () => {
  it('renders forge title correctly', () => {
    render(
      <MemoryRouter>
        <ForgePage />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: /FORGE/i })).toBeInTheDocument();
  });
});
