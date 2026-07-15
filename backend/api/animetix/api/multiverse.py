from dependency_injector.wiring import Provide, inject
from django.http import FileResponse, Http404
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from ..containers import Container
from ..presenters import MultiversePresenter


class MultiverseGalleryView(APIView):
    # Public catalogue browsing: GET stays open, writes (if any) require auth.
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @inject
    def __init__(
        self,
        multiverse_service=Provide[Container.core.multiverse_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.multiverse_service = multiverse_service

    def get(self, request):
        results = self.multiverse_service.get_gallery_raw_data()
        data = MultiversePresenter.format_gallery_data(results)
        return Response(data)


class MultiverseCatalogView(APIView):
    """
    GET /api/v1/multiverse/catalog/
    Paginated, filterable, searchable catalog of synthetic universes.

    Query params:
      - search: text search on name/description/cosmology
      - genre: filter by genre name (exact match)
      - sort: 'newest' | 'name' | 'characters' (default: newest)
      - page: page number (1-indexed, default: 1)
      - page_size: items per page (default: 12, max: 48)
    """

    # Public catalogue browsing: GET stays open, writes (if any) require auth.
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @inject
    def __init__(
        self,
        multiverse_service=Provide[Container.core.multiverse_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.multiverse_service = multiverse_service

    def get(self, request):
        # Parse query params
        search = request.query_params.get("search", "").strip()
        genre_filter = request.query_params.get("genre", "").strip()
        sort_by = request.query_params.get("sort", "newest")
        try:
            page = max(1, int(request.query_params.get("page", 1)))
        except (ValueError, TypeError):
            page = 1
        try:
            page_size = min(48, max(1, int(request.query_params.get("page_size", 12))))
        except (ValueError, TypeError):
            page_size = 12

        results, total, genre_results = self.multiverse_service.get_catalog_raw_data(
            search=search,
            genre_filter=genre_filter,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
        )

        data = MultiversePresenter.format_catalog_data(
            results=results,
            total=total,
            page=page,
            page_size=page_size,
            search=search,
            genre_filter=genre_filter,
            sort_by=sort_by,
            genre_results=genre_results,
        )

        return Response(data)


class MultiverseExportPDFView(APIView):
    """
    GET /api/v1/multiverse/<str:universe_name>/export-pdf/
    Génère et télécharge une fiche scénaristique PDF stylisée comme un Wiki
    contenant la description, la cosmologie, les personnages et les relations Neo4j.
    """

    # Public catalogue browsing: GET stays open, writes (if any) require auth.
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @inject
    def __init__(
        self,
        multiverse_service=Provide[Container.core.multiverse_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.multiverse_service = multiverse_service

    def get(self, request, universe_name):
        raw_data = self.multiverse_service.get_universe_pdf_raw_data(universe_name)
        if not raw_data:
            raise Http404("Univers synthétique non trouvé.")

        buffer = MultiversePresenter.generate_lore_pdf(universe_name, raw_data)

        # Clean file name
        safe_filename = "".join(
            c for c in universe_name if c.isalnum() or c in (" ", "_", "-")
        ).rstrip()
        safe_filename = safe_filename.replace(" ", "_")
        if not safe_filename:
            safe_filename = "multiverse_lore"

        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f"wiki_{safe_filename}.pdf",
            content_type="application/pdf",
        )
