# Library Categorization & Sorting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Organize the manga collection into custom folders ("Reading", "Completed", "Plan to Read") with filters and unread chapter counters.

**Architecture:** We will extend the existing `FavoriteManga` model to store status (folder) and `last_read_chapter`. The backend APIs will be updated to return/update these fields, dynamically computing the unread chapter count. The frontend will have a new dashboard page for the library and sidebar integration.

**Tech Stack:** Django (Backend REST API), React + TypeScript + Vite + TailwindCSS (Frontend)

---

### Task 1: Update FavoriteManga Model

**Files:**
- Modify: `backend/api/animetix/models.py:83-100`
- Test: `tests/backend/api/test_manga_favorites_api.py`

- [ ] **Step 1: Write the failing test**
  Add a test to verify `FavoriteManga` has the new status and `last_read_chapter` fields.
  Add to `tests/backend/api/test_manga_favorites_api.py`:
  ```python
  @pytest.mark.django_db
  def test_favorite_manga_new_fields(db):
      from django.contrib.auth.models import User
      from animetix.models import FavoriteManga, MediaItem
      
      user = User.objects.create_user(username="testuser", password="password")
      manga = MediaItem.objects.create(external_id="test_manga_1", media_type="Manga", title="Test Manga")
      fav = FavoriteManga.objects.create(user=user, manga=manga)
      
      # Assert fields exist with default values
      assert fav.status == "reading"
      assert fav.last_read_chapter == 0.0
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `..\..\.venv\Scripts\pytest.exe tests/backend/api/test_manga_favorites_api.py::test_favorite_manga_new_fields -v`
  Expected: FAIL (AttributeError: 'FavoriteManga' object has no attribute 'status')

- [ ] **Step 3: Update the model in backend/api/animetix/models.py**
  Replace `FavoriteManga` declaration:
  ```python
  class FavoriteManga(models.Model):
      STATUS_CHOICES = [
          ("reading", "Reading"),
          ("completed", "Completed"),
          ("plan_to_read", "Plan to Read"),
      ]
      user = models.ForeignKey(
          User, on_delete=models.CASCADE, related_name="favorite_mangas"
      )
      manga = models.ForeignKey(
          MediaItem,
          on_delete=models.CASCADE,
          related_name="favorited_by",
          limit_choices_to={"media_type": "Manga"},
      )
      status = models.CharField(
          max_length=20,
          choices=STATUS_CHOICES,
          default="reading",
          db_index=True,
      )
      last_read_chapter = models.FloatField(default=0.0)
      created_at = models.DateTimeField(auto_now_add=True)
      updated_at = models.DateTimeField(auto_now=True)

      class Meta:
          unique_together = ("user", "manga")

      def __str__(self):
          return f"{self.user.username} - {self.manga.title} ({self.status})"
  ```

- [ ] **Step 4: Create and apply migrations**
  Run: `..\..\.venv\Scripts\python.exe backend/api/manage.py makemigrations`
  Run: `..\..\.venv\Scripts\python.exe backend/api/manage.py migrate`

- [ ] **Step 5: Run tests to verify they pass**
  Run: `..\..\.venv\Scripts\pytest.exe tests/backend/api/test_manga_favorites_api.py -v`
  Expected: PASS

- [ ] **Step 6: Commit**
  Run:
  ```bash
  git add backend/api/animetix/models.py tests/backend/api/test_manga_favorites_api.py
  git commit -m "feat: add status and last_read_chapter to FavoriteManga model"
  ```

---

### Task 2: Implement FavoriteMangaSerializer

**Files:**
- Modify: `backend/api/animetix/serializers.py`
- Test: `tests/backend/api/test_manga_favorites_api.py`

- [ ] **Step 1: Write a test for the serializer**
  Add a test to verify serializer outputs correct values including computed unread chapters count.
  Add to `tests/backend/api/test_manga_favorites_api.py`:
  ```python
  @pytest.mark.django_db
  def test_favorite_manga_serializer(db):
      from django.contrib.auth.models import User
      from animetix.models import FavoriteManga, MediaItem, MangaChapter
      from animetix.serializers import FavoriteMangaSerializer
      
      user = User.objects.create_user(username="testuser", password="password")
      manga = MediaItem.objects.create(external_id="test_manga_1", media_type="Manga", title="Test Manga")
      MangaChapter.objects.create(manga=manga, number=1.0, title="Ch 1")
      MangaChapter.objects.create(manga=manga, number=2.0, title="Ch 2")
      
      fav = FavoriteManga.objects.create(user=user, manga=manga, status="reading", last_read_chapter=1.0)
      
      serializer = FavoriteMangaSerializer(fav)
      data = serializer.data
      
      assert data["status"] == "reading"
      assert data["last_read_chapter"] == 1.0
      assert data["unread_chapters_count"] == 1 # Only Ch 2 is unread
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `..\..\.venv\Scripts\pytest.exe tests/backend/api/test_manga_favorites_api.py::test_favorite_manga_serializer -v`
  Expected: FAIL (ImportError: cannot import name 'FavoriteMangaSerializer')

