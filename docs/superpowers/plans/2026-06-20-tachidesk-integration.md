# Tachidesk/Suwayomi Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the project to a local Tachidesk/Suwayomi instance to browse extensions/sources, search mangas, view chapter lists, and read chapters in our Manga Reader UI.

**Architecture:** We use Hexagonal Architecture: a `SuwayomiPort` in the core layer, implemented by a `SuwayomiAdapter` in the adapter layer communicating with Tachidesk via GraphQL, injected as a singleton dependency, and coordinated by `MangaService`. Page images are proxied through a Django backend view.

**Tech Stack:** Python 3.11, Django, React, TypeScript, Tailwind CSS, GraphQL.

---

### Task 1: Configuration

**Files:**
- Modify: `backend/core/config.py`
- Modify: `.env`
- Modify: `.env.example`

- [ ] **Step 1: Add configuration variables to `backend/core/config.py`**
Modify `backend/core/config.py` to add `SUWAYOMI_URL` and `SUWAYOMI_PASSWORD` inside the `Settings` class:
```python
    # AI/ML
    BRAIN_API_URL: Optional[str] = None

    # Tachidesk/Suwayomi
    SUWAYOMI_URL: str = "http://127.0.0.1:4567"
    SUWAYOMI_PASSWORD: Optional[str] = None
```

- [ ] **Step 2: Add variables to `.env`**
Add the following lines to the end of `.env` and `.env.example`:
```env
# --- Tachidesk/Suwayomi ---
SUWAYOMI_URL="http://127.0.0.1:4567"
SUWAYOMI_PASSWORD=""
```

- [ ] **Step 3: Commit**
```bash
git add backend/core/config.py .env .env.example
git commit -m "feat: add Suwayomi config settings"
```

---

### Task 2: Define SuwayomiPort

**Files:**
- Create: `backend/core/ports/suwayomi_port.py`

- [ ] **Step 1: Create port interface**
Create `backend/core/ports/suwayomi_port.py` with abstract definitions for Suwayomi interactions:
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class SuwayomiPort(ABC):
    @abstractmethod
    def get_sources(self) -> List[Dict[str, Any]]:
        """Fetch all installed manga sources from Suwayomi."""
        pass

    @abstractmethod
    def search_manga(self, source_id: str, query: str = "") -> List[Dict[str, Any]]:
        """Search manga or retrieve popular manga from a source on Suwayomi."""
        pass

    @abstractmethod
    def get_manga_details(self, suwayomi_manga_id: str) -> Dict[str, Any]:
        """Fetch details of a manga by its ID from Suwayomi."""
        pass

    @abstractmethod
    def get_chapters(self, suwayomi_manga_id: str) -> List[Dict[str, Any]]:
        """Fetch chapters for a given manga ID from Suwayomi."""
        pass

    @abstractmethod
    def get_pages(self, suwayomi_chapter_id: str) -> List[str]:
        """Fetch page image URLs/paths for a given chapter ID."""
        pass
```

- [ ] **Step 2: Commit**
```bash
git add backend/core/ports/suwayomi_port.py
git commit -m "feat: define SuwayomiPort interface"
```

---

### Task 3: Implement SuwayomiAdapter

**Files:**
- Create: `backend/adapters/persistence/suwayomi_adapter.py`

- [ ] **Step 1: Write GraphQL client adapter**
Create `backend/adapters/persistence/suwayomi_adapter.py` using `httpx` for GraphQL requests:
```python
import logging
import httpx
from typing import Any, Dict, List
from core.ports.suwayomi_port import SuwayomiPort
from core.config import settings

logger = logging.getLogger("animetix.suwayomi")

