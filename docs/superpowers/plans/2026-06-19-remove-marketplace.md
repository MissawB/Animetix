# Remove Marketplace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all backend and frontend components, routes, models, views, and tests associated with the digital assets marketplace.

**Architecture:** 
1. Delete the page [ShopPage.tsx](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/src/pages/explore/ShopPage.tsx) and its test file [test_market_api.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/tests/api/test_market_api.py).
2. Remove navigation links in frontend components ([Layout.tsx](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/src/components/Layout.tsx), [ExplorePage.tsx](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/src/pages/explore/ExplorePage.tsx)) and the shop route in [ExploreRoutes.tsx](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/src/features/explore/routes/ExploreRoutes.tsx).
3. Remove the backend models (`MarketListing`), views (`MarketListingViewSet`), serializers (`MarketListingSerializer`), transaction type choices (`market_sale`, `market_purchase`), and URLs.
4. Run Django database migration to drop the marketplace tables.

**Tech Stack:** React, TypeScript, Python, Django, DRF, SQLite / PostgreSQL.

---

### Task 1: Clean Frontend Pages, Navigation & Routes

**Files:**
- Delete: `frontend/src/pages/explore/ShopPage.tsx`
- Modify: `frontend/src/features/explore/routes/ExploreRoutes.tsx`
- Modify: `frontend/src/pages/explore/ExplorePage.tsx`
- Modify: `frontend/src/components/Layout.tsx`

- [ ] **Step 1: Delete ShopPage.tsx**
  Delete the file `frontend/src/pages/explore/ShopPage.tsx` from the filesystem.

- [ ] **Step 2: Modify ExploreRoutes.tsx to remove shop route**
  Remove `ShopPage` imports and route from `frontend/src/features/explore/routes/ExploreRoutes.tsx`.
  ```typescript
  // Target
  const ShopPage = lazy(() => import('../../../pages/explore/ShopPage'));
  ...
  <Route path="/explore/shop/" element={<ShopPage />} />
  ```

- [ ] **Step 3: Modify ExplorePage.tsx to remove shop button**
  Remove the shop link from `frontend/src/pages/explore/ExplorePage.tsx`.
  ```typescript
  // Target (around line 139-144)
  <Link 
      to="/explore/shop/"
      className="flex items-center gap-3 px-6 py-2 bg-emerald-400/10 border border-emerald-400/20 rounded-full text-emerald-500 font-black uppercase text-[10px] tracking-widest hover:bg-emerald-400 hover:text-black transition-all group no-underline shadow-lg shadow-emerald-400/5"
  >
      <ShoppingBag className="w-4 h-4 group-hover:scale-110" /> Boutique d'Actifs
  </Link>
  ```
  Also remove `ShoppingBag` from imports if no longer used.

- [ ] **Step 4: Modify Layout.tsx to remove shop link from Sidebar**
  Remove the shop sidebar item from `frontend/src/components/Layout.tsx`.
  ```typescript
  // Target (around line 175-177)
  <Link to="/explore/shop/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/explore/shop/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
    <ShoppingBag className="w-4 h-4 text-emerald-400" /> {t('nav.shop', "Boutique d'Actifs")}
  </Link>
  ```
  Also remove `ShoppingBag` from imports on line 20 if no longer used.

- [ ] **Step 5: Verify build**
  Run: `npm run build` or similar in `frontend/` to make sure there are no compile errors in the frontend.

---

### Task 2: Remove Backend Views, Serializers, and URL Routing

**Files:**
- Modify: `backend/api/animetix/api/explore.py`
- Modify: `backend/api/animetix/serializers.py`
- Modify: `backend/api/animetix/urls/api.py`

- [ ] **Step 1: Modify explore.py to remove MarketListingViewSet**
  Remove `MarketListingViewSet` class entirely and the corresponding imports (`MarketListing`, `MarketListingSerializer`) from `backend/api/animetix/api/explore.py`.

- [ ] **Step 2: Modify serializers.py to remove MarketListingSerializer**
  Remove `MarketListingSerializer` class entirely and the corresponding import `MarketListing` from `backend/api/animetix/serializers.py`.

- [ ] **Step 3: Modify urls/api.py to remove marketplace paths**
  Remove routes for `market/listings/`, `market/listings/<int:pk>/`, `market/listings/<int:pk>/buy/`, and `market/listings/<int:pk>/cancel/` from `backend/api/animetix/urls/api.py`.

---

### Task 3: Remove Backend Models and Run Database Migration

**Files:**
- Modify: `backend/api/animetix/models.py`
- Create: Database migration (auto-generated)

- [ ] **Step 1: Modify models.py to remove MarketListing**
  Remove the `MarketListing` class (lines 528-543) from `backend/api/animetix/models.py`.
  Also remove:
  - `collected_fusions` ManyToMany field on `Profile` (lines 97-99).
  - `"market_sale"` and `"market_purchase"` choices from `WalletTransaction.TRANSACTION_TYPES` (lines 446-447).

- [ ] **Step 2: Generate Django Migration**
  Run: `python backend/api/manage.py makemigrations` in `backend/api/` or from workspace root.
  Expected: Django creates a migration file `backend/api/animetix/migrations/00XX_...py` that drops the model `MarketListing` and field `collected_fusions`.

- [ ] **Step 3: Run Django Migration**
  Run: `python backend/api/manage.py migrate` to apply migrations and drop database tables.

---

### Task 4: Clean Tests and Verify Build

**Files:**
- Delete: `tests/api/test_market_api.py`

- [ ] **Step 1: Delete test_market_api.py**
  Delete the file `tests/api/test_market_api.py` from the filesystem.

- [ ] **Step 2: Run remaining API tests to verify**
  Run: `.venv\Scripts\pytest tests/api/test_explore.py` (or check other explore-related tests).
  Expected: Tests pass.
