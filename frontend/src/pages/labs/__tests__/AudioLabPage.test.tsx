import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';

const seiyuu = {
  id: 1,
  name: 'Mamoru Miyano',
  language: 'japanese',
  origin: 'dataset',
  roles: 'Light Yagami',
  definition: 'Legendary seiyuu.',
  sample_url: 'http://example.test/sample.wav',
};

vi.mock('../../../features/labs/hooks/useAudioLab', () => ({
  useAudioLab: () => ({
    data: null,
    loading: false,
    processAudio: vi.fn(),
    searchSeiyuu: vi.fn(),
    ingestVoice: vi.fn(),
    seiyuuResults: [seiyuu],
    isSearchingSeiyuu: false,
    isIngestingVoice: false,
  }),
}));

vi.mock('../../../features/labs/hooks/useQuickIngestForm', () => ({
  useQuickIngestForm: () => ({
    toggle: vi.fn(),
    isOpen: false,
    submit: vi.fn(),
    name: '',
    setName: vi.fn(),
    language: 'japanese',
    setLanguage: vi.fn(),
    source: '',
    setSource: vi.fn(),
    error: null,
    close: vi.fn(),
  }),
}));

import AudioLabPage from '../AudioLabPage';

describe('AudioLabPage', () => {
  it('renders the recording panel, voice database with a seiyuu card, and the guide', () => {
    render(
      <MemoryRouter>
        <AudioLabPage />
      </MemoryRouter>,
    );

    // Recording panel — idle status
    expect(screen.getByText(/Prêt à enregistrer/i)).toBeInTheDocument();
    // Voice Database sidebar heading
    expect(screen.getByText(/Database/)).toBeInTheDocument();
    // A seiyuu profile card (from the mocked results)
    expect(screen.getByText('Mamoru Miyano')).toBeInTheDocument();
    // Guide section
    expect(screen.getByText(/Guide de la Forge Vocale/i)).toBeInTheDocument();
  });
});