- [ ] **Step 3: Define FavoriteMangaSerializer in backend/api/animetix/serializers.py**
  Add to imports in `backend/api/animetix/serializers.py`:
  `FavoriteManga,`
  And add the serializer class:
  ```python
  class FavoriteMangaSerializer(serializers.ModelSerializer):
      manga = MediaItemSerializer(read_only=True)
      unread_chapters_count = serializers.SerializerMethodField()

      class Meta:
          model = FavoriteManga
          fields = [
              "id",
              "manga",
              "status",
              "last_read_chapter",
              "unread_chapters_count",
              "created_at",
              "updated_at",
          ]

      def get_unread_chapters_count(self, obj):
          return obj.manga.chapters.filter(number__gt=obj.last_read_chapter).count()
  ```

- [ ] **Step 4: Run tests to verify they pass**
  Run: `..\..\.venv\Scripts\pytest.exe tests/backend/api/test_manga_favorites_api.py::test_favorite_manga_serializer -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add backend/api/animetix/serializers.py tests/backend/api/test_manga_favorites_api.py
  git commit -m "feat: implement FavoriteMangaSerializer"
  ```

---

### Task 3: Update Toggle and List Views

**Files:**
- Modify: `backend/api/animetix/api/core.py`
- Test: `tests/backend/api/test_manga_favorites_api.py`

- [ ] **Step 1: Write tests for list and toggle API updates**
  Update list and toggle tests to verify that:
  - List view returns serializer data (array of FavoriteManga objects).
  - Toggle view accepts custom status payload.
  - Toggle view GET returns favorite metadata.
  Add/modify in `tests/backend/api/test_manga_favorites_api.py`:
  ```python
  @pytest.mark.django_db
  def test_favorite_list_view_serialized(authenticated_client):
      from animetix.models import MediaItem, FavoriteManga
      user = User.objects.get(username="testuser")
      manga = MediaItem.objects.create(external_id="m1", media_type="Manga", title="Manga 1")
      FavoriteManga.objects.create(user=user, manga=manga, status="plan_to_read")
      
      url = reverse("api_manga_favorites")
      res = authenticated_client.get(url)
      assert res.status_code == 200
      assert len(res.data) == 1
      assert res.data[0]["status"] == "plan_to_read"
      assert res.data[0]["manga"]["title"] == "Manga 1"

  @pytest.mark.django_db
  def test_favorite_toggle_custom_status(authenticated_client):
      from animetix.models import MediaItem, FavoriteManga
      manga = MediaItem.objects.create(external_id="m2", media_type="Manga", title="Manga 2")
      url = reverse("api_manga_favorite_toggle", kwargs={"media_id": "m2"})
      
      # Toggle on with completed status
      res = authenticated_client.post(url, {"status": "completed"}, format="json")
      assert res.status_code == 200
      assert res.data["success"] is True
      assert res.data["is_favorite"] is True
      
      # Check detail state via GET
      res = authenticated_client.get(url)
      assert res.status_code == 200
      assert res.data["is_favorite"] is True
      assert res.data["status"] == "completed"
  ```

- [ ] **Step 2: Run tests to verify failure**
  Run: `..\..\.venv\Scripts\pytest.exe tests/backend/api/test_manga_favorites_api.py -v`
  Expected: FAIL

