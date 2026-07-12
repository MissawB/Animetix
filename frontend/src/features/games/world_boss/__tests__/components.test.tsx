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
    render(<TimerRing questionId="q1" seconds={3} onExpire={onExpire} paused={false} />);

    expect(screen.getByText('3')).toBeInTheDocument();
    act(() => {
      vi.advanceTimersByTime(4000);
    });

    expect(onExpire).toHaveBeenCalledTimes(1);
  });

  it('does not fire while paused', () => {
    const onExpire = vi.fn();
    render(<TimerRing questionId="q1" seconds={1} onExpire={onExpire} paused />);
    vi.advanceTimersByTime(5000);
    expect(onExpire).not.toHaveBeenCalled();
  });

  it('restarts the countdown for a new question even when the band timer (seconds) is unchanged', () => {
    // Regression: band A is 20s for every tier in the band, so two consecutive
    // questions in the same band share `seconds`. Without a question-keyed
    // reset the ring stays frozen at 0 after the first question expires.
    const onExpire = vi.fn();
    const { rerender } = render(
      <TimerRing questionId="q1" seconds={3} onExpire={onExpire} paused={false} />,
    );

    act(() => {
      vi.advanceTimersByTime(4000);
    });
    expect(onExpire).toHaveBeenCalledTimes(1);
    expect(screen.getByText('0')).toBeInTheDocument();

    // A new question lands, same band, same `seconds` budget, different question.
    rerender(<TimerRing questionId="q2" seconds={3} onExpire={onExpire} paused={false} />);
    expect(screen.getByText('3')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(4000);
    });
    expect(onExpire).toHaveBeenCalledTimes(2);
  });

  it('does not restart when the same pending question is re-issued verbatim', () => {
    // The backend re-issues the SAME pending question if asked again inside its
    // own timer. That must not reset the ring the player is already watching.
    const onExpire = vi.fn();
    const { rerender } = render(
      <TimerRing questionId="q1" seconds={5} onExpire={onExpire} paused={false} />,
    );

    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(screen.getByText('3')).toBeInTheDocument();

    // Same question, same timer budget, re-rendered (e.g. a parent re-render).
    rerender(<TimerRing questionId="q1" seconds={5} onExpire={onExpire} paused={false} />);
    expect(screen.getByText('3')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(3000);
    });
    expect(onExpire).toHaveBeenCalledTimes(1);
  });

  it('hides the visible numeral from assistive tech so the live region only announces once', () => {
    const onExpire = vi.fn();
    render(<TimerRing questionId="q1" seconds={3} onExpire={onExpire} paused={false} />);

    expect(screen.getByText('3')).toHaveAttribute('aria-hidden', 'true');
    expect(screen.getByText(/3 s/)).not.toHaveAttribute('aria-hidden');
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

  it('locks the options while an answer is in flight, even though there is no verdict yet', async () => {
    // The page disables Start/Next during `phase === 'answering'` (the server
    // round trip) — the options need the same treatment, otherwise a click on
    // a different option during that window updates the locally highlighted
    // "your pick" without it being the answer actually sent.
    const onPick = vi.fn();
    render(<QuestionCard question={QUESTION} verdict={null} onPick={onPick} locked />);

    const button = screen.getByRole('button', { name: '1998' });
    expect(button).toBeDisabled();
    await userEvent.click(button);
    expect(onPick).not.toHaveBeenCalled();
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

  it("marks the player's own wrong pick distinctly from both the correct answer and the untouched options", async () => {
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
    const { rerender } = render(
      <QuestionCard question={QUESTION} verdict={null} onPick={onPick} />,
    );

    // The player picks the wrong option ('2004', index 3) — not the same wrong
    // option as another player might pick ('2001', index 2).
    await userEvent.click(screen.getByRole('button', { name: '2004' }));
    rerender(<QuestionCard question={QUESTION} verdict={verdict} onPick={onPick} />);

    expect(screen.getByRole('button', { name: '1998' })).toHaveAttribute('data-state', 'correct');
    expect(screen.getByRole('button', { name: '2004' })).toHaveAttribute(
      'data-state',
      'wrong-picked',
    );
    expect(screen.getByRole('button', { name: '2001' })).toHaveAttribute(
      'data-state',
      'wrong-other',
    );
    expect(screen.getByRole('button', { name: '1996' })).toHaveAttribute(
      'data-state',
      'wrong-other',
    );
  });

  it('forgets the previous pick once a new question is handed to it', async () => {
    const onPick = vi.fn();
    const verdict = {
      correct: true,
      late: false,
      damage_dealt: 4,
      correct_index: 2,
      correct_label: '2001',
      subject: 'Next question',
      tier: 4,
      run_damage: 7,
      best_tier: 4,
      limiter_break: false,
      streak: 1,
      boss: { current_hp: 8, total_hp: 10, current_phase: 1, is_active: true },
    };
    const NEXT_QUESTION = { ...QUESTION, prompt: 'Another one entirely' };

    const { rerender } = render(
      <QuestionCard question={QUESTION} verdict={null} onPick={onPick} />,
    );
    await userEvent.click(screen.getByRole('button', { name: '2004' }));

    // A brand-new question arrives before any verdict on the old one lands.
    rerender(<QuestionCard question={NEXT_QUESTION} verdict={null} onPick={onPick} />);
    // ...and its own verdict comes back marking a *different* index correct.
    rerender(<QuestionCard question={NEXT_QUESTION} verdict={verdict} onPick={onPick} />);

    // The stale pick from the previous question must not resurface as
    // "wrong-picked" on an option that was never clicked for this question.
    expect(screen.getByRole('button', { name: '2004' })).toHaveAttribute(
      'data-state',
      'wrong-other',
    );
  });
});
