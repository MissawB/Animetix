import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import LabHubPage from '../LabHubPage';

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <LabHubPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe('LabHubPage', () => {
  it('renders the header', () => {
    renderPage();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/SINGULARITY/i);
  });

  it('renders the main lab cards', () => {
    renderPage();
    expect(screen.getByText('Quantum Cognition')).toBeInTheDocument();
    // The Forge Créative and Cognition Core sections have been removed, so their
    // cards (e.g. Manga Lab, Archetype Nexus) are intentionally no longer shown.
    expect(screen.queryByText('Manga Lab')).not.toBeInTheDocument();
    expect(screen.queryByText('Archetype Nexus')).not.toBeInTheDocument();
  });

  it('renders links pointing to lab routes', () => {
    renderPage();
    const quantumLink = screen.getByText('Quantum Cognition').closest('a');
    expect(quantumLink).toHaveAttribute('href', '/lab/quantum/');
  });

  it('renders the catalogue secondary link for multiverse', () => {
    const { container } = renderPage();
    const catalogue = container.querySelector('a[href="/multiverse/catalog/"]');
    expect(catalogue).toBeInTheDocument();
    expect(catalogue).toHaveTextContent(/Catalogue/i);
  });

  it('no longer links to the removed forge/cognition hubs', () => {
    const { container } = renderPage();
    expect(container.querySelector('a[href="/lab/forge-hub/"]')).not.toBeInTheDocument();
    expect(container.querySelector('a[href="/lab/cognition-hub/"]')).not.toBeInTheDocument();
  });
});