- [ ] **Step 3: Update views in backend/api/animetix/api/core.py**
  Update `FavoriteMangaListView.get`:
  ```python
      def get(self, request):
          from ..models import FavoriteManga
          from ..serializers import FavoriteMangaSerializer

          favorites = FavoriteManga.objects.filter(user=request.user).select_related(
              "manga"
          )
          serializer = FavoriteMangaSerializer(favorites, many=True)
          return Response(serializer.data)
  ```
  Update `FavoriteMangaToggleView.post` and `get`:
  ```python
      def post(self, request, media_id):
          # ... (keep item retrieval/auto-import)
          
          # 2. Toggle/Update Favori
          status_val = request.data.get("status")
          if status_val:
              if status_val not in ["reading", "completed", "plan_to_read"]:
                  return Response({"error": "Invalid status value"}, status=400)
              favorite, created = FavoriteManga.objects.get_or_create(
                  user=request.user, manga=manga,
                  defaults={"status": status_val}
              )
              if not created:
                  favorite.status = status_val
                  favorite.save()
              is_favorite = True
          else:
              favorite, created = FavoriteManga.objects.get_or_create(
                  user=request.user, manga=manga
              )
              if not created:
                  favorite.delete()
                  is_favorite = False
              else:
                  is_favorite = True

          return Response({"success": True, "is_favorite": is_favorite})

      def get(self, request, media_id):
          from ..models import FavoriteManga

          try:
              favorite = FavoriteManga.objects.get(
                  user=request.user, manga__external_id=media_id
              )
              return Response({
                  "is_favorite": True,
                  "status": favorite.status,
                  "last_read_chapter": favorite.last_read_chapter,
              })
          except FavoriteManga.DoesNotExist:
              return Response({
                  "is_favorite": False,
                  "status": None,
                  "last_read_chapter": 0.0,
              })
  ```

- [ ] **Step 4: Run tests to verify they pass**
  Run: `..\..\.venv\Scripts\pytest.exe tests/backend/api/test_manga_favorites_api.py -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add backend/api/animetix/api/core.py tests/backend/api/test_manga_favorites_api.py
  git commit -m "feat: support custom status in toggle API and serialize favorites"
  ```

---

### Task 4: Integrate Auto-Transitions in Sync Progress API

**Files:**
- Modify: `backend/api/animetix/api/core.py`
- Test: `tests/backend/api/test_tracker_sync_api.py`

- [ ] **Step 1: Write a test verifying progress updates and auto-transitions**
  Add to `tests/backend/api/test_tracker_sync_api.py`:
  ```python
  @pytest.mark.django_db
  def test_manga_chapter_sync_progress_and_auto_transitions(authenticated_client):
      from animetix.models import MediaItem, FavoriteManga, MangaChapter
      user = User.objects.get(username="testuser")
      
      manga = MediaItem.objects.create(
          external_id="999",
          media_type="Manga",
          title="Fullmetal Alchemist",
          metadata={"id": "999"},
      )
      # Create 2 chapters
      MangaChapter.objects.create(manga=manga, number=1.0)
      MangaChapter.objects.create(manga=manga, number=2.0)
      
      # Start as plan to read
      FavoriteManga.objects.create(user=user, manga=manga, status="plan_to_read")
      
      # Sync chapter 1 -> Should auto-transition to reading
      url = reverse("api_manga_chapter_sync", kwargs={"media_id": "999", "chapter_number": "1"})
      res = authenticated_client.post(url)
      assert res.status_code == 200
      
      fav = FavoriteManga.objects.get(user=user, manga=manga)
      assert fav.last_read_chapter == 1.0
      assert fav.status == "reading"
      
      # Sync chapter 2 -> Last chapter read, should auto-transition to completed
      url = reverse("api_manga_chapter_sync", kwargs={"media_id": "999", "chapter_number": "2"})
      res = authenticated_client.post(url)
      assert res.status_code == 200
      
      fav.refresh_from_db()
      assert fav.last_read_chapter == 2.0
      assert fav.status == "completed"
  ```

- [ ] **Step 2: Run test to verify failure**
  Run: `..\..\.venv\Scripts\pytest.exe tests/backend/api/test_tracker_sync_api.py::test_manga_chapter_sync_progress_and_auto_transitions -v`
  Expected: FAIL

