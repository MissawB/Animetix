import { setup, assign, fromPromise } from 'xstate';
import { visionService } from '../services/visionService';
import { VisionState } from '../../../types';

export const visionMachine = setup({
  types: {
    context: {} as {
      gameState: VisionState | null;
      error: string | null;
    },
    events: {} as
      | { type: 'GUESS'; description: string }
      | { type: 'RESTART' },
  },
  actors: {
    loadGame: fromPromise(async () => {
      try {
        return await visionService.getState();
      } catch {
        return await visionService.startGame();
      }
    }),
    submitGuess: fromPromise(async ({ input }: { input: { description: string } }) => {
      return await visionService.submitGuess(input.description);
    }),
    restartGame: fromPromise(async () => {
      return await visionService.startGame();
    })
  }
}).createMachine({
  id: 'vision',
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
          if (event.type === 'GUESS') return { description: event.description };
          return { description: '' };
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
