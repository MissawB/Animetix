# Design Spec: Tachidesk/Suwayomi Integration

This design document outlines the architecture, data flow, and components for integrating a local Tachidesk/Suwayomi (Mihon Backend) instance into the Animetix project. This integration connects our system to over 500 manga sources via Tachiyomi/Mihon extensions.

## Goal Description
Connect the Animetix frontend and backend to a local Tachidesk/Suwayomi server. Users will be able to browse installed sources/extensions, search mangas, view chapter lists, and read chapters directly inside the Animetix Manga Reader UI.

---

## Architecture Overview

We respect Hexagonal Architecture principles:
```
Presentation (UI) ➡️ Core (MangaService/SuwayomiPort) ⬅️ Adapters (SuwayomiAdapter)
```

1. **Configuration**: Parametrized URL (`SUWAYOMI_URL`) and password (`SUWAYOMI_PASSWORD`) in `.env` and `config.py`.
2. **Core Port**: `SuwayomiPort` defines the interface to interact with Tachidesk.
3. **Adapter**: `SuwayomiAdapter` implements the port using GraphQL queries against `{SUWAYOMI_URL}/api/graphql`.
4. **Proxy**: Django backend proxies page images to bypass CORS, authentication, and network isolation.
5. **UI**: A dedicated page "Tachidesk Explorer" (`TachideskExplorerPage.tsx`) for searching and selecting mangas.

---

## Detailed Components

### 1. Configuration & Dependency Injection
- **`backend/core/config.py`**: Add `SUWAYOMI_URL: str = "http://127.0.0.1:4567"` and `SUWAYOMI_PASSWORD: Optional[str] = None`.
- **`backend/core/ports/suwayomi_port.py`**: Definas `SuwayomiPort` class.
- **`backend/adapters/persistence/suwayomi_adapter.py`**: Implements the port using `httpx` to send POST requests to the GraphQL endpoint.
- **`backend/api/animetix/containers/persistence.py`**: Registers `suwayomi_adapter` as a singleton.
- **`backend/core/domain/services/manga_service.py`**: Injects `suwayomi_adapter`.

### 2. Synchronization Flow (`MangaService`)
To integrate Suwayomi mangas into our SQL models:
- Suwayomi mangas use `external_id = "suwayomi:<source_id>:<manga_id>"`.
- When fetching chapters via `get_chapters(manga_id)`:
  - If the manga is not in `MediaItem` database, fetch details using `suwayomi_adapter.get_manga_details` and create the `MediaItem` in SQL database.
  - Call `suwayomi_adapter.get_chapters` to fetch all chapters and bulk create them as `MangaChapter` in SQL database (storing Suwayomi chapter IDs in `external_id`).
- When fetching pages via `get_chapter_details(manga_id, chapter_number)`:
  - Call `suwayomi_adapter.get_pages(chapter.external_id)`.
  - Save pages in `MangaPage` database with proxied URLs: `/api/v1/media/Manga/suwayomi-image/?page_url=<base64_encoded_url>`.

### 3. Image Proxy Endpoint
- Expose `/api/v1/media/Manga/suwayomi-image/` in Django.
- Intercepts requests, calls local Suwayomi server to fetch the binary image, and returns it with the correct MIME type.

### 4. API Endpoints
- `GET /api/v1/suwayomi/sources/`: Returns list of installed sources on Suwayomi.
- `GET /api/v1/suwayomi/sources/<source_id>/search/?q=<query>`: Searches or lists popular manga on a source.
- `POST /api/v1/suwayomi/manga/import/`: Imports a manga as a `MediaItem` in our DB.

### 5. Frontend UI (`TachideskExplorerPage.tsx`)
- Modern, high-fidelity explorer page using Tailwind CSS, including:
  - Dropdown selector for active source/language.
  - Search bar.
  - Responsive grid of cards displaying cover, title, and genres.
  - Interactive modal displaying synopsis and list of chapters.
  - Smooth slide/fade animations for transitions.
- Integrates with standard Manga Reader routes upon selecting a chapter.

---

## Verification Plan

### Automated Tests
- Write python unit tests for `SuwayomiAdapter` verifying correct GraphQL query payloads.
- Write unit tests for `MangaService` mock-intercepting Suwayomi IDs and creating database records.

### Manual Verification
- Start the Django server and React/Vite development server.
- Connect to a local Suwayomi server.
- Verify searching, browsing, importing, and reading chapters.