class SuwayomiAdapter(SuwayomiPort):
    def __init__(self):
        self.url = f"{settings.SUWAYOMI_URL.rstrip('/')}/api/graphql"
        self.headers = {"Content-Type": "application/json"}
        if settings.SUWAYOMI_PASSWORD:
            self.headers["Authorization"] = f"Bearer {settings.SUWAYOMI_PASSWORD}"

    def _query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(self.url, json={"query": query, "variables": variables or {}}, headers=self.headers)
                res.raise_for_status()
                data = res.json()
                if "errors" in data:
                    logger.error(f"GraphQL Errors: {data['errors']}")
                    return {}
                return data.get("data", {})
        except Exception as e:
            logger.error(f"Failed to query Suwayomi at {self.url}: {e}")
            return {}

    def get_sources(self) -> List[Dict[str, Any]]:
        q = """
        query {
          sources {
            nodes {
              id
              name
              lang
            }
          }
        }
        """
        data = self._query(q)
        return data.get("sources", {}).get("nodes", [])

    def search_manga(self, source_id: str, query: str = "") -> List[Dict[str, Any]]:
        q = """
        query Search($source: LongString!, $query: String, $type: SourceMangaType!) {
          fetchSourceManga(source: $source, query: $query, type: $type, page: 1) {
            mangas {
              id
              title
              thumbnailUrl
            }
          }
        }
        """
        vars = {
            "source": source_id,
            "query": query,
            "type": "SEARCH" if query else "POPULAR"
        }
        data = self._query(q, vars)
        return data.get("fetchSourceManga", {}).get("mangas", [])

    def get_manga_details(self, suwayomi_manga_id: str) -> Dict[str, Any]:
        q = """
        query GetManga($id: Int!) {
          manga(id: $id) {
            id
            title
            description
            thumbnailUrl
            author
            artist
            status
          }
        }
        """
        vars = {"id": int(suwayomi_manga_id)}
        data = self._query(q, vars)
        return data.get("manga", {}) or {}

    def get_chapters(self, suwayomi_manga_id: str) -> List[Dict[str, Any]]:
        # Check database, if empty force fetch
        q = """
        query GetChapters($id: Int!) {
          manga(id: $id) {
            chapters {
              id
              name
              chapterNumber
            }
          }
        }
        """
        vars = {"id": int(suwayomi_manga_id)}
        data = self._query(q, vars)
        chapters = data.get("manga", {}).get("chapters", []) if data.get("manga") else []
        if not chapters:
            mut = """
            mutation FetchChapters($id: Int!) {
              fetchChapters(input: { mangaId: $id }) {
                chapters {
                  id
                  name
                  chapterNumber
                }
              }
            }
            """
            data_mut = self._query(mut, {"id": int(suwayomi_manga_id)})
            chapters = data_mut.get("fetchChapters", {}).get("chapters", [])
        return chapters

    def get_pages(self, suwayomi_chapter_id: str) -> List[str]:
        mut = """
        mutation FetchPages($id: Int!) {
          fetchChapterPages(input: { id: $id }) {
            chapter {
              id
              pages
            }
          }
        }
        """
        data = self._query(mut, {"id": int(suwayomi_chapter_id)})
        pages = data.get("fetchChapterPages", {}).get("chapter", {}).get("pages", []) if data.get("fetchChapterPages") else []
        if not pages:
            # Fallback to query
            q = """
            query GetPages($id: Int!) {
              chapter(id: $id) {
                pages
              }
            }
            """
            data_q = self._query(q, {"id": int(suwayomi_chapter_id)})
            pages = data_q.get("chapter", {}).get("pages", []) if data_q.get("chapter") else []
        return pages
```

- [ ] **Step 2: Commit**
```bash
git add backend/adapters/persistence/suwayomi_adapter.py
git commit -m "feat: implement SuwayomiAdapter with GraphQL queries"
```

---

### Task 4: Register in Dependency Injection

**Files:**
- Modify: `backend/api/animetix/containers/persistence.py`
- Modify: `backend/api/animetix/containers/core_services.py`

- [ ] **Step 1: Register SuwayomiAdapter in persistence container**
Open `backend/api/animetix/containers/persistence.py` and register the adapter:
```python
    fandom_adapter = providers.Singleton(
        LazyClass("adapters.persistence.fandom_adapter", "FandomAdapter")
    )

    suwayomi_adapter = providers.Singleton(
        LazyClass("adapters.persistence.suwayomi_adapter", "SuwayomiAdapter")
    )
