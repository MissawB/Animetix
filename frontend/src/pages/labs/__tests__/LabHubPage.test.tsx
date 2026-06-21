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
  it('renders the header and section titles', () => {
    renderPage();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/SINGULARITY/i);
    const sectionHeadings = screen.getAllByRole('heading', { level: 2 });
    const headingText = sectionHeadings.map((h) => h.textContent).join(' ');
    expect(headingText).toMatch(/FORGE/i);
    expect(headingText).toMatch(/COGNITION/i);
  });

  it('renders lab cards from every section', () => {
    renderPage();
    expect(screen.getByText('Quantum Cognition')).toBeInTheDocument();
    expect(screen.getByText('Manga Lab')).toBeInTheDocument();
    expect(screen.getByText('Archetype Nexus')).toBeInTheDocument();
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

  it('renders the hub navigation links', () => {
    const { container } = renderPage();
    expect(container.querySelector('a[href="/forge-hub/"]')).toBeInTheDocument();
    expect(container.querySelector('a[href="/cognition-hub/"]')).toBeInTheDocument();
  });
});
