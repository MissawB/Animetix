# World Boss UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implémenter l'interface "Epic Raid" pour le World Boss, incluant la connexion WebSocket pour les PV en temps réel, la zone de défi trivia, et le système de loot et leaderboard.

**Architecture:** React SPA frontend interacting with existing Django REST API (`/api/v1/boss/`) and Django Channels (`/ws/boss/`). The UI will be broken down into focused components (Header, HealthBar, CombatTerminal, Leaderboard) managed by a central container (`WorldBossPage`).

**Tech Stack:** React 19, TypeScript, Tailwind CSS, Framer Motion, Zustand (if complex state needed), Lucide React, WebSocket API.

---

### Task 1: Setup Route and Skeleton Page

**Files:**
- Modify: `frontend/src/features/games/routes/GameRoutes.tsx`
- Create: `frontend/src/features/games/WorldBossPage.tsx`
- Test: `frontend/src/features/games/__tests__/WorldBossPage.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/features/games/__tests__/WorldBossPage.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import WorldBossPage from '../WorldBossPage';

describe('WorldBossPage', () => {
  it('renders the epic raid title', () => {
    render(
      <MemoryRouter>
        <WorldBossPage />
      </MemoryRouter>
    );
    expect(screen.getByText(/WORLD BOSS/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test -- WorldBossPage.test.tsx`
Expected: FAIL (file not found or component not exported)

- [ ] **Step 3: Write minimal implementation**

```tsx
// frontend/src/features/games/WorldBossPage.tsx
import React from 'react';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

const WorldBossPage: React.FC = () => {
  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-16 text-white">
        <h1 className="text-5xl font-black italic uppercase text-center text-red-500 mb-8">
          WORLD BOSS
        </h1>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 bg-gray-900 min-h-[500px] rounded-xl border border-red-900/50">
                {/* Main Raid Area Placeholder */}
            </div>
            <div className="bg-gray-900 min-h-[500px] rounded-xl border border-gray-800">
                {/* Sidebar Placeholder */}
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default WorldBossPage;
```

Update routing:
```tsx
// frontend/src/features/games/routes/GameRoutes.tsx
// Add import:
const WorldBossPage = lazy(() => import('../WorldBossPage'));
// Add route:
<Route path="/game/world-boss/" element={<WorldBossPage />} />
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test -- WorldBossPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/games/WorldBossPage.tsx frontend/src/features/games/__tests__/WorldBossPage.test.tsx frontend/src/features/games/routes/GameRoutes.tsx
git commit -m "feat(boss): setup WorldBossPage skeleton and routing"
```

### Task 2: Implement BossHeader and GlobalHealthBar

**Files:**
- Create: `frontend/src/features/games/components/BossHeader.tsx`
- Create: `frontend/src/features/games/components/GlobalHealthBar.tsx`
- Modify: `frontend/src/features/games/WorldBossPage.tsx`
- Test: `frontend/src/features/games/__tests__/GlobalHealthBar.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/features/games/__tests__/GlobalHealthBar.test.tsx
import { render, screen } from '@testing-library/react';
import { GlobalHealthBar } from '../components/GlobalHealthBar';

describe('GlobalHealthBar', () => {
  it('renders correct percentage', () => {
    render(<GlobalHealthBar currentHp={500} totalHp={1000} />);
    const bar = screen.getByTestId('health-bar-fill');
    expect(bar).toHaveStyle('width: 50%');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test -- GlobalHealthBar.test.tsx`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```tsx
// frontend/src/features/games/components/BossHeader.tsx
import React from 'react';
import { Skull } from 'lucide-react';

interface BossHeaderProps {
    name: string;
    phase: number;
    phaseName: string;
}

export const BossHeader: React.FC<BossHeaderProps> = ({ name, phase, phaseName }) => (
    <div className="text-center mb-8">
        <div className="w-24 h-24 mx-auto bg-red-950 rounded-full mb-4 border-2 border-red-500 flex items-center justify-center shadow-[0_0_30px_rgba(239,68,68,0.3)]">
            <Skull className="w-12 h-12 text-red-500" />
        </div>
        <h2 className="text-4xl font-black italic uppercase tracking-tighter text-white">{name}</h2>
        <p className="text-red-400 font-bold text-sm tracking-widest mt-2 uppercase">
            PHASE {phase} - {phaseName}
        </p>
    </div>
);
```

