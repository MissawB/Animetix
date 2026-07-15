import '@testing-library/jest-dom';
import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AIFeedbackHistoryPage from '../AIFeedbackHistoryPage';
import { labService } from '../../../features/labs/services/labService';
import { AIFeedback } from '../../../types';

vi.mock('../../../features/labs/services/labService', () => ({
  labService: {
    getAIFeedbackHistory: vi.fn(),
  },
}));

const mockedGetHistory = vi.mocked(labService.getAIFeedbackHistory);

const renderPage = () =>
  render(
    <MemoryRouter>
      <AIFeedbackHistoryPage />
    </MemoryRouter>,
  );

const feedback = (overrides: Partial<AIFeedback>): AIFeedback => ({
  id: 1,
  user: 1,
  username: 'tester',
  feedback_type: 'CHAT',
  input_context: 'What is the meaning of life?',
  output_text: '42',
  is_positive: true,
  created_at: '2024-05-01T10:00:00Z',
  ...overrides,
});

describe('AIFeedbackHistoryPage', () => {
  beforeEach(() => {
    mockedGetHistory.mockReset();
  });

  it('renders loading state initially', () => {
    mockedGetHistory.mockReturnValue(new Promise(() => {}));
    renderPage();
    expect(screen.getByText(/Accès à l'archive neuronale/i)).toBeInTheDocument();
  });

  it('renders empty state when no feedback', async () => {
    mockedGetHistory.mockResolvedValue([]);
    renderPage();
    expect(
      await screen.findByText(/Vous n'avez pas encore soumis de feedback/i),
    ).toBeInTheDocument();
  });

  it('renders populated feedback list with positive and negative entries', async () => {
    mockedGetHistory.mockResolvedValue([
      feedback({ id: 1, is_positive: true, input_context: 'Positive query' }),
      feedback({ id: 2, is_positive: false, input_context: 'Negative query' }),
    ]);
    renderPage();
    expect(await screen.findByText('Positive query')).toBeInTheDocument();
    expect(screen.getByText('Negative query')).toBeInTheDocument();
    expect(screen.getByText('HISTORIQUE DES FEEDBACKS IA')).toBeInTheDocument();
  });

  it('handles fetch error gracefully and shows empty state', async () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockedGetHistory.mockRejectedValue(new Error('boom'));
    renderPage();
    expect(
      await screen.findByText(/Vous n'avez pas encore soumis de feedback/i),
    ).toBeInTheDocument();
    errorSpy.mockRestore();
  });
});
