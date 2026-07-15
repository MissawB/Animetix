/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { companionService } from '../services/companionService';
import { useCompanionStore } from '../companionStore';

vi.mock('../services/companionService', () => ({
  companionService: {
    interact: vi.fn(),
  },
}));

const mockedInteract = vi.mocked(companionService.interact);

describe('useCompanionStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCompanionStore.setState({
      activeMentor: 'sensei',
      customPersona: '',
      isOpen: false,
      history: [],
      isLoading: false,
      error: null,
    });
  });

  it('initializes with default mentor, closed, empty history', () => {
    const state = useCompanionStore.getState();
    expect(state.activeMentor).toBe('sensei');
    expect(state.isOpen).toBe(false);
    expect(state.history).toEqual([]);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('toggleOpen flips the isOpen flag', () => {
    useCompanionStore.getState().toggleOpen();
    expect(useCompanionStore.getState().isOpen).toBe(true);

    useCompanionStore.getState().toggleOpen();
    expect(useCompanionStore.getState().isOpen).toBe(false);
  });

  it('setMentor changes the active mentor', () => {
    useCompanionStore.getState().setMentor('rival');
    expect(useCompanionStore.getState().activeMentor).toBe('rival');
  });

  it('sendMessage appends the user message then replaces history with API response', async () => {
    mockedInteract.mockResolvedValue({
      response: 'Hello there',
      history: [
        { role: 'user', content: 'Hi' },
        { role: 'assistant', content: 'Hello there' },
      ],
    });

    await useCompanionStore.getState().sendMessage('Hi', 'http://ctx');

    const state = useCompanionStore.getState();
    expect(mockedInteract).toHaveBeenCalledWith('sensei', 'Hi', 'http://ctx', undefined);
    expect(state.history).toEqual([
      { role: 'user', content: 'Hi' },
      { role: 'assistant', content: 'Hello there' },
    ]);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('sendMessage uses the active mentor when sending', async () => {
    useCompanionStore.getState().setMentor('rival');
    mockedInteract.mockResolvedValue({ response: 'ok', history: [] });

    await useCompanionStore.getState().sendMessage('yo', 'http://ctx');

    expect(mockedInteract).toHaveBeenCalledWith('rival', 'yo', 'http://ctx', undefined);
  });

  it('sendMessage forwards the custom persona for the custom mentor', async () => {
    useCompanionStore.getState().setMentor('custom');
    useCompanionStore.getState().setCustomPersona('Tu es un pirate.');
    mockedInteract.mockResolvedValue({ response: 'ok', history: [] });

    await useCompanionStore.getState().sendMessage('yo', 'http://ctx');

    expect(mockedInteract).toHaveBeenCalledWith('custom', 'yo', 'http://ctx', 'Tu es un pirate.');
  });

  it('sendMessage derives a context url from location and document when none given', async () => {
    mockedInteract.mockResolvedValue({ response: 'ok', history: [] });

    await useCompanionStore.getState().sendMessage('what is this page');

    const passedContext = mockedInteract.mock.calls[0][2];
    expect(passedContext).toContain('(Page:');
    expect(passedContext).toContain(window.location.href);
  });

  it('sendMessage keeps the user message in history and records error on failure', async () => {
    mockedInteract.mockRejectedValue(new Error('network down'));

    await useCompanionStore.getState().sendMessage('Hi', 'http://ctx');

    const state = useCompanionStore.getState();
    expect(state.history).toEqual([{ role: 'user', content: 'Hi' }]);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBe('network down');
  });

  it('clearHistory empties the history', () => {
    useCompanionStore.setState({ history: [{ role: 'user', content: 'x' }] });
    useCompanionStore.getState().clearHistory();
    expect(useCompanionStore.getState().history).toEqual([]);
  });
});