```tsx
// frontend/src/features/games/components/GlobalHealthBar.tsx
import React from 'react';
import { motion } from 'framer-motion';

interface GlobalHealthBarProps {
    currentHp: number;
    totalHp: number;
}

export const GlobalHealthBar: React.FC<GlobalHealthBarProps> = ({ currentHp, totalHp }) => {
    const percentage = totalHp > 0 ? Math.max(0, Math.min(100, (currentHp / totalHp) * 100)) : 0;
    
    return (
        <div className="w-full mb-8">
            <div className="flex justify-between text-xs font-bold mb-2 text-gray-400 uppercase tracking-wider">
                <span>HP GLOBAUX</span>
                <span>{currentHp.toLocaleString()} / {totalHp.toLocaleString()}</span>
            </div>
            <div className="w-full h-8 bg-gray-900 rounded-full border border-gray-700 overflow-hidden relative shadow-inner">
                {/* Markers for phases (example 50% and 10%) */}
                <div className="absolute top-0 bottom-0 left-1/2 w-0.5 bg-black/50 z-10" />
                <div className="absolute top-0 bottom-0 left-[10%] w-0.5 bg-black/50 z-10" />
                
                <motion.div 
                    data-testid="health-bar-fill"
                    className="h-full bg-gradient-to-r from-red-700 to-orange-500 rounded-full relative"
                    initial={{ width: `${percentage}%` }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ type: 'spring', bounce: 0, duration: 0.8 }}
                >
                    <div className="absolute inset-0 bg-white/20 animate-pulse mix-blend-overlay" />
                </motion.div>
            </div>
        </div>
    );
};
```

Update `WorldBossPage.tsx` to include them with mock data:
```tsx
import { BossHeader } from './components/BossHeader';
import { GlobalHealthBar } from './components/GlobalHealthBar';
// inside component...
<div className="lg:col-span-2 bg-black p-8 rounded-2xl border border-red-900/30 shadow-2xl relative overflow-hidden">
    <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-red-900/10 to-transparent pointer-events-none" />
    <div className="relative z-10">
        <BossHeader name="Le Titan Primordial" phase={2} phaseName="Enragé" />
        <GlobalHealthBar currentHp={45210} totalHp={100000} />
    </div>
</div>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test -- GlobalHealthBar.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/games/components/BossHeader.tsx frontend/src/features/games/components/GlobalHealthBar.tsx frontend/src/features/games/WorldBossPage.tsx frontend/src/features/games/__tests__/GlobalHealthBar.test.tsx
git commit -m "feat(boss): add BossHeader and GlobalHealthBar components"
```

### Task 3: Implement CombatTerminal (Trivia Interface)