```

- [ ] **Step 2: Pass suwayomi_adapter to MangaService**
Open `backend/api/animetix/containers/core_services.py` and inject it:
```python
    manga_service = providers.Singleton(
        LazyClass("core.domain.services.manga_service", "MangaService"),
        suwayomi_adapter=persistence.suwayomi_adapter,
    )
```

- [ ] **Step 3: Commit**
```bash
git add backend/api/animetix/containers/persistence.py backend/api/animetix/containers/core_services.py
git commit -m "feat: register suwayomi_adapter in dependency injection container"
```

---

### Task 5: Integrate Suwayomi in MangaService

**Files:**
- Modify: `backend/core/domain/services/manga_service.py`

- [ ] **Step 1: Update MangaService class constructor and synchro methods**
Modify `backend/core/domain/services/manga_service.py` to accept `suwayomi_adapter` and fetch/import Suwayomi data:
```python
import logging
import base64
from typing import List, Optional

from animetix.models import MangaChapter, MangaPage, MediaItem

logger = logging.getLogger("animetix.manga")


class MangaService:
    """
    Service gérant la logique métier des mangas, notamment le chargement dynamique des chapitres.
    """

    def __init__(self, suwayomi_adapter=None):
        self.suwayomi_adapter = suwayomi_adapter

    def get_chapters(self, manga_id: str) -> List[MangaChapter]:
        """Récupère la liste des chapitres. Déclenche une synchro si nécessaire."""
        chapters = list(
            MangaChapter.objects.filter(manga__external_id=manga_id).order_by("number")
        )

        if not chapters:
            logger.info(
                f"📚 No chapters found in DB for manga {manga_id}. Triggering dynamic fetch..."
            )
            self._sync_chapters_from_external(manga_id)
            chapters = list(
                MangaChapter.objects.filter(manga__external_id=manga_id).order_by(
                    "number"
                )
            )

        return chapters

    def get_chapter_details(
        self, manga_id: str, chapter_number: float
    ) -> Optional[MangaChapter]:
        """Récupère les détails d'un chapitre (pages)."""
        try:
            chapter = MangaChapter.objects.get(
                manga__external_id=manga_id, number=chapter_number
            )

            # Si le chapitre n'a pas de pages, on tente de les charger
            if not chapter.pages.exists():
                logger.info(
                    f"📄 No pages found for chapter {chapter_number} of manga {manga_id}. Fetching..."
                )
                self._sync_pages_from_external(chapter)

            return chapter
        except MangaChapter.DoesNotExist:
            # Tenter de synchroniser si le manga existe
            if MediaItem.objects.filter(
                external_id=manga_id, media_type="Manga"
            ).exists():
                self._sync_chapters_from_external(manga_id)
                try:
                    return MangaChapter.objects.get(
                        manga__external_id=manga_id, number=chapter_number
                    )
                except MangaChapter.DoesNotExist:
                    return None
            return None

    def _sync_chapters_from_external(self, manga_id: str):
        """
        Récupère les chapitres depuis un backend externe (Suwayomi ou Mock).
        """
        try:
            manga = MediaItem.objects.get(external_id=manga_id, media_type="Manga")

            if manga_id.startswith("suwayomi:") and self.suwayomi_adapter:
                # Parse suwayomi:<source_id>:<suwayomi_manga_id>
                parts = manga_id.split(":")
                if len(parts) >= 3:
                    suwayomi_manga_id = parts[2]
                    logger.info(f"Syncing chapters from Suwayomi for manga {suwayomi_manga_id}")
                    chapters_data = self.suwayomi_adapter.get_chapters(suwayomi_manga_id)
                    new_chapters = []
                    for ch in chapters_data:
                        chapter, created = MangaChapter.objects.get_or_create(
                            manga=manga,
                            number=float(ch.get("chapterNumber", 0.0) or 0.0),
                            defaults={
                                "title": ch.get("name", f"Chapitre {ch.get('chapterNumber')}"),
                                "external_id": str(ch.get("id"))
                            },
                        )
                        if created:
                            new_chapters.append(chapter)
                    logger.info(f"✅ Synced {len(new_chapters)} chapters from Suwayomi for {manga.title}")
                    return

            # Fallback/Mock
            new_chapters = []
            for i in range(1, 4):
                chapter, created = MangaChapter.objects.get_or_create(
                    manga=manga,
                    number=float(i),
                    defaults={"title": f"Chapitre {i} : L'éveil du Nexus"},
                )
                if created:
                    new_chapters.append(chapter)
            logger.info(f"✅ Synced {len(new_chapters)} new chapters for {manga.title}")

        except MediaItem.DoesNotExist:
            logger.error(
                f"❌ Cannot sync chapters: Manga {manga_id} not found in catalog."
            )

    def _sync_pages_from_external(self, chapter: MangaChapter):
        """
        Récupère les pages depuis Suwayomi ou génère des placeholders.
        """
        if chapter.manga.external_id.startswith("suwayomi:") and self.suwayomi_adapter and chapter.external_id:
            logger.info(f"Syncing pages from Suwayomi for chapter {chapter.external_id}")
            pages_data = self.suwayomi_adapter.get_pages(chapter.external_id)
            pages = []
            for idx, p_url in enumerate(pages_data):
                # Generates backend image proxy URL
                encoded_url = base64.b64encode(p_url.encode('utf-8')).decode('utf-8')
                proxy_url = f"/api/v1/media/Manga/suwayomi-image/?page_url={encoded_url}"
                page, created = MangaPage.objects.get_or_create(
                    chapter=chapter,
                    number=idx + 1,
                    defaults={"image_url": proxy_url}
                )
                pages.append(page)
            logger.info(f"✅ Synced {len(pages)} pages from Suwayomi for chapter {chapter.number}")
            return

        # Fallback/Mock
        page_urls = [
            f"https://picsum.photos/seed/animetix_{chapter.manga.external_id}_{chapter.number}_{p}/800/1200"
            for p in range(1, 6)
        ]
        pages = []
        for idx, url in enumerate(page_urls):
            page, created = MangaPage.objects.get_or_create(
                chapter=chapter, number=idx + 1, defaults={"image_url": url}
            )
            pages.append(page)
        logger.info(f"✅ Synced {len(pages)} pages for {chapter}")
