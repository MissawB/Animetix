# Extension Quantum Lab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Intégrer les contrôles de compilation JIT et de plasticité synaptique dans la page `QuantumLabPage` et mettre à jour la mutation API associée.

**Architecture:** Ajout d'états React pour gérer les nouveaux paramètres, intégration des composants d'interface dans la carte de configuration, et mise à jour du payload de la mutation TanStack Query.

**Tech Stack:** React, TypeScript, TanStack Query, Tailwind CSS.

---

### Task 1: Mise à jour de l'interface `QuantumLabPage`

**Files:**
- Modify: `frontend\src\pages\labs\QuantumLabPage.tsx`

- [ ] **Step 1: Ajouter les nouveaux états**

Ajouter ces lignes dans le composant `QuantumLabPage`:

```tsx
const [jitLevel, setJitLevel] = useState('basic');
const [plasticity, setPlasticity] = useState('medium');
```

- [ ] **Step 2: Ajouter les composants de contrôle dans le JSX**

Ajouter ces éléments après le sélecteur `Observable Thématique` existant:

```tsx
<div className="space-y-4">
    <label className="text-[10px] font-black opacity-30 uppercase tracking-[0.2em] px-2">Compilation JIT</label>
    <select 
        value={jitLevel} 
        onChange={(e) => setJitLevel(e.target.value)} 
        className="w-full bg-black border-2 border-white/5 rounded-2xl px-6 py-4 text-sm font-bold text-white outline-none focus:border-purple-500 transition-all"
    >
        <option value="none">NONE</option>
        <option value="basic">BASIC</option>
        <option value="aggressive">AGGRESSIVE</option>
    </select>
</div>
<div className="space-y-4">
    <label className="text-[10px] font-black opacity-30 uppercase tracking-[0.2em] px-2">Plasticité Synaptique</label>
    <select 
        value={plasticity} 
        onChange={(e) => setPlasticity(e.target.value)} 
        className="w-full bg-black border-2 border-white/5 rounded-2xl px-6 py-4 text-sm font-bold text-white outline-none focus:border-purple-500 transition-all"
    >
        <option value="low">LOW</option>
        <option value="medium">MEDIUM</option>
        <option value="high">HIGH</option>
        <option value="dynamic">DYNAMIC</option>
    </select>
</div>
```

- [ ] **Step 3: Mettre à jour la mutation**

Modifier l'appel `quantumMutation.mutate`:

```tsx
<Button 
    onClick={() => quantumMutation.mutate({ action: 'quantum', theme: quantumTheme, jitLevel, plasticity })} 
    disabled={quantumMutation.isPending} 
    // ... reste inchangé
>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/labs/QuantumLabPage.tsx
git commit -m "feat: add JIT and synaptic plasticity controls to QuantumLabPage"
```

---

### Task 2: Vérification

- [ ] **Step 1: Vérifier le build**

Run: `npm run build` dans le dossier `frontend` (si disponible, sinon vérifier s'il y a des erreurs de typage).
Expected: PASS

- [ ] **Step 2: Vérification visuelle (optionnelle)**

Lancer le frontend et vérifier la présence des nouveaux sélecteurs et le fonctionnement de la mutation avec les nouveaux paramètres.