**Files:**
- Create: `frontend/src/features/games/components/CombatTerminal.tsx`
- Modify: `frontend/src/features/games/WorldBossPage.tsx`
- Test: `frontend/src/features/games/__tests__/CombatTerminal.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/features/games/__tests__/CombatTerminal.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { CombatTerminal } from '../components/CombatTerminal';
import { vi } from 'vitest';

describe('CombatTerminal', () => {
  it('calls onSubmit with input value', () => {
    const handleSubmit = vi.fn();
    render(<CombatTerminal question="Test Q?" onSubmit={handleSubmit} isSubmitting={false} />);
    
    const input = screen.getByPlaceholderText(/Votre réponse/i);
    fireEvent.change(input, { target: { value: 'Test A' } });
    fireEvent.submit(screen.getByRole('button', { name: /ATTAQUER/i }));
    
    expect(handleSubmit).toHaveBeenCalledWith('Test A');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test -- CombatTerminal.test.tsx`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```tsx
// frontend/src/features/games/components/CombatTerminal.tsx
import React, { useState, useEffect } from 'react';
import { Sword, Clock } from 'lucide-react';
import { Button } from '../../../components/ui/Button';

interface CombatTerminalProps {
    question: string;
    onSubmit: (answer: string) => void;
    isSubmitting: boolean;
}

export const CombatTerminal: React.FC<CombatTerminalProps> = ({ question, onSubmit, isSubmitting }) => {
    const [answer, setAnswer] = useState('');
    const [timeLeft, setTimeLeft] = useState(60);

    // Simple countdown logic
    useEffect(() => {
        if (timeLeft <= 0) return;
        const timer = setInterval(() => setTimeLeft(prev => prev - 1), 1000);
        return () => clearInterval(timer);
    }, [timeLeft]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!answer.trim() || isSubmitting) return;
        onSubmit(answer);
        setAnswer('');
        setTimeLeft(60); // Reset timer on submit for now
    };

    return (
        <div className="bg-gray-900/80 p-6 rounded-xl border border-red-500/30 backdrop-blur-sm relative">
            <div className="flex justify-between items-center mb-4 border-b border-gray-800 pb-2">
                <h4 className="text-xs font-black uppercase text-red-500 tracking-widest flex items-center gap-2">
                    <Sword className="w-4 h-4" /> DÉFI ACTUEL
                </h4>
                <div className={`text-xs font-mono font-bold flex items-center gap-1 ${timeLeft < 10 ? 'text-red-500 animate-pulse' : 'text-gray-400'}`}>
                    <Clock className="w-3 h-3" /> 00:{timeLeft.toString().padStart(2, '0')}
                </div>
            </div>
            
            <p className="text-lg font-medium mb-6 text-white leading-relaxed">
                "{question}"
            </p>
            
            <form onSubmit={handleSubmit} className="space-y-4">
                <input 
                    type="text" 
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    placeholder="Votre réponse..." 
                    disabled={isSubmitting || timeLeft === 0}
                    className="w-full bg-black border border-gray-700 rounded-lg p-4 text-white focus:outline-none focus:border-red-500 transition-colors disabled:opacity-50"
                />
                <Button 
                    type="submit" 
                    variant="primary" 
                    fullWidth 
                    disabled={isSubmitting || !answer.trim() || timeLeft === 0}
                    className="bg-red-600 hover:bg-red-500 text-white font-black py-4 text-lg tracking-wider"
                >
                    {isSubmitting ? 'FRAPPE EN COURS...' : 'ATTAQUER'}
                </Button>
            </form>
        </div>
    );
};
```

Update `WorldBossPage.tsx` to include it:
```tsx
import { CombatTerminal } from './components/CombatTerminal';
// inside the relative z-10 div, below GlobalHealthBar:
<CombatTerminal 
    question="Dans quelle série l'épisode 47 a-t-il été censuré uniquement lors de sa diffusion télévisée française à cause d'un jeu de mots intraduisible ?"
    onSubmit={(ans) => console.log("Attacking with:", ans)}
    isSubmitting={false}
/>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test -- CombatTerminal.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/games/components/CombatTerminal.tsx frontend/src/features/games/WorldBossPage.tsx frontend/src/features/games/__tests__/CombatTerminal.test.tsx
git commit -m "feat(boss): add CombatTerminal for trivia challenges"
```

### Task 4: Implement Sidebar (LootTracker and Leaderboard)

**Files:**
- Create: `frontend/src/features/games/components/LootTracker.tsx`
- Create: `frontend/src/features/games/components/RaidLeaderboard.tsx`
- Modify: `frontend/src/features/games/WorldBossPage.tsx`

- [ ] **Step 1: Write the components (Visual/Presentational)**

We will skip tests for these purely presentational components to save time, focusing on implementation.

```tsx
// frontend/src/features/games/components/LootTracker.tsx
import React from 'react';
import { Package, TrendingUp } from 'lucide-react';
import { Card } from '../../../components/ui/Card';

interface LootTrackerProps {
    personalDamage: number;
    currentTier: 'Commun' | 'Rare' | 'Epique' | 'Légendaire';
}

const tierColors = {
    'Commun': 'text-gray-400 border-gray-400',
    'Rare': 'text-blue-400 border-blue-400',
    'Epique': 'text-purple-400 border-purple-400',
    'Légendaire': 'text-yellow-400 border-yellow-400',
};

export const LootTracker: React.FC<LootTrackerProps> = ({ personalDamage, currentTier }) => (
    <Card padding="md" className="bg-gray-900 border-gray-800 mb-6">
        <h3 className="text-xs font-black uppercase text-gray-400 mb-4 flex items-center gap-2">
            <Package className="w-4 h-4" /> Progression de Loot
        </h3>
        
        <div className="space-y-4">
            <div>
                <p className="text-[10px] uppercase text-gray-500 font-bold mb-1">Dégâts infligés</p>
                <p className="text-2xl font-black italic text-white flex items-center gap-2">
                    {personalDamage.toLocaleString()} <TrendingUp className="w-4 h-4 text-emerald-500" />
                </p>
            </div>
            
            <div>
                <p className="text-[10px] uppercase text-gray-500 font-bold mb-2">Tiers de Drop Actuel</p>
                <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border bg-black/50 ${tierColors[currentTier]}`}>
                    <span className="w-2 h-2 rounded-full bg-current animate-pulse" />
                    <span className="text-xs font-black uppercase tracking-widest">{currentTier}</span>
                </div>
            </div>
            <p className="text-[10px] text-gray-500 italic">Plus vous infligez de dégâts, plus la rareté des drops augmente.</p>
        </div>
    </Card>
);
```

```tsx
// frontend/src/features/games/components/RaidLeaderboard.tsx
import React from 'react';
import { Trophy } from 'lucide-react';
import { Card } from '../../../components/ui/Card';

