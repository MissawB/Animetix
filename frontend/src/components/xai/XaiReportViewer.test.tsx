import { render, screen } from '@testing-library/react';
import { XaiReportViewer } from './XaiReportViewer';
import { describe, it, expect } from 'vitest';

const mockReport = {
  query_intent: 'Test Intent',
  final_confidence: 0.85,
  agent_trace: [
    { agent: 'Test Agent', thought: 'Thinking about testing' }
  ],
  retrieval_attribution: [
    { title: 'Source 1', contribution_weight: 0.6 }
  ],
  internal_diagnostics: {
    top_influential_tokens: ['test', 'unit']
  }
};

describe('XaiReportViewer', () => {
  it('renders correctly with all fields', () => {
    render(<XaiReportViewer report={mockReport as any} />);
    
    // Header
    expect(screen.getByText('Test Intent')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
    
    // Agent Trace
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
    expect(screen.getByText('Thinking about testing')).toBeInTheDocument();
    
    // Source Attribution
    expect(screen.getByText('Source 1')).toBeInTheDocument();
    expect(screen.getByText('60%')).toBeInTheDocument();
    
    // Influential Tokens
    expect(screen.getByText('test')).toBeInTheDocument();
    expect(screen.getByText('unit')).toBeInTheDocument();
  });

  it('handles missing optional fields gracefully', () => {
    const minimalReport = {
      query_intent: 'Minimal Intent',
      final_confidence: 0.5,
    };
    
    render(<XaiReportViewer report={minimalReport as any} />);
    
    expect(screen.getByText('Minimal Intent')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
    
    // These should not be present
    expect(screen.queryByText('Agent Trace')).not.toBeInTheDocument();
    expect(screen.queryByText('Source Attribution')).not.toBeInTheDocument();
    expect(screen.queryByText('Influential Tokens')).not.toBeInTheDocument();
  });
});