```

- [ ] **Step 2: Commit**
```bash
git add backend/core/domain/services/manga_service.py
git commit -m "feat: integrate Suwayomi synchronization in MangaService"
```

---

### Task 6: Create Proxy Endpoint and API views

**Files:**
- Modify: `backend/api/animetix/api/core.py`
- Modify: `backend/api/animetix/urls/api.py`

- [ ] **Step 1: Implement Image Proxy View and Suwayomi API Views in `core.py`**
Open `backend/api/animetix/api/core.py`. Add `suwayomi_image_proxy` and the API endpoints at the bottom of the file:
```python
import base64
import httpx
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from core.config import settings

@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def suwayomi_image_proxy(request):
    encoded_url = request.GET.get("page_url")
    if not encoded_url:
        return HttpResponse("Missing page_url", status=400)
    try:
        url = base64.b64decode(encoded_url).decode("utf-8")
        # Ensure it starts with '/' or relative path, or prepend settings.SUWAYOMI_URL
        if not url.startswith("http"):
            url = f"{settings.SUWAYOMI_URL.rstrip('/')}/{url.lstrip('/')}"
        
        headers = {}
        if settings.SUWAYOMI_PASSWORD:
            headers["Authorization"] = f"Bearer {settings.SUWAYOMI_PASSWORD}"

        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=headers)
            if res.status_code == 200:
                return HttpResponse(res.content, content_type=res.headers.get("Content-Type", "image/jpeg"))
            return HttpResponse(status=res.status_code)
    except Exception as e:
        logger.error(f"Suwayomi image proxy error: {e}")
        return HttpResponse(status=500)


class SuwayomiSourcesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        container = get_container()
        suwayomi_adapter = container.persistence.suwayomi_adapter()
        sources = suwayomi_adapter.get_sources()
        return Response(sources)


class SuwayomiSearchView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, source_id):
        query = request.query_params.get("q", "")
        container = get_container()
        suwayomi_adapter = container.persistence.suwayomi_adapter()
        mangas = suwayomi_adapter.search_manga(source_id, query)
        return Response(mangas)