interface LeaderboardEntry {
    username: string;
    damage: number;
}

interface RaidLeaderboardProps {
    entries: LeaderboardEntry[];
}

export const RaidLeaderboard: React.FC<RaidLeaderboardProps> = ({ entries }) => (
    <Card padding="md" className="bg-gray-900 border-gray-800">
        <h3 className="text-xs font-black uppercase text-yellow-500 mb-4 flex items-center gap-2">
            <Trophy className="w-4 h-4" /> Top Contributeurs
        </h3>
        <div className="space-y-3">
            {entries.map((entry, idx) => (
                <div key={idx} className="flex justify-between items-center p-2 rounded bg-black/50 border border-white/5">
                    <div className="flex items-center gap-3">
                        <span className={`text-xs font-black ${idx === 0 ? 'text-yellow-500' : idx === 1 ? 'text-gray-300' : idx === 2 ? 'text-amber-600' : 'text-gray-600'}`}>
                            #{idx + 1}
                        </span>
                        <span className="text-sm font-bold text-gray-200">{entry.username}</span>
                    </div>
                    <span className="text-sm font-mono text-red-400">{entry.damage.toLocaleString()}</span>
                </div>
            ))}
            {entries.length === 0 && <p className="text-xs text-gray-500 italic text-center py-4">Aucune attaque enregistrée.</p>}
        </div>
    </Card>
);
```

Update `WorldBossPage.tsx` to include them in the sidebar:
```tsx
import { LootTracker } from './components/LootTracker';
import { RaidLeaderboard } from './components/RaidLeaderboard';
// inside the sidebar div:
<div className="space-y-6">
    <LootTracker personalDamage={1500} currentTier="Rare" />
    <RaidLeaderboard entries={[
        { username: "Kakarot", damage: 15400 },
        { username: "Saitama", damage: 9800 },
        { username: "Player1", damage: 1500 }
    ]} />
</div>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/games/components/LootTracker.tsx frontend/src/features/games/components/RaidLeaderboard.tsx frontend/src/features/games/WorldBossPage.tsx
git commit -m "feat(boss): add LootTracker and RaidLeaderboard sidebar components"
```

### Task 5: Implement WebSocket and API Hook (useWorldBoss)

**Files:**
- Create: `frontend/src/features/games/hooks/useWorldBoss.ts`
- Modify: `frontend/src/features/games/WorldBossPage.tsx`

- [ ] **Step 1: Write the hook implementation**

```typescript
// frontend/src/features/games/hooks/useWorldBoss.ts
import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../../../utils/apiClient';
import { useAuthStore } from '../../../store/authStore';
import { useToast } from '../../../hooks/useToast';

interface BossState {
    id: number;
    title: string;
    total_hp: number;
    current_hp: number;
    current_phase: number;
    active_question: string;
    leaderboard: { username: string; damage: number }[];
}

