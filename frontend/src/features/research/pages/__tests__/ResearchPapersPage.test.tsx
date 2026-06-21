import '@testing-library/jest-dom';
import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ResearchPapersPage from '../ResearchPapersPage';
import type { ResearchPaper } from '../../data/papers';

interface MotionProps {
  children?: React.ReactNode;
  layout?: unknown;
  initial?: unknown;
  animate?: unknown;
  exit?: unknown;
  transition?: unknown;
  className?: string;
}

const strip = (props: MotionProps) => {
  const { children, layout, initial, animate, exit, transition, ...rest } = props;
  void layout;
  void initial;
  void animate;
  void exit;
  void transition;
  return { rest, children };
};

vi.mock('framer-motion', () => ({
  motion: {
    div: (props: MotionProps) => {
      const { rest, children } = strip(props);
      return <div {...rest}>{children}</div>;
    },
  },
  AnimatePresence: ({ children }: { children?: React.ReactNode }) => <>{children}</>,
}));

const papers: ResearchPaper[] = [
  {
    id: 'p1',
    title: 'Deep Reasoning Networks',
    source: 'arXiv:0001',
    url: 'https://example.com/1',
    keyConcept: 'Chain of thought reasoning',
    implementation: 'Used in our thinking engine.',
    category: 'reasoning',
  },
  {
    id: 'p2',
    title: 'Agentic Game Playing',
    source: 'arXiv:0002',
    url: 'https://example.com/2',
    keyConcept: 'Self-play agents',
    implementation: 'Powers the VS battle mode.',
    category: 'agents',
  },
];

vi.mock('../../data/papers', () => ({
  get researchPapers() {
    return papers;
  },
}));

describe('ResearchPapersPage', () => {
  it('renders header and all papers initially', () => {
    render(<ResearchPapersPage />);
    expect(screen.getByText(/LABO DE/i)).toBeInTheDocument();
    expect(screen.getByText('Deep Reasoning Networks')).toBeInTheDocument();
    expect(screen.getByText('Agentic Game Playing')).toBeInTheDocument();
  });

  it('filters the list by search query (title match)', () => {
    render(<ResearchPapersPage />);
    const input = screen.getByLabelText('Rechercher un concept ou un papier');
    fireEvent.change(input, { target: { value: 'Agentic' } });
    expect(screen.getByText('Agentic Game Playing')).toBeInTheDocument();
    expect(screen.queryByText('Deep Reasoning Networks')).not.toBeInTheDocument();
  });

  it('filters by key concept and shows empty state when nothing matches', () => {
    render(<ResearchPapersPage />);
    const input = screen.getByLabelText('Rechercher un concept ou un papier');

    fireEvent.change(input, { target: { value: 'self-play' } });
    expect(screen.getByText('Agentic Game Playing')).toBeInTheDocument();

    fireEvent.change(input, { target: { value: 'zzzznomatch' } });
    expect(
      screen.getByText(/Aucun papier trouvé pour cette recherche/i)
    ).toBeInTheDocument();
  });

  it('filters by category tab selection', () => {
    render(<ResearchPapersPage />);
    fireEvent.click(screen.getByText('Agents & Jeux'));
    expect(screen.getByText('Agentic Game Playing')).toBeInTheDocument();
    expect(screen.queryByText('Deep Reasoning Networks')).not.toBeInTheDocument();
  });
});
