# Animetix – Frontend SPA

> Interface React découplée pour la plateforme **Animetix**, connectée au backend Django via son API REST.

## 🛠️ Stack

| Technologie | Usage |
|-------------|-------|
| **Vite 8**  | Bundler ultra-rapide |
| **React 19** | Framework UI |
| **TailwindCSS 3** | Styling utility-first |
| **Lucide React** | Icônes |

## 🚀 Démarrer en développement

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

> Le serveur Vite proxifie automatiquement `/api/*` et `/ws/*` vers Django sur `http://localhost:8000`.

## 🔧 Configuration

Créez (ou modifiez) `frontend/.env` :

```env
VITE_API_BASE=http://localhost:8000
```

## 📦 Build de production

```bash
npm run build
# Génère le dossier dist/ prêt à être servi par Django ou un CDN
```

## 🗂️ Structure & conventions

```
frontend/src/
├── main.tsx              # Entry point (ErrorBoundary + observabilité + AuthProvider + Router)
├── index.css             # Design system Tailwind
├── api.ts                # Client REST haut-niveau + types générés (components["schemas"][…])
├── types/                # Types app + api.d.ts (généré depuis l'OpenAPI backend)
├── context/              # Providers React (Auth…)
├── i18n/                 # Internationalisation
├── store/                # Stores Zustand GLOBAUX (auth, ui, toast, notification)
├── hooks/                # Hooks transverses (non liés à un domaine)
├── utils/                # Utilitaires transverses (apiClient, queryClient, observability…)
├── components/           # UI partagée TRANSVERSE
│   ├── ui/               #   primitives (Button, Card, ErrorBoundary…)
│   ├── layout/           #   layout applicatif (Sidebar, Settings…)
│   └── …                 #   xai/, three/, video/…
├── features/<domaine>/   # LOGIQUE d'un domaine, réutilisable
│   ├── hooks/            #   React Query + logique (useClassicGame…)
│   ├── services/         #   appels API du domaine (classicService…)
│   ├── stores/           #   stores Zustand spécifiques au domaine
│   ├── components/       #   sous-composants réutilisables du domaine
│   └── routes/           #   câblage des routes du domaine (→ importe les pages)
└── pages/<domaine>/      # COMPOSANTS D'ÉCRAN (un par route), qui composent les features
    └── <page>/           #   (optionnel) sous-composants/hooks PROPRES à une grosse page
```

**Où mettre quoi ?** (`features/` et `pages/` se **complètent**, ils ne se dupliquent pas — 0 fichier en double)

| Question | Emplacement |
|----------|-------------|
| Ça rend une **route/écran** ? | `pages/<domaine>/XxxPage.tsx` |
| **Logique de domaine** (hook React Query, appel API, store) réutilisée ? | `features/<domaine>/{hooks,services,stores}` |
| Sous-composant **réutilisable** d'un domaine ? | `features/<domaine>/components/` |
| UI **transverse** (multi-domaines) ? | `components/ui` ou `components/<thème>` |
| State **global** (auth, toasts, UI) ? | `store/` (Zustand) ; sinon préférer React Query pour l'état serveur |
| Sous-composant/hook **propre à une seule grosse page** ? | co-localisé sous `pages/<domaine>/<page>/` |

> Convention validée : `features/` = logique, `pages/` = écrans. Pas de migration `modules/` —
> la séparation est saine et un déplacement massif (≈265 fichiers + imports/routing/lazy/PWA)
> serait à haut risque pour un gain marginal.

## 🧠 Convention de state (Zustand vs React Query vs useState)

Choisir l'outil selon la **nature** de la donnée, pas par habitude :

| Nature de l'état | Outil | Exemples |
|------------------|-------|----------|
| **État serveur** (données d'API : CRUD, listes, détails) | **React Query** (`useQuery`/`useMutation`) | profil, dashboard social, clubs, achievements, leaderboard, détail média, admin, `custom-config` |
| **État global client** (UI/préférences, auth, transverse) | **Zustand** (`store/`) | `authStore`, `uiStore` (sidebar/thème/langue), `toastStore`, `notificationStore` (WebSocket), `personalizationStore` |
| **État local d'un composant** (form, toggle, focus) | **`useState`/`useReducer`** | inputs, visibilité d'un menu |
| **Session transient** d'un jeu/lab piloté par un service | **Zustand de feature** _(toléré)_ **ou** React Query | `akinetix/paradox/vision/blindtestStore` (Zustand) ; `useClassicGame/useCovertest/useEmoji` (React Query) |

Garde-fous :
- **Jamais** de données serveur brutes dans un `useState` partagé entre composants → React Query.
- **Sessions de jeu** : les deux approches coexistent (choix historique assumé). Pour un *nouveau* jeu, préférer un hook React Query (cf. `useClassicGame`) ; ne garder Zustand que si la session est fortement couplée à un flux de service local sans besoin du cache/stale/refetch.
- `custom-config` (`/api/v1/custom-config/`, React Query, thème visuel) et `personalizationStore` (`/api/v1/profiles/me/`, Zustand, archétype/aura) sont **deux concerns distincts** — ce **n'est pas** une duplication.
- **Clés React Query** : tableaux simples (`['profile', username]`). Si le nombre de clés croît, factoriser une *query-key factory* par domaine pour éviter les bugs d'invalidation.
- **WebSocket** : l'état de connexion vit en Zustand (`notificationStore`) et déclenche des `invalidateQueries` pour rafraîchir le cache serveur (séparation temps-réel / cache).

## 🔌 Endpoints utilisés

| Endpoint | Usage |
|----------|-------|
| `GET /api/v1/search/?q=...` | Autocomplete |
| `POST /api/v1/game/classic/start/` | Démarrer une partie |
| `GET /api/v1/game/classic/state/` | Récupérer l'état |
| `POST /api/v1/game/classic/guess/` | Soumettre une tentative |
| `POST /api/v1/game/classic/reveal/` | Révéler la réponse |
| `POST /api/v1/search/rag/` | Oracle IA (RAG hybride) |