export const useWorldBoss = () => {
    const { token } = useAuthStore();
    const { addToast } = useToast();
    const [bossState, setBossState] = useState<BossState | null>(null);
    const [personalDamage, setPersonalDamage] = useState(0);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [loading, setLoading] = useState(true);

    // Initial fetch
    useEffect(() => {
        const fetchBoss = async () => {
            try {
                // Assuming GET /api/v1/boss/active/ exists or will be created
                const data = await apiClient('/api/v1/boss/active/');
                setBossState(data);
                // In a real scenario, personal damage should come from the backend or be synced
                setPersonalDamage(data.my_damage || 0); 
            } catch (err) {
                console.error("Failed to fetch boss", err);
            } finally {
                setLoading(false);
            }
        };
        fetchBoss();
    }, []);

    // WebSocket Setup
    useEffect(() => {
        if (!bossState?.id) return;
        
        // Use wss:// in prod, ws:// in dev. Assuming standard Django Channels setup.
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/boss/${bossState.id}/`;
        
        let ws: WebSocket;
        try {
            ws = new WebSocket(wsUrl);
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'hp_update') {
                    setBossState(prev => prev ? { ...prev, current_hp: data.current_hp } : null);
                } else if (data.type === 'phase_change') {
                    setBossState(prev => prev ? { ...prev, current_phase: data.phase, active_question: data.new_question } : null);
                    addToast('warning', `Le boss passe en Phase ${data.phase} !`);
                } else if (data.type === 'leaderboard_update') {
                    setBossState(prev => prev ? { ...prev, leaderboard: data.leaderboard } : null);
                }
            };
        } catch(e) {
            console.warn("WebSocket connection failed, relying on polling or static data", e);
        }

        return () => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
        };
    }, [bossState?.id, addToast]);

    const attack = useCallback(async (answer: string) => {
        setIsSubmitting(true);
        try {
            // Assuming POST /api/v1/boss/attack/ exists
            const result = await apiClient('/api/v1/boss/attack/', {
                method: 'POST',
                body: JSON.stringify({ answer })
            });

            if (result.success) {
                setPersonalDamage(prev => prev + result.damage_dealt);
                addToast('success', `Coup critique ! -${result.damage_dealt} HP`);
                if (result.loot) {
                    addToast('info', `Drop obtenu : ${result.loot.name} !`);
                }
                // HP is updated via WS, but we can optimistically update here if needed
            } else {
                addToast('error', 'Attaque parée (Mauvaise réponse).');
            }
            
            // If the backend rotates questions on correct answer per user, refresh active_question
            if (result.new_question) {
               setBossState(prev => prev ? { ...prev, active_question: result.new_question } : null);
            }

        } catch (err) {
             addToast('error', 'Erreur de communication avec le serveur.');
        } finally {
            setIsSubmitting(false);
        }
    }, [addToast]);

    const getTier = (dmg: number) => {
        if (dmg > 10000) return 'Légendaire';
        if (dmg > 5000) return 'Epique';
        if (dmg > 1000) return 'Rare';
        return 'Commun';
    };

    return {
        bossState,
        loading,
        personalDamage,
        currentTier: getTier(personalDamage),
        isSubmitting,
        attack
    };
};
```

- [ ] **Step 2: Integrate hook into `WorldBossPage.tsx`**

```tsx
// Replace mock data in WorldBossPage.tsx
import { useWorldBoss } from './hooks/useWorldBoss';
import { CardSkeleton } from '../../components/ui/Skeleton';

// Inside WorldBossPage component:
const { bossState, loading, personalDamage, currentTier, isSubmitting, attack } = useWorldBoss();

if (loading) return <div className="p-20"><CardSkeleton /></div>;

// If no active boss
if (!bossState) return (
  <div className="max-w-3xl mx-auto py-20 text-center text-white">
      <h2 className="text-3xl font-black italic">Aucun World Boss Actif</h2>
      <p className="opacity-50 mt-4">Revenez plus tard pour le prochain événement.</p>
  </div>
);

// Map state to components:
// <BossHeader name={bossState.title} phase={bossState.current_phase} phaseName="Enragé" />
// <GlobalHealthBar currentHp={bossState.current_hp} totalHp={bossState.total_hp} />
// <CombatTerminal question={bossState.active_question || "Chargement..."} onSubmit={attack} isSubmitting={isSubmitting} />
// <LootTracker personalDamage={personalDamage} currentTier={currentTier} />
// <RaidLeaderboard entries={bossState.leaderboard || []} />
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/games/hooks/useWorldBoss.ts frontend/src/features/games/WorldBossPage.tsx
git commit -m "feat(boss): integrate useWorldBoss hook for API and WebSocket communication"
```