- [ ] **Step 3: Update sync endpoint logic in backend/api/animetix/api/core.py**
  Add local progress updates inside `MangaChapterSyncView.post`:
  ```python
          # (inside MangaChapterSyncView.post, near line 916)
          # Loop over connections and sync ... (existing MAL/AniList code)
          
          # 5. Local Progress Update & Auto-Transition
          try:
              from ..models import FavoriteManga
              
              fav, created = FavoriteManga.objects.get_or_create(
                  user=request.user, manga=manga,
                  defaults={"status": "reading", "last_read_chapter": float(chapter_number)}
              )
              if not created:
                  fav.last_read_chapter = max(fav.last_read_chapter, float(chapter_number))
                  # Auto transition logic
                  has_unread = manga.chapters.filter(number__gt=fav.last_read_chapter).exists()
                  if not has_unread:
                      fav.status = "completed"
                  elif fav.status == "plan_to_read":
                      fav.status = "reading"
                  fav.save()
              else:
                  # For new favorites, also check if it's the last chapter
                  has_unread = manga.chapters.filter(number__gt=fav.last_read_chapter).exists()
                  if not has_unread:
                      fav.status = "completed"
                      fav.save()
          except Exception as e:
              logger.error(f"Failed to update local FavoriteManga progress: {e}")
  ```

- [ ] **Step 4: Run tests to verify they pass**
  Run: `..\..\.venv\Scripts\pytest.exe tests/backend/api/test_tracker_sync_api.py -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add backend/api/animetix/api/core.py tests/backend/api/test_tracker_sync_api.py
  git commit -m "feat: implement auto-transitions and local progress update on chapter sync"
  ```

---

