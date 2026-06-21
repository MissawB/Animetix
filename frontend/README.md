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

## 🔌 Endpoints utilisés

| Endpoint | Usage |
|----------|-------|
| `GET /api/v1/search/?q=...` | Autocomplete |
| `POST /api/v1/game/classic/start/` | Démarrer une partie |
| `GET /api/v1/game/classic/state/` | Récupérer l'état |
| `POST /api/v1/game/classic/guess/` | Soumettre une tentative |
| `POST /api/v1/game/classic/reveal/` | Révéler la réponse |
| `POST /api/v1/search/rag/` | Oracle IA (RAG hybride) |
