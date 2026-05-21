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

## 🗂️ Structure

```
frontend/src/
├── api.js               # Client REST (search, classic game)
├── index.css            # Design system Tailwind
├── main.jsx             # Entry point React
├── App.jsx              # App principale : NavBar, Dashboard, OraclePanel
└── components/
    ├── SearchBar.jsx    # Autocomplete avec debounce
    └── ClassicGame.jsx  # Jeu classique complet
```

## 🔌 Endpoints utilisés

| Endpoint | Usage |
|----------|-------|
| `GET /api/v1/search/?q=...` | Autocomplete |
| `POST /api/v1/game/classic/start/` | Démarrer une partie |
| `GET /api/v1/game/classic/state/` | Récupérer l'état |
| `POST /api/v1/game/classic/guess/` | Soumettre une tentative |
| `POST /api/v1/game/classic/reveal/` | Révéler la réponse |
| `POST /api/v1/search/rag/` | Oracle IA (RAG hybride) |
