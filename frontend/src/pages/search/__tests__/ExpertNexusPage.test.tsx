import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import ExpertNexusPage from '../ExpertNexusPage';

vi.mock('../../hooks/useSSE', () => ({
  useSSE: () => ({
    start: vi.fn(),
    stop: vi.fn(),
    isStreaming: false,
    error: null,
  }),
}));

describe('ExpertNexusPage', () => {
  it('renders search input and placeholder correctly', () => {
    render(
      <MemoryRouter initialEntries={['/search/nexus?q=test']}>
        <ExpertNexusPage />
      </MemoryRouter>,
    );

    expect(screen.getByPlaceholderText(/Posez une question/i)).toBeInTheDocument();
  });
});
