import { setup, assign, fromPromise } from 'xstate';
import { akinetixService } from '../services/akinetixService';
import { AkinetixState } from '../../../types';

export const akinetixMachine = setup({
  types: {
    context: {} as {
      gameState: AkinetixState | null;
      error: string | null;
    },
    events: {} as
      | { type: 'ANSWER'; answer: string }
      | { type: 'CONFIRM'; isCorrect: boolean }
      | { type: 'RESTART' },
  },
  actors: {
    loadGame: fromPromise(async () => {
      try {
        return await akinetixService.getState();
      } catch {
        return await akinetixService.startGame();
      }
    }),
    submitAnswer: fromPromise(async ({ input }: { input: { answer: string } }) => {
      return await akinetixService.submitAnswer(input.answer);
    }),
    submitConfirmation: fromPromise(async ({ input }: { input: { isCorrect: boolean } }) => {
      await akinetixService.submitConfirmation(input.isCorrect);
    })
  }
}).createMachine({
  id: 'akinetix',
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
        ANSWER: { target: 'submittingAnswer' }
      }
    },
    submittingAnswer: {
      invoke: {
        src: 'submitAnswer',
        input: ({ event }) => {
          if (event.type === 'ANSWER') return { answer: event.answer };
          return { answer: '' };
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
        CONFIRM: { target: 'confirming' }
      }
    },
    confirming: {
      invoke: {
        src: 'submitConfirmation',
        input: ({ event }) => {
          if (event.type === 'CONFIRM') return { isCorrect: event.isCorrect };
          return { isCorrect: false };
        },
        onDone: {
          target: 'initializing',
          actions: () => window.location.reload()
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
