import datetime
import mimetypes
import os

from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView


class OpenDatasetListView(APIView):
    """
    List public datasets available for academic compliance.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        datasets_dir = os.path.join(settings.BASE_DIR, "data", "mlops", "datasets")

        # Explicit file mapping for safety
        allowed_files = {
            "dpo_pairs": {
                "filename": "dpo_train_validated.jsonl",
                "display_name": "Paires DPO (Alignement RLHF)",
                "description": "Paires de préférences validées (choisies vs rejetées) pour l'alignement des modèles de recommandation d'anime.",
                "format": "JSONL",
            },
            "anonymized_logs": {
                "filename": "gameplay_sessions.jsonl",
                "display_name": "Logs de session anonymisés",
                "description": "Traces anonymisées de sessions d'interaction et de jeu pour la recherche sur le comportement utilisateur.",
                "format": "JSONL",
            },
        }

        data = []
        for key, info in allowed_files.items():
            file_path = os.path.join(datasets_dir, info["filename"])
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                data.append(
                    {
                        "id": key,
                        "name": info["display_name"],
                        "description": info["description"],
                        "format": info["format"],
                        "size_bytes": stat.st_size,
                        "updated_at": datetime.datetime.fromtimestamp(
                            stat.st_mtime
                        ).isoformat(),
                    }
                )

        return Response({"status": "success", "datasets": data})


class OpenDatasetDownloadView(APIView):
    """
    Download a public dataset file.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, dataset_id):
        datasets_dir = os.path.join(settings.BASE_DIR, "data", "mlops", "datasets")

        allowed_files = {
            "dpo_pairs": "dpo_train_validated.jsonl",
            "anonymized_logs": "gameplay_sessions.jsonl",
        }

        if dataset_id not in allowed_files:
            raise Http404("Dataset not found")

        filename = allowed_files[dataset_id]
        file_path = os.path.join(datasets_dir, filename)

        if not os.path.exists(file_path):
            raise Http404("File does not exist")

        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        response = FileResponse(open(file_path, "rb"), content_type=mime_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
