# AI Feedback History Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the AI Feedback History page by adding navigation entries in the Sidebar and Settings page, and correct the page's back link.

**Architecture:** Update the Sidebar layout, the Account Settings page, and the Feedback History page with correct routing.

**Tech Stack:** React, TypeScript, React Router

---

### Task 1: Update Sidebar and Settings Links

**Files:**
- Modify: [Layout.tsx](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/src/components/Layout.tsx)
- Modify: [AccountSettingsPage.tsx](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/src/pages/auth/AccountSettingsPage.tsx)

- [ ] **Step 1: Import MessageSquare and add link to Sidebar**

In `Layout.tsx`, import `MessageSquare` from `lucide-react`:
```typescript
import { 
  X, Home, Zap, Trophy, Settings, Sun, Moon, Monitor, 
  CheckCircle2, Shield, Sparkles, Gamepad2, Search, Compass, 
  Network, Film, Users, UserPlus, FlaskConical, BrainCircuit, Eye, LogIn, Microscope, Mic,
  Database, MessageSquare
} from 'lucide-react';
```

And add the link in the Sidebar navigation under the Community section for logged-in users (around line 191):
```typescript
          {isAuthenticated && (
            <>
              <Link to="/social/friends/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/social/friends/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
                <UserPlus className="w-4 h-4 text-pink-400" /> {t('nav.friends', 'Amis')}
              </Link>
              <Link to="/social/sync/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/social/sync/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
                <Database className="w-4 h-4 text-yellow-400" /> {t('nav.offline_sync', 'Sync Hors-ligne')}
              </Link>
              <Link to="/social/ai-feedback-history/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/social/ai-feedback-history/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
                <MessageSquare className="w-4 h-4 text-purple-400" /> {t('nav.ai_feedback_history', 'Feedbacks IA')}
              </Link>
            </>
          )}
```

- [ ] **Step 2: Add Feedback History link in Account Settings Page**

In `AccountSettingsPage.tsx`, add the Link under the "Historique IA" card (around line 225):
```typescript
            {/* Historique IA */}
            <Card padding="lg" className="space-y-6 shadow-xl border-none bg-white dark:bg-[#0f0f1a]">
              <h2 className="text-xl font-bold uppercase tracking-widest border-b border-gray-100 dark:border-white/5 pb-4 mb-4 flex items-center gap-2 text-black dark:text-white">
                <BarChart3 className="w-5 h-5 text-blue-500" /> Quotas & Consommation
              </h2>
              <p className="text-sm opacity-60 text-black dark:text-white">
                Suivez votre utilisation des Bx et vérifiez votre limite quotidienne.
              </p>
              <div className="space-y-3">
                <Link 
                  to="/auth/usage/" 
                  className="flex items-center justify-between bg-blue-500/5 dark:bg-blue-500/10 p-4 rounded-xl border border-blue-500/10 hover:border-blue-500 transition-all no-underline text-black dark:text-white group"
                >
                  <span className="font-bold uppercase tracking-widest text-xs text-blue-600 dark:text-blue-400">Voir mes statistiques</span>
                  <ChevronRight className="w-5 h-5 text-blue-400 group-hover:translate-x-1 transition-all" />
                </Link>
                <Link 
                  to="/social/ai-feedback-history/" 
                  className="flex items-center justify-between bg-purple-500/5 dark:bg-purple-500/10 p-4 rounded-xl border border-purple-500/10 hover:border-purple-500 transition-all no-underline text-black dark:text-white group"
                >
                  <span className="font-bold uppercase tracking-widest text-xs text-purple-600 dark:text-purple-400">Historique des Feedbacks IA</span>
                  <ChevronRight className="w-5 h-5 text-purple-400 group-hover:translate-x-1 transition-all" />
                </Link>
              </div>
            </Card>
```

- [ ] **Step 3: Commit settings & sidebar changes**

```bash
git add frontend/src/components/Layout.tsx frontend/src/pages/auth/AccountSettingsPage.tsx
git commit -m "feat(navigation): add links to AI feedback history in Sidebar and Settings"
```

---

### Task 2: Correct Back Link in Feedback History Page

**Files:**
- Modify: [AIFeedbackHistoryPage.tsx](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/src/pages/social/AIFeedbackHistoryPage.tsx)

- [ ] **Step 1: Update Link target**

Change `/settings` to `/auth/settings/` at line 38 of `AIFeedbackHistoryPage.tsx`.
```typescript
          <Link to="/auth/settings/" className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-gray-500 hover:text-brand-primary mb-4 no-underline transition-colors">
            <ChevronLeft className="w-4 h-4" /> Paramètres
          </Link>
```

- [ ] **Step 2: Commit feedback page changes**

```bash
git add frontend/src/pages/social/AIFeedbackHistoryPage.tsx
git commit -m "fix(navigation): correct back button link in AIFeedbackHistoryPage"
```
