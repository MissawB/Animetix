import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import NeuralDiagnosticsPage from '../NeuralDiagnosticsPage';

interface DiagnosticsData {
  avg_entropy?: number;
  confidence_score: number;
  per_token_diagnostics: unknown[];
  logit_lens_trajectory: unknown[];
}

interface DiagnosticsHook {
  runDiagnostic: (prompt: string) => Promise<void>;
  loading: boolean;
  data: DiagnosticsData | undefined;
  error: Error | null;
}

const runDiagnostic = vi.fn<(prompt: string) => Promise<void>>(() => Promise.resolve());
let hookValue: DiagnosticsHook;

vi.mock('../../../features/labs/hooks/useNeuralDiagnostics', () => ({
  useNeuralDiagnostics: () => hookValue,
}));

vi.mock('../../../features/labs/components/EntropyBarChart', () => ({
  default: () => <div data-testid="entropy-chart" />,
}));

vi.mock('../../../features/labs/components/LogitLensHeatmap', () => ({
  default: () => <div data-testid="logit-heatmap" />,
}));

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren<React.HTMLAttributes<HTMLDivElement>>) => (
      <div {...props}>{children}</div>
    ),
  },
  AnimatePresence: ({ children }: React.PropsWithChildren<unknown>) => <>{children}</>,
}));

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <NeuralDiagnosticsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe('NeuralDiagnosticsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hookValue = { runDiagnostic, loading: false, data: undefined, error: null };
  });

  it('renders the idle state with empty visualizations placeholders', () => {
    renderPage();
    expect(screen.getByLabelText('labs.diagnostics.input_prompt')).toBeInTheDocument();
    expect(screen.getByText('labs.diagnostics.waiting_data')).toBeInTheDocument();
    expect(screen.getByText('labs.diagnostics.synaptic_mapping')).toBeInTheDocument();
  });

  it('disables the run button when the prompt is empty', () => {
    renderPage();
    expect(screen.getByText('labs.diagnostics.run_diagnostic').closest('button')).toBeDisabled();
  });

  it('runs the diagnostic with the entered prompt', async () => {
    renderPage();
    fireEvent.change(screen.getByLabelText('labs.diagnostics.input_prompt'), {
      target: { value: 'analyse this' },
    });
    fireEvent.click(screen.getByText('labs.diagnostics.run_diagnostic'));
    await waitFor(() => expect(runDiagnostic).toHaveBeenCalledWith('analyse this'));
  });

  it('renders the loading spinners', () => {
    hookValue = { runDiagnostic, loading: true, data: undefined, error: null };
    renderPage();
    expect(screen.getByText('labs.diagnostics.analyzing')).toBeInTheDocument();
    expect(screen.getByText('labs.diagnostics.processing_layers')).toBeInTheDocument();
  });

  it('renders the error banner', () => {
    hookValue = { runDiagnostic, loading: false, data: undefined, error: new Error('boom') };
    renderPage();
    expect(screen.getByText('labs.diagnostics.error')).toBeInTheDocument();
  });

  it('renders metrics and visualizations when data is present', () => {
    hookValue = {
      runDiagnostic,
      loading: false,
      data: {
        avg_entropy: 1.2345,
        confidence_score: 0.873,
        per_token_diagnostics: [{}],
        logit_lens_trajectory: [{}],
      },
      error: null,
    };
    renderPage();
    expect(screen.getByText('1.2345')).toBeInTheDocument();
    expect(screen.getByText('87.3%')).toBeInTheDocument();
    expect(screen.getByTestId('entropy-chart')).toBeInTheDocument();
    expect(screen.getByTestId('logit-heatmap')).toBeInTheDocument();
  });
});
