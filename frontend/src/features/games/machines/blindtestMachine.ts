import { setup, assign, fromPromise } from 'xstate';
import { blindtestService } from '../services/blindtestService';
import { BlindtestState } from '../../../types';

export const blindtestMachine = setup({
  types: {
    context: {} as {
      gameState: BlindtestState | null;
      error: string | null;
    },
    events: {} as
      | { type: 'GUESS'; guess: string }
      | { type: 'RESTART' },
  },
  actors: {
    loadGame: fromPromise(async () => {
      try {
        return await blindtestService.getState();
      } catch {
        return await blindtestService.startGame();
      }
    }),
    submitGuess: fromPromise(async ({ input }: { input: { guess: string } }) => {
      return await blindtestService.submitGuess(input.guess);
    }),
    restartGame: fromPromise(async () => {
      return await blindtestService.startGame();
    })
  }
}).createMachine({
  id: 'blindtest',
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
          if (event.type === 'GUESS') return { guess: event.guess };
          return { guess: '' };
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
        RESTART: { target: 'restarting' }
      }
    },
    restarting: {
      invoke: {
        src: 'restartGame',
        onDone: {
          target: 'playing',
          actions: assign({ gameState: ({ event }) => event.output })
        },
        onError: {
          target: 'error',
          actions: assign({ error: ({ event }) => (event.error as Error).message })
        }
      }
    },
    error: {
      on: {
        RESTART: { target: 'initializing' }
      }
    }
  }
});
