import { useState, type FormEvent } from 'react';
import type { VoiceProfile } from '../../../types';
import type { IngestVoicePayload } from '../services/audioLabService';

interface UseQuickIngestFormArgs {
  ingestVoice: (payload: IngestVoicePayload) => Promise<{ message: string; profile: VoiceProfile }>;
  /** Called with the freshly created profile after a successful ingest. */
  onIngested: (profile: VoiceProfile) => void;
}

/**
 * Owns the "Quick YouTube Ingest" form of the Audio Lab: open/closed state,
 * the three field values, validation and the submit flow. Keeps that cohesive
 * slice out of the page component (which otherwise juggled ~13 useState calls).
 */
export const useQuickIngestForm = ({ ingestVoice, onIngested }: UseQuickIngestFormArgs) => {
  const [isOpen, setIsOpen] = useState(false);
  const [name, setName] = useState('');
  const [language, setLanguage] = useState('japanese');
  const [source, setSource] = useState('');
  const [error, setError] = useState('');

  const toggle = () => setIsOpen((open) => !open);
  const close = () => setIsOpen(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    if (!name || !source) {
      setError('Le nom et la source sont requis.');
      return;
    }
    try {
      const response = await ingestVoice({ name, language, query: source });
      onIngested(response.profile);
      setIsOpen(false);
      setName('');
      setSource('');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '';
      setError(message || "Erreur d'ingestion.");
    }
  };

  return {
    isOpen,
    toggle,
    close,
    name,
    setName,
    language,
    setLanguage,
    source,
    setSource,
    error,
    submit,
  };
};
