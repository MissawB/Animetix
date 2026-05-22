import { setup, assign, fromPromise } from 'xstate';
import { paradoxService } from '../services/paradoxService';
import { ParadoxState } from '../../../types';

export const paradoxMachine = setup({
  types: {
    context: {} as {
      gameState: ParadoxState | null;
      error: string | null;
    },
    events: {} as
      | { type: 'GUESS'; itemId: number }
      | { type: 'RESTART' },
  },
  actors: {
    loadGame: fromPromise(async () => {
      try {
        return await paradoxService.getState();
      } catch {
        // En cas d'erreur ou si pas de jeu, on en démarre un (pattern observé dans les autres jeux)
        // Mais ici le service n'a pas de start explicite dans le code lu précédemment, 
        // ou il est géré différemment. Je me base sur le pattern API standard.
        const res = await fetch('/api/v1/game/paradox/start/', { method: 'POST' });
        return res.json();
      }
    }),
    submitGuess: fromPromise(async ({ input }: { input: { itemId: number } }) => {
      return await paradoxService.submit({ guess: input.itemId });
    })
  }
}).createMachine({
  id: 'paradox',
  initial: 'initializing',
  context: {
    gameState: null,
    error: null,
  },
  states: {
    initializing: {
      invoke: {
        src: 'loadGame',
        onDone: {
          target: 'checkState',
          actions: assign({ gameState: ({ event }) => event.output })
        },
        onError: {
          target: 'error',
          actions: assign({ error: ({ event }) => (event.error as Error).message })
        }
      }
    },
    checkState: {
      always: [
        { guard: ({ context }) => context.gameState?.gameOver === true, target: 'gameOver' },
        { target: 'playing' }
      ]
    },
    playing: {
      on: {
        GUESS: { target: 'submitting' }
      }
    },
    submitting: {
      invoke: {
        src: 'submitGuess',
        input: ({ event }) => {
          if (event.type === 'GUESS') return { itemId: event.itemId };
          return { itemId: 0 };
        },
        onDone: {
          target: 'checkState',
          actions: assign({ gameState: ({ event }) => event.output })
        },
        onError: {
          target: 'error',
          actions: assign({ error: ({ event }) => (event.error as Error).message })
        }
      }
    },
    gameOver: {
      on: {
        RESTART: { target: 'initializing' }
      }
    },
    error: {
      on: {
        RESTART: { target: 'initializing' }
      }
    }
  }
});
