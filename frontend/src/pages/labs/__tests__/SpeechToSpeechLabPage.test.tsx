import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Unauthenticated → connectWebSocket() hits the auth gate and returns before
// ever constructing a WebSocket, so the render test never touches the (jsdom-
// absent) WebSocket / getUserMedia APIs.
vi.mock('../../../store/authStore', () => ({
  useAuthStore: { getState: () => ({ isAuthenticated: false }) },
}));
vi.mock('../../../utils/firebase', () => ({ auth: { currentUser: null } }));

const profile = {
  id: 7,
  name: 'Kana Hanazawa',
  language: 'japanese',
  roles: 'Nadeko',
  definition: 'Iconic seiyuu.',
};

import SpeechToSpeechLabPage from '../SpeechToSpeechLabPage';

const renderPage = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <SpeechToSpeechLabPage />
    </QueryClientProvider>,
  );
};

describe('SpeechToSpeechLabPage', () => {
  beforeEach(() => {
    global.fetch = vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve({ results: [profile] }) }),
    ) as unknown as typeof fetch;
  });

  it('renders the casting sidebar, live console and guide', async () => {
    renderPage();

    // Header
    expect(screen.getByText(/SPEECH-TO-SPEECH/i)).toBeInTheDocument();
    // Casting sidebar
    expect(screen.getByText('Casting Persona')).toBeInTheDocument();
    expect(screen.getByText('Gemini Native Voice')).toBeInTheDocument();
    // Live console
    expect(screen.getByText(/Transcription en Direct/i)).toBeInTheDocument();
    // Guide
    expect(screen.getByText(/Guide du Live/i)).toBeInTheDocument();
    // A fetched profile shows up in the casting list
    expect(await screen.findByText('Kana Hanazawa')).toBeInTheDocument();
  });
});
