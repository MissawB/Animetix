import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import React from 'react';
import { TimerRing } from '../TimerRing';
import { TierLadder } from '../TierLadder';
import { QuestionCard } from '../QuestionCard';

const QUESTION = {
  tier: 3,
  band: 'A' as const,
  timer: 20,
  damage: 4,
  limiter_break: false,
  streak: 0,
  run_damage: 3,
  best_tier: 2,
  archetype: 'year',
  prompt: 'En quelle année est sortie « Cowboy Bebop » ?',
  options: ['1996', '1998', '2001', '2004'],
  image: null,
};

describe('TimerRing', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('counts down and fires once at zero', () => {
    const onExpire = vi.fn();
    render(<TimerRing seconds={3} onExpire={onExpire} paused={false} />);

    expect(screen.getByText('3')).toBeInTheDocument();
    act(() => {
      vi.advanceTimersByTime(4000);
    });

    expect(onExpire).toHaveBeenCalledTimes(1);
  });

  it('does not fire while paused', () => {
    const onExpire = vi.fn();
    render(<TimerRing seconds={1} onExpire={onExpire} paused />);
    vi.advanceTimersByTime(5000);
    expect(onExpire).not.toHaveBeenCalled();
  });
});

describe('TierLadder', () => {
  it('shows the doubling damage, and lights the rung the player is on', () => {
    render(<TierLadder tier={3} limiterBreak={false} />);

    expect(screen.getByText('2048')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByLabelText(/palier 3/i)).toHaveAttribute('data-current', 'true');
  });

  it('announces the limiter break', () => {
    render(<TierLadder tier={12} limiterBreak />);
    expect(screen.getByText(/brisage de limiteur/i)).toBeInTheDocument();
    expect(screen.getByText('4096')).toBeInTheDocument();
  });
});

describe('QuestionCard', () => {
  it('renders the four options and reports the one clicked', async () => {
    const onPick = vi.fn();
    render(<QuestionCard question={QUESTION} verdict={null} onPick={onPick} />);

    await userEvent.click(screen.getByRole('button', { name: '1998' }));

    expect(onPick).toHaveBeenCalledWith(1);
    expect(screen.getAllByRole('button')).toHaveLength(4);
  });

  it('marks the right answer once the verdict is in, and locks the buttons', async () => {
    const onPick = vi.fn();
    const verdict = {
      correct: false,
      late: false,
      damage_dealt: 0,
      correct_index: 1,
      correct_label: '1998',
      subject: 'Cowboy Bebop',
      tier: 1,
      run_damage: 0,
      best_tier: 2,
      limiter_break: false,
      streak: 0,
      boss: { current_hp: 9, total_hp: 10, current_phase: 1, is_active: true },
    };
    render(<QuestionCard question={QUESTION} verdict={verdict} onPick={onPick} />);

    expect(screen.getByRole('button', { name: '1998' })).toHaveAttribute('data-state', 'correct');
    await userEvent.click(screen.getByRole('button', { name: '2004' }));
    expect(onPick).not.toHaveBeenCalled();
  });
});