class SuwayomiImportView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        source_id = request.data.get("source_id")
        suwayomi_manga_id = request.data.get("manga_id")
        title = request.data.get("title")
        thumbnail_url = request.data.get("thumbnail_url")

        if not source_id or not suwayomi_manga_id or not title:
            return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)

        from animetix.models import MediaItem
        external_id = f"suwayomi:{source_id}:{suwayomi_manga_id}"

        # Get or create the MediaItem in SQL
        manga_item, created = MediaItem.objects.get_or_create(
            external_id=external_id,
            media_type="Manga",
            defaults={
                "title": title,
                "image_url": thumbnail_url,
                "popularity": 1.0
            }
        )

        return Response({
            "id": manga_item.external_id,
            "title": manga_item.title,
            "image": manga_item.image_url,
            "created": created
        })
```

- [ ] **Step 2: Add routes to `backend/api/animetix/urls/api.py`**
Open `backend/api/animetix/urls/api.py` and register the new endpoints:
```python
    path(
        "media/Manga/suwayomi-image/",
        api_views.suwayomi_image_proxy,
        name="api_suwayomi_image_proxy",
    ),
    path(
        "suwayomi/sources/",
        api_views.SuwayomiSourcesView.as_view(),
        name="api_suwayomi_sources",
    ),
    path(
        "suwayomi/sources/<str:source_id>/search/",
        api_views.SuwayomiSearchView.as_view(),
        name="api_suwayomi_search",
    ),
    path(
        "suwayomi/manga/import/",
        api_views.SuwayomiImportView.as_view(),
        name="api_suwayomi_import",
    ),
```

- [ ] **Step 3: Verify the import inside `backend/api/animetix/api_views.py`**
Because `api_views.py` imports everything from `api/core.py`, check that `suwayomi_image_proxy`, `SuwayomiSourcesView`, `SuwayomiSearchView`, and `SuwayomiImportView` are correctly imported and available.

- [ ] **Step 4: Commit**
```bash
git add backend/api/animetix/api/core.py backend/api/animetix/urls/api.py
git commit -m "feat: add Suwayomi proxy endpoint and search/import API views"
```

---

### Task 7: Create Frontend UI for Tachidesk Explorer

**Files:**
- Create: `frontend/src/pages/explore/TachideskExplorerPage.tsx`
- Modify: `frontend/src/features/explore/routes/ExploreRoutes.tsx`
- Modify: `frontend/src/components/Layout.tsx`

- [ ] **Step 1: Implement TachideskExplorerPage**
Create `frontend/src/pages/explore/TachideskExplorerPage.tsx` with modern UI components to select source, search, and view chapters:
```tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { Search, Globe, Library, BookOpen, Loader2, X, ChevronRight } from 'lucide-react';

interface SuwayomiSource {
  id: string;
  name: string;
  lang: string;
}

interface SuwayomiManga {
  id: string;
  title: string;
  thumbnailUrl: string;
}

const TachideskExplorerPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [activeManga, setActiveManga] = useState<SuwayomiManga | null>(null);

  // Fetch Sources
  const { data: sources, isLoading: loadingSources } = useQuery<SuwayomiSource[]>({
    queryKey: ['suwayomi', 'sources'],
    queryFn: () => apiClient('/api/v1/suwayomi/sources/'),
  });

  // Set default source
  useEffect(() => {
    if (sources && sources.length > 0 && !selectedSource) {
      setSelectedSource(sources[0].id);
    }
  }, [sources, selectedSource]);

  // Fetch Mangas
  const { data: mangas, isLoading: loadingMangas, refetch } = useQuery<SuwayomiManga[]>({
    queryKey: ['suwayomi', 'search', selectedSource, searchQuery],
    queryFn: () => apiClient(`/api/v1/suwayomi/sources/${selectedSource}/search/?q=${encodeURIComponent(searchQuery)}`),
    enabled: !!selectedSource,
  });

  // Fetch chapters & detail from Suwayomi through standard flow after Import
  const importMangaMutation = useMutation({
    mutationFn: (manga: SuwayomiManga) => apiClient('/api/v1/suwayomi/manga/import/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_id: selectedSource,
        manga_id: manga.id,
        title: manga.title,
        thumbnail_url: manga.thumbnailUrl
      })
    }),
  });

  // Fetch details (chapters) for active manga
  const { data: activeMangaDetails, isLoading: loadingChapters } = useQuery<any>({
    queryKey: ['suwayomi', 'manga-chapters', activeManga?.id],
    queryFn: async () => {
      if (!activeManga) return null;
      // First import/stub
      const imported = await importMangaMutation.mutateAsync(activeManga);
      // Retrieve chapters
      const chapters = await apiClient(`/api/v1/media/Manga/${imported.id}/chapters/`);
      return { importedId: imported.id, chapters };
    },
    enabled: !!activeManga,
  });

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#05050a] text-white p-6 md:p-12">
        <header className="mb-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div>
            <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-anime-accent mb-2">
              <Library className="w-4 h-4" />
              Manga Hub
            </div>
            <h1 className="text-3xl md:text-4xl font-black italic uppercase tracking-tight">
              Tachidesk <span className="text-anime-accent">Explorer</span>
            </h1>
            <p className="text-sm text-gray-400 mt-1 max-w-xl">
              Connecté à votre serveur Suwayomi local. Accédez à plus de 500 sources et extensions de lecture.
            </p>
          </div>

          {/* Sources Dropdown */}
          <div className="flex items-center gap-3 bg-navy-900/60 border border-white/10 rounded-2xl px-4 py-2 w-full md:w-auto">
            <Globe className="w-4 h-4 text-anime-accent shrink-0" />
            {loadingSources ? (
              <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
            ) : (
              <select
                value={selectedSource}
                onChange={(e) => setSelectedSource(e.target.value)}
                className="bg-transparent text-white text-xs font-bold focus:outline-none uppercase tracking-wider cursor-pointer"
              >
                {sources?.map((s) => (
                  <option key={s.id} value={s.id} className="bg-navy-950 text-white">
                    [{s.lang.toUpperCase()}] {s.name}
                  </option>
                ))}
              </select>
            )}
          </div>
        </header>

        {/* Search Bar */}
        <div className="relative mb-12 max-w-2xl">
          <input
            type="text"
            placeholder="Rechercher un manga..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && refetch()}
            className="w-full bg-navy-900/40 border border-white/5 focus:border-anime-accent/30 rounded-2xl pl-12 pr-6 py-4 text-sm font-medium placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-anime-accent/30 transition-all shadow-inner"
          />
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
        </div>

        {/* Mangas Grid */}
        {loadingMangas ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <Loader2 className="w-8 h-8 animate-spin text-anime-accent" />
            <span className="text-xs font-black uppercase tracking-widest text-gray-500">Chargement du catalogue...</span>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
            {mangas?.map((m) => (
              <div
                key={m.id}
                onClick={() => setActiveManga(m)}
                className="group bg-navy-900/20 border border-white/5 hover:border-anime-accent/20 rounded-2xl overflow-hidden cursor-pointer transition-all duration-300 hover:-translate-y-1 shadow-lg"
              >
                <div className="aspect-[3/4] relative overflow-hidden bg-navy-950">
                  <img
                    src={m.thumbnailUrl || '/static/img/cover_placeholder.jpg'}
                    alt={m.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-4">
                    <button className="w-full bg-anime-accent text-white py-2 rounded-xl text-xs font-black uppercase tracking-wider">
                      Voir les chapitres
                    </button>
                  </div>
                </div>
                <div className="p-4">
                  <h3 className="text-xs font-black uppercase tracking-tight line-clamp-2 group-hover:text-anime-accent transition-colors">
                    {m.title}
                  </h3>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Chapters Slide-over Panel */}
        {activeManga && (
          <div className="fixed inset-0 z-50 flex justify-end">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setActiveManga(null)} />
            <div className="relative w-full max-w-lg bg-navy-950 border-l border-white/10 h-full shadow-2xl flex flex-col p-6 overflow-y-auto animate-in slide-in-from-right duration-350">
              <button
                onClick={() => setActiveManga(null)}
                className="absolute top-6 right-6 p-2 hover:bg-white/5 rounded-full transition-colors"
              >
                <X className="w-6 h-6" />
              </button>

              <div className="mt-8 flex gap-4 items-start">
                <img
                  src={activeManga.thumbnailUrl}
                  alt={activeManga.title}
                  className="w-24 aspect-[3/4] object-cover rounded-xl border border-white/10"
                />
                <div>
                  <h2 className="text-lg font-black uppercase tracking-tight">{activeManga.title}</h2>
                  <span className="text-xs text-anime-accent font-bold mt-1 inline-block">ID: {activeManga.id}</span>
                </div>
              </div>

              <div className="h-px bg-white/10 my-6" />

              <h3 className="text-xs font-black uppercase tracking-widest text-gray-400 mb-4">Chapitres</h3>

              {loadingChapters ? (
                <div className="flex flex-col items-center justify-center py-10 gap-3">
                  <Loader2 className="w-6 h-6 animate-spin text-anime-accent" />
                  <span className="text-[10px] font-black uppercase tracking-wider text-gray-500">Récupération des chapitres...</span>
                </div>
              ) : (
                <div className="flex-1 flex flex-col gap-2">
                  {activeMangaDetails?.chapters?.map((ch: any) => (
                    <button
                      key={ch.id}
                      onClick={() => navigate(`/media/manga/${activeMangaDetails.importedId}/${ch.number}/`)}
                      className="w-full flex items-center justify-between p-4 bg-navy-900/30 hover:bg-anime-accent/15 border border-white/5 hover:border-anime-accent/20 rounded-xl transition-all text-left group"
                    >
                      <div className="flex items-center gap-3">
                        <BookOpen className="w-4 h-4 text-gray-500 group-hover:text-anime-accent" />
                        <span className="text-xs font-bold text-gray-200 group-hover:text-white">
                          {ch.title || `Chapitre ${ch.number}`}
                        </span>
                      </div>
                      <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-white group-hover:translate-x-1 transition-transform" />
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </AnimatedPage>
  );
};

export default TachideskExplorerPage;
```

- [ ] **Step 2: Add route to `frontend/src/features/explore/routes/ExploreRoutes.tsx`**
Open `frontend/src/features/explore/routes/ExploreRoutes.tsx` and import the new page and append the route:
```tsx
import { Route } from 'react-router-dom';
import { lazy } from 'react';

const ExplorePage = lazy(() => import('../../../pages/explore/ExplorePage'));
const SeichijunreiMapPage = lazy(() => import('../../../pages/explore/SeichijunreiMapPage'));
const MarketWikiPage = lazy(() => import('../../../pages/explore/MarketWikiPage'));
const TachideskExplorerPage = lazy(() => import('../../../pages/explore/TachideskExplorerPage'));

export const ExploreRoutes = () => (
  <>
    <Route path="/explore/" element={<ExplorePage />} />
    <Route path="/explore/seichijunrei/" element={<SeichijunreiMapPage />} />
    <Route path="/explore/market/" element={<MarketWikiPage />} />
    <Route path="/explore/tachidesk/" element={<TachideskExplorerPage />} />
  </>
);
```

- [ ] **Step 3: Add sidebar link to `frontend/src/components/Layout.tsx`**
Open `frontend/src/components/Layout.tsx`. Search for the sidebar explore/search links and add the new Link to Tachidesk Explorer:
```tsx
          <Link to="/explore/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/explore/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
             <Map className="w-5 h-5" />
             <span className="text-xs font-black uppercase tracking-widest">{t('sidebar.explore', 'Exploration')}</span>
          </Link>
          <Link to="/explore/tachidesk/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/explore/tachidesk/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
             <BookOpen className="w-5 h-5" />
             <span className="text-xs font-black uppercase tracking-widest">Tachidesk Explorer</span>
          </Link>
```

- [ ] **Step 4: Commit**
```bash
git add frontend/src/pages/explore/TachideskExplorerPage.tsx frontend/src/features/explore/routes/ExploreRoutes.tsx frontend/src/components/Layout.tsx
git commit -m "feat: implement frontend TachideskExplorerPage and navigation"
```
