import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import ForgeHubPage from '../ForgeHubPage';

// react-i18next is mocked globally (t returns the key) in vitest setup.

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren<React.HTMLAttributes<HTMLDivElement>>) => (
      <div {...props}>{children}</div>
    ),
    button: ({ children, ...props }: React.PropsWithChildren<React.ButtonHTMLAttributes<HTMLButtonElement>>) => (
      <button {...props}>{children}</button>
    ),
  },
  AnimatePresence: ({ children }: React.PropsWithChildren<unknown>) => <>{children}</>,
}));

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ForgeHubPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe('ForgeHubPage', () => {
  it('renders the four category relics', () => {
    renderPage();
    expect(screen.getByLabelText('forge_hub.categories.narrative.title')).toBeInTheDocument();
    expect(screen.getByLabelText('forge_hub.categories.visual.title')).toBeInTheDocument();
    expect(screen.getByLabelText('forge_hub.categories.audio.title')).toBeInTheDocument();
    expect(screen.getByLabelText('forge_hub.categories.experimental.title')).toBeInTheDocument();
  });

  it('renders the localized title and description keys', () => {
    renderPage();
    expect(screen.getByText('forge_hub.description')).toBeInTheDocument();
  });

  it('keeps the overlay closed initially', () => {
    renderPage();
    expect(screen.queryByLabelText('Fermer')).not.toBeInTheDocument();
  });

  it('opens the lab overlay when a category is selected', () => {
    renderPage();
    fireEvent.click(screen.getByLabelText('forge_hub.categories.visual.title'));
    expect(screen.getByLabelText('Fermer')).toBeInTheDocument();
    // visual category labs include the Manga Lab entry
    expect(screen.getByText('Manga Lab')).toBeInTheDocument();
  });

  it('closes the overlay via the close button', () => {
    renderPage();
    fireEvent.click(screen.getByLabelText('forge_hub.categories.narrative.title'));
    expect(screen.getByText('Forge de Réalité')).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('Fermer'));
    expect(screen.queryByLabelText('Fermer')).not.toBeInTheDocument();
  });
});