### Task 5: Update Frontend Types and API Client

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/api.ts`

- [ ] **Step 1: Update type definitions in frontend/src/types/index.ts**
  Add `FavoriteManga` type and status type:
  ```typescript
  export type FavoriteMangaStatus = 'reading' | 'completed' | 'plan_to_read';

  export interface FavoriteManga {
    id: number;
    manga: MediaItem;
    status: FavoriteMangaStatus;
    last_read_chapter: number;
    unread_chapters_count: number;
    created_at: string;
    updated_at: string;
  }
  ```

- [ ] **Step 2: Update API functions in frontend/src/api.ts**
  Add functions:
  ```typescript
  export async function getFavoriteMangas(): Promise<FavoriteManga[]> {
    return apiClient('/api/v1/media/favorites/');
  }

  export async function toggleFavoriteManga(mediaId: string, status?: FavoriteMangaStatus, autoImportParams?: { source_id: string, suwayomi_manga_id: string }): Promise<{ success: boolean; is_favorite: boolean }> {
    return apiClient(`/api/v1/media/Manga/${mediaId}/favorite/`, {
      method: 'POST',
      body: JSON.stringify({ status, ...autoImportParams }),
    });
  }

  export async function getFavoriteMangaStatus(mediaId: string): Promise<{ is_favorite: boolean; status: FavoriteMangaStatus | null; last_read_chapter: number }> {
    return apiClient(`/api/v1/media/Manga/${mediaId}/favorite/`);
  }
  ```

- [ ] **Step 3: Commit**
  Run:
  ```bash
  git add frontend/src/types/index.ts frontend/src/api.ts
  git commit -m "feat: add frontend types and API functions for library favorites"
  ```

---

### Task 6: Implement Manga Library Page and Routes

**Files:**
- Create: `frontend/src/pages/media/MangaLibraryPage.tsx`
- Modify: `frontend/src/features/media/routes/MediaRoutes.tsx`
- Modify: `frontend/src/components/layout/SidebarDrawer.tsx`

- [ ] **Step 1: Create MangaLibraryPage.tsx**
  Implement the full UI dashboard with search, tabs ("All", "Reading", "Plan to Read", "Completed"), sorting, unread badges, and folder selector.
  Create [MangaLibraryPage.tsx](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/src/pages/media/MangaLibraryPage.tsx):
  ```tsx
  import React, { useState } from 'react';
  import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
  import { useNavigate, Link } from 'react-router-dom';
  import { BookOpen, Search, ArrowUpDown, Bookmark, Loader2, BookmarkCheck } from 'lucide-react';
  import { getFavoriteMangas, toggleFavoriteManga } from '../../api';
  import type { FavoriteMangaStatus } from '../../types';
  import { AnimatedPage } from '../../components/ui/AnimatedPage';

  const MangaLibraryPage: React.FC = () => {
    const queryClient = useQueryClient();
    const navigate = useNavigate();
    
    const [activeTab, setActiveTab] = useState<'all' | FavoriteMangaStatus>('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [sortBy, setSortBy] = useState<'title' | 'unread' | 'date'>('title');

    const { data: favorites, isLoading } = useQuery({
      queryKey: ['favoriteMangas'],
      queryFn: getFavoriteMangas,
    });

    const updateStatusMutation = useMutation({
      mutationFn: ({ mediaId, status }: { mediaId: string; status: FavoriteMangaStatus }) => 
        toggleFavoriteManga(mediaId, status),
      onSuccess: () => {
        void queryClient.invalidateQueries({ queryKey: ['favoriteMangas'] });
      }
    });

    const removeFavoriteMutation = useMutation({
      mutationFn: (mediaId: string) => toggleFavoriteManga(mediaId),
      onSuccess: () => {
        void queryClient.invalidateQueries({ queryKey: ['favoriteMangas'] });
      }
    });

    if (isLoading) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
          <Loader2 className="w-10 h-10 animate-spin text-yellow-400" />
          <p className="text-sm font-black uppercase tracking-widest opacity-60">Chargement de votre bibliothèque...</p>
        </div>
      );
    }

    const filtered = (favorites || []).filter(fav => {
      const matchTab = activeTab === 'all' || fav.status === activeTab;
      const matchSearch = fav.manga.title.toLowerCase().includes(searchQuery.toLowerCase());
      return matchTab && matchSearch;
    });

    const sorted = [...filtered].sort((a, b) => {
      if (sortBy === 'title') return a.manga.title.localeCompare(b.manga.title);
      if (sortBy === 'unread') return b.unread_chapters_count - a.unread_chapters_count;
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });

    const counts = {
      all: favorites?.length || 0,
      reading: favorites?.filter(f => f.status === 'reading').length || 0,
      plan_to_read: favorites?.filter(f => f.status === 'plan_to_read').length || 0,
      completed: favorites?.filter(f => f.status === 'completed').length || 0,
    };

    return (
      <AnimatedPage>
        <div className="max-w-7xl mx-auto px-6 py-12">
          <h1 className="text-4xl font-black italic manga-font uppercase mb-8 flex items-center gap-3">
            <BookOpen className="w-8 h-8 text-yellow-400" />
            Ma <span className="text-yellow-400">Bibliothèque</span> Manga
          </h1>

          {/* Folder Tabs */}
          <div className="flex flex-wrap gap-2 mb-8 border-b border-white/5 pb-6">
            {(['all', 'reading', 'plan_to_read', 'completed'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-5 py-2.5 rounded-full text-xs font-black uppercase tracking-wider transition-all ${
                  activeTab === tab 
                    ? 'bg-yellow-400 text-black shadow-lg scale-105' 
                    : 'bg-white/5 text-white/60 hover:text-white hover:bg-white/10'
                }`}
              >
                {tab === 'all' && `Tout (${counts.all})`}
                {tab === 'reading' && `En cours (${counts.reading})`}
                {tab === 'plan_to_read' && `À lire (${counts.plan_to_read})`}
                {tab === 'completed' && `Terminés (${counts.completed})`}
              </button>
            ))}
          </div>

          {/* Toolbar */}
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between mb-8 bg-white/5 p-4 rounded-2xl border border-white/5">
            {/* Search */}
            <div className="relative w-full md:w-80">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
              <input
                type="text"
                placeholder="Rechercher dans la bibliothèque..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full bg-white/5 border border-white/5 rounded-xl py-2.5 pl-11 pr-4 text-sm text-white placeholder-white/30 focus:outline-none focus:border-yellow-400/50"
              />
            </div>

            {/* Sort */}
            <div className="flex items-center gap-3 w-full md:w-auto justify-end">
              <ArrowUpDown className="w-4 h-4 text-white/40" />
              <select
                value={sortBy}
                onChange={e => setSortBy(e.target.value as any)}
                className="bg-[#0f0f1a] border border-white/5 rounded-xl px-4 py-2.5 text-xs font-black uppercase tracking-wider text-white focus:outline-none focus:border-yellow-400"
              >
                <option value="title">Trier par Titre</option>
                <option value="unread">Trier par Non lus</option>
                <option value="date">Trier par Date d'ajout</option>
              </select>
            </div>
          </div>

          {sorted.length === 0 ? (
            <div className="text-center py-20 bg-white/5 border border-white/5 rounded-3xl p-8">
              <Bookmark className="w-16 h-16 text-white/10 mx-auto mb-4" />
              <h3 className="text-lg font-bold text-white mb-1">Aucun manga trouvé</h3>
              <p className="text-sm text-white/40 max-w-sm mx-auto mb-6">
                Ajoutez des mangas en favoris depuis le catalogue Explorer ou Tachidesk pour commencer à remplir votre bibliothèque.
              </p>
              <Link to="/explore/" className="px-6 py-3 bg-yellow-400 hover:bg-yellow-300 text-black text-xs font-black uppercase tracking-wider rounded-xl transition-all shadow-md inline-block">
                Parcourir les mangas
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {sorted.map(fav => (
                <div key={fav.id} className="bg-white/5 border border-white/5 hover:border-white/10 rounded-3xl p-5 flex flex-col justify-between transition-all hover:scale-[1.02] group">
                  <div className="flex gap-4">
                    {/* Cover Image */}
                    <div className="w-20 h-28 bg-[#1a1a2e] rounded-xl overflow-hidden flex-shrink-0 relative border border-white/5 shadow-md">
                      {fav.manga.image ? (
                        <img src={fav.manga.image} alt={fav.manga.title} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center opacity-30">
                          <BookOpen className="w-8 h-8" />
                        </div>
                      )}
                      
                      {/* Unread Counter Badge */}
                      {fav.unread_chapters_count > 0 && (
                        <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-black px-2 py-0.5 rounded-full shadow-lg border border-red-600 animate-pulse">
                          +{fav.unread_chapters_count}
                        </span>
                      )}
                    </div>

                    {/* Content info */}
                    <div className="flex-1 min-w-0 flex flex-col justify-between">
                      <div>
                        <h3 className="text-sm font-black italic uppercase tracking-tight truncate text-white leading-tight mb-1" title={fav.manga.title}>
                          {fav.manga.title}
                        </h3>
                        <p className="text-[10px] font-bold text-white/40 uppercase tracking-widest">
                          Lu : Ch. {fav.last_read_chapter}
                        </p>
                      </div>

                      {/* Dropdown status changer */}
                      <div className="mt-2">
                        <select
                          value={fav.status}
                          onChange={e => updateStatusMutation.mutate({ mediaId: fav.manga.id, status: e.target.value as FavoriteMangaStatus })}
                          className="bg-white/5 border border-white/5 rounded-lg px-2.5 py-1.5 text-[10px] font-black uppercase tracking-wider text-white focus:outline-none w-full cursor-pointer hover:bg-white/10"
                        >
                          <option value="reading" className="bg-[#0f0f1a]">En cours</option>
                          <option value="plan_to_read" className="bg-[#0f0f1a]">À lire</option>
                          <option value="completed" className="bg-[#0f0f1a]">Terminés</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2 mt-4">
                    <button
                      onClick={() => navigate(`/media/manga/${fav.manga.id}/${fav.last_read_chapter + 1}/`)}
                      className="py-2 bg-yellow-400 hover:bg-yellow-300 text-black text-[9px] font-black uppercase tracking-widest rounded-xl transition-all shadow-md active:scale-95 text-center flex items-center justify-center gap-1.5"
                    >
                      <BookOpen className="w-3 h-3" />
                      Continuer
                    </button>
                    <button
                      onClick={() => {
                        if (window.confirm("Retirer ce manga de votre bibliothèque ?")) {
                          removeFavoriteMutation.mutate(fav.manga.id);
                        }
                      }}
                      className="py-2 bg-white/5 hover:bg-red-500/10 text-white/60 hover:text-red-400 text-[9px] font-black uppercase tracking-widest rounded-xl transition-all border border-white/5 hover:border-red-500/20 active:scale-95"
                    >
                      Retirer
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </AnimatedPage>
    );
  };

  export default MangaLibraryPage;
  ```

- [ ] **Step 2: Add route to MediaRoutes.tsx**
  Add imports/declarations in `frontend/src/features/media/routes/MediaRoutes.tsx`:
  ```typescript
  const MangaLibraryPage = lazy(() => import('../../../pages/media/MangaLibraryPage'));
  ```
  And inside routes wrapper:
  ```typescript
  <Route path="/media/manga/library/" element={<MangaLibraryPage />} />
  ```

- [ ] **Step 3: Add link to SidebarDrawer.tsx**
  Add under Exploration routes section in `frontend/src/components/layout/SidebarDrawer.tsx` (next to `Manga Hors-ligne` line 108):
  ```tsx
  <Link to="/media/manga/library/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/media/manga/library/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
    <BookOpen className="w-4 h-4 text-yellow-400" /> {t('nav.manga_library', 'Ma Bibliothèque')}
  </Link>
  ```

- [ ] **Step 4: Commit**
  Run:
  ```bash
  git add frontend/src/pages/media/MangaLibraryPage.tsx frontend/src/features/media/routes/MediaRoutes.tsx frontend/src/components/layout/SidebarDrawer.tsx
  git commit -m "feat: implement MangaLibraryPage UI, routing and sidebar link"
  ```

---

### Task 7: Update Explorer Details Drawer with Folder Selector

**Files:**
- Modify: `frontend/src/pages/explore/tachidesk/components/MangaDetailDrawer.tsx`
- Modify: `frontend/src/pages/explore/tachidesk/hooks/useTachideskExplorer.ts`

- [ ] **Step 1: Update useTachideskExplorer hook to handle folder status**
  Update `selectManga` and `toggleFavorite` in `frontend/src/pages/explore/tachidesk/hooks/useTachideskExplorer.ts` to support receiving and setting `status` from backend.
  We will modify:
  - Add state `const [favoriteStatus, setFavoriteStatus] = useState<FavoriteMangaStatus | null>(null);`
  - In `selectManga`, when calling favorite status endpoint:
    ```typescript
      void fetch(`/api/v1/media/Manga/${extId}/favorite/`)
        .then(res => res.ok ? res.json() : { is_favorite: false, status: null })
        .then((data: { is_favorite: boolean, status: any }) => {
          setIsFavorited(data.is_favorite);
          setFavoriteStatus(data.status);
        });
    ```
  - Modify `toggleFavorite` to accept `status?: FavoriteMangaStatus`:
    ```typescript
      const toggleFavorite = useCallback(async (status?: any) => {
        if (!selectedManga) return;
        const extId = `suwayomi:${selectedSource}:${selectedManga.id}`;
        setTogglingFavorite(true);
        try {
          const res = await fetch(`/api/v1/media/Manga/${extId}/favorite/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              status,
              source_id: selectedSource,
              suwayomi_manga_id: selectedManga.id
            })
          });
          if (res.ok) {
            const data: { is_favorite: boolean, status?: any } = await res.json();
            setIsFavorited(data.is_favorite);
            setFavoriteStatus(data.status || null);
          }
        } catch {
          setError("Impossible de mettre à jour le statut favori");
        } finally {
          setTogglingFavorite(false);
        }
      }, [selectedManga, selectedSource]);
    ```

- [ ] **Step 2: Update MangaDetailDrawer.tsx**
  Modify [MangaDetailDrawer.tsx](file:///c:/Users/bahma/PycharmProjects\Projet solo\Double_scenario_Project\frontend\src\pages\explore\tachidesk\components\MangaDetailDrawer.tsx) to pass `favoriteStatus` and allow choosing status via dropdown next to bookmark button.

- [ ] **Step 3: Commit**
  Run:
  ```bash
  git add frontend/src/pages/explore/tachidesk/hooks/useTachideskExplorer.ts frontend/src/pages/explore/tachidesk/components/MangaDetailDrawer.tsx
  git commit -m "feat: add status selector dropdown to explorer manga drawer"
  ```
