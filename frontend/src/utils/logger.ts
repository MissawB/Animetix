/* eslint-disable no-console */
// Dev-only logger. No-ops in production builds (import.meta.env.DEV is false), so
// diagnostic chatter (WebSocket lifecycle, realtime events, …) stays out of the
// prod console. For real problems use console.warn / console.error directly —
// those are allowed by the no-console ESLint rule.
const isDev = import.meta.env.DEV;

export const logger = {
  log: (...args: unknown[]): void => {
    if (isDev) console.log(...args);
  },
  debug: (...args: unknown[]): void => {
    if (isDev) console.debug(...args);
  },
};
