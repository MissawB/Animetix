import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import XaiReportDisplay from '../XaiReportDisplay';
import type { XaiReport } from '../../types';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren<React.HTMLAttributes<HTMLDivElement>>) => (
      <div {...props}>{children}</div>
    ),
  },
  AnimatePresence: ({ children }: React.PropsWithChildren<unknown>) => <>{children}</>,
}));

vi.mock('../ui/Card', () => ({
  Card: ({ children }: React.PropsWithChildren<unknown>) => <div>{children}</div>,
}));

vi.mock('../ui/Badge', () => ({
  Badge: ({ children }: React.PropsWithChildren<unknown>) => <span>{children}</span>,
}));

const fullReport: XaiReport = {
  query_intent: 'Who is the strongest character?',
  final_confidence: 0.85,
  uncertainty: {
    confidence_score: 0.85,
    is_reliable: true,
    perplexity: 3.21,
    action_required: 'none_required',
    method: 'self_consistency',
  },
  retrieval_attribution: [
    {
      title: 'Power Levels Wiki',
      contribution_weight: 0.4,
      relevance_score: 0.9,
      document_id: 'doc-1',
    },
  ],
  internal_diagnostics: {
    attention_heatmap: [[0.1]],
    top_influential_tokens: ['strongest', 'power'],
    logit_lens_trajectory: [
      { layer: 5, top_tokens: ['Goku'], internal_probabilities: [0.7] },
    ],
  },
};

describe('XaiReportDisplay', () => {
  it('renders nothing when no report is provided', () => {
    const { container } = render(<XaiReportDisplay xaiReport={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders the collapsed header by default', () => {
    render(<XaiReportDisplay xaiReport={fullReport} />);
    expect(screen.getByText('Diagnostics XAI Avancés')).toBeInTheDocument();
    expect(screen.getByRole('button')).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByText('Intention de la Requête')).not.toBeInTheDocument();
  });

  it('expands to show diagnostics when the header is clicked', () => {
    render(<XaiReportDisplay xaiReport={fullReport} />);
    fireEvent.click(screen.getByRole('button'));

    expect(screen.getByRole('button')).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('Confiance Finale: 85.0%')).toBeInTheDocument();
    expect(screen.getByText('Fiable')).toBeInTheDocument();
    expect(screen.getByText('Perplexité: 3.21')).toBeInTheDocument();
    expect(screen.getByText('Who is the strongest character?')).toBeInTheDocument();
    expect(screen.getByText('Power Levels Wiki')).toBeInTheDocument();
    expect(screen.getByText('strongest')).toBeInTheDocument();
    expect(screen.getByText('Goku (70.0%)')).toBeInTheDocument();
  });

  it('shows the verification-recommended badge when not reliable', () => {
    const report: XaiReport = {
      ...fullReport,
      uncertainty: {
        confidence_score: 0.2,
        is_reliable: false,
        perplexity: null,
        action_required: 'human_review',
        method: 'mc_dropout',
      },
    };
    render(<XaiReportDisplay xaiReport={report} />);
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByText('Vérification Recommandée')).toBeInTheDocument();
    // perplexity null -> the perplexity badge is omitted
    expect(screen.queryByText(/Perplexité:/)).not.toBeInTheDocument();
  });
});
