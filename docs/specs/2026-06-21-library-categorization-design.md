# Spec: Library Categorization & Sorting

**Date:** 2026-06-21  
**Topic:** Organize manga collection into custom folders with filters and unread counters.

---

## 1. Overview & Goals

The goal is to allow users to organize their tracked manga collection into three predefined folders: "Reading" (En cours), "Plan to Read" (À lire), and "Completed" (Terminés). We will also show the number of unread chapters for each manga in their library based on their locally synchronized reading progress.

### Core Features:
- **Folder Categorization:** Group manga favorites into "Reading", "Completed", or "Plan to Read".
- **Auto-Transitions:** Automatically set status to "Reading" when progress is synced, and to "Completed" when the last chapter is read.
- **Unread Chapter Counter:** Display a dynamic count of unread chapters (chapters with a number greater than the user's last read chapter).
- **Library Dashboard UI:** Provide a beautiful dashboard to filter, search, and sort the manga collection.

---

## 2. Database Schema changes

We will modify the existing `FavoriteManga` model in `backend/api/animetix/models.py`:

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
```

---

## 3. Backend API Endpoints

### 3.1. Serializer (`FavoriteMangaSerializer`)
A new serializer is introduced to output favorites with their metadata:
* **Fields:** `id`, `manga` (serialized `MediaItem`), `status`, `last_read_chapter`, `unread_chapters_count`, `created_at`, `updated_at`.
* **Computed Field:** `unread_chapters_count` counts the database chapters associated with this manga that have a chapter number greater than `last_read_chapter`.

### 3.2. Favorites List Endpoint (`FavoriteMangaListView`)
* **Endpoint:** `GET /api/v1/media/favorites/`
* **Response:** Returns a list of all favorite records using `FavoriteMangaSerializer`.

### 3.3. Favorite Toggle & Update Endpoint (`FavoriteMangaToggleView`)
* **Endpoint:** `POST /api/v1/media/Manga/<str:media_id>/favorite/`
* **Payload:** Optional `{"status": "completed" | "reading" | "plan_to_read"}`
* **Behavior:**
  * If a `status` is provided, we create the `FavoriteManga` record (or update it if it already exists) with that status.
  * If no `status` is provided, we perform the standard toggle (delete if it exists, create if not).

### 3.4. Progress Sync Endpoint (`MangaChapterSyncView`)
* **Endpoint:** `POST /api/v1/media/Manga/<str:media_id>/chapters/<str:chapter_number>/sync/`
* **Behavior:**
  * Updates the `last_read_chapter` for the user's `FavoriteManga` record.
  * Auto-transition: Checks if any chapters exist for this manga with a number greater than the newly synced `chapter_number`. If none exist, the status is automatically set to `"completed"`. Otherwise, if status is currently `"plan_to_read"`, it is auto-transitioned to `"reading"`.

---

## 4. Frontend UI Components

### 4.1. Library Page (`MangaLibraryPage.tsx`)
A new React page located at `/media/manga/library/`. It features:
* **Folder Tabs:** "Tous", "En cours", "À lire", "Terminés", showing dynamic counts.
* **Control Bar:** Search filter input, and sort dropdown (Title, Unread Count, Date Added).
* **Grid:** Displays cards for each favorite manga.
* **Manga Cards:**
  * Show Cover image, title, and current folder badge.
  * **Unread Counter:** If unread count > 0, show a badge (e.g. `+12` in red/orange).
  * **"Continue" Action:** Button navigating to `/media/manga/{mediaId}/{last_read_chapter + 1}/` to resume reading.
  * **Folder Dropdown Selector:** Inline selector to move the manga to another folder or remove it.

### 4.2. Navigation Updates
* **Sidebar:** Add "Ma Bibliothèque" to the Exploration section in `SidebarDrawer.tsx`.
* **Detail Drawer:** Update `MangaDetailDrawer.tsx` to display a folder dropdown selector.

---

## 5. Testing & Validation Plan

### 5.1. Backend Tests
We will add tests in `tests/backend/api/test_manga_favorites_api.py` to cover:
- Fetching favorites returning the new fields (`status`, `last_read_chapter`, `unread_chapters_count`).
- Updating favorite status via POST payload.
- Syncing progress updating `last_read_chapter` and triggering the auto-transition to `completed`.

### 5.2. Frontend Tests
We will add/update tests for the frontend views to ensure components render correctly and handle filters and folder changes.
