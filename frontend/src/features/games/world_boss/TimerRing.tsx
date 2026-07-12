import React from 'react';
import { useTranslation } from 'react-i18next';

interface Props {
  seconds: number;
  onExpire: () => void;
  paused: boolean;
}

const CIRCUMFERENCE = 2 * Math.PI * 44;

/**
 * The clock, as a ring that closes in. It is decor: the server decides whether an
 * answer was late. What it must do is make the last three seconds feel like three.
 */
export const TimerRing: React.FC<Props> = ({ seconds, onExpire, paused }) => {
  const { t } = useTranslation();
  const [left, setLeft] = React.useState(seconds);
  const [prevSeconds, setPrevSeconds] = React.useState(seconds);
  const fired = React.useRef(false);

  // A fresh question hands us a fresh `seconds` budget — reset the countdown
  // to match. Adjusted during render (React's supported pattern for deriving
  // state from a changed prop, see react.dev/learn/you-might-not-need-an-effect)
  // rather than in an effect body, so it lands in the same render instead of
  // flashing the old value for a tick, and so the lint gate (no synchronous
  // setState in an effect) stays clean. `fired` is a ref, not state — refs
  // can't be touched during render, so its reset lives in the effect below.
  if (seconds !== prevSeconds) {
    setPrevSeconds(seconds);
    setLeft(seconds);
  }

  React.useEffect(() => {
    fired.current = false;
  }, [seconds]);

  React.useEffect(() => {
    if (paused) return undefined;
    const id = setInterval(() => setLeft((n) => Math.max(0, n - 1)), 1000);
    return () => clearInterval(id);
  }, [paused, seconds]);

  React.useEffect(() => {
    if (left === 0 && !paused && !fired.current) {
      fired.current = true;
      onExpire();
    }
  }, [left, paused, onExpire]);

  const ratio = seconds > 0 ? left / seconds : 0;
  const urgent = left <= 3;

  return (
    <div className="relative w-24 h-24" aria-live="polite">
      <svg viewBox="0 0 96 96" className="w-full h-full -rotate-90">
        <circle cx="48" cy="48" r="44" strokeWidth="6" fill="none" className="stroke-white/10" />
        <circle
          cx="48"
          cy="48"
          r="44"
          strokeWidth="6"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={CIRCUMFERENCE * (1 - ratio)}
          className={`transition-[stroke-dashoffset] duration-1000 ease-linear ${
            urgent ? 'stroke-red-500' : 'stroke-amber-400'
          }`}
        />
      </svg>
      <span
        className={`absolute inset-0 grid place-items-center font-mono font-black text-2xl ${
          urgent ? 'text-red-500' : 'text-white'
        }`}
      >
        {left}
      </span>
      <span className="sr-only">{t('games.world_boss.seconds_left', '{{n}} s', { n: left })}</span>
    </div>
  );
};
