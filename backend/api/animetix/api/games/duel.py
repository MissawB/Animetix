import random
import string

from dependency_injector.wiring import Provide, inject
from rest_framework import permissions, response, status, views

from ...containers import Container
from ...models import DuelRoom


def generate_room_code():
    return "".join(
        random.choices(string.ascii_uppercase + string.digits, k=6)
    )  # nosec B311


class CreateDuelRoomView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @inject
    def post(self, request, catalog_service=Provide[Container.core.catalog_service]):
        media_type = request.data.get("media_type", "anime")

        # Sélection d'un titre secret aléatoire
        data = catalog_service.load_data(media_type)
        if not data:
            return response.Response(
                {"detail": "Invalid media type."}, status=status.HTTP_400_BAD_REQUEST
            )

        titles = list(data["title_to_full_data"].keys())
        secret_title = random.choice(titles)  # nosec B311

        room_code = generate_room_code()
        while DuelRoom.objects.filter(room_code=room_code).exists():
            room_code = generate_room_code()

        room = DuelRoom.objects.create(
            room_code=room_code,
            player1=request.user,
            media_type=media_type,
            secret_title=secret_title,
        )

        return response.Response(
            {"room_code": room.room_code, "media_type": room.media_type},
            status=status.HTTP_201_CREATED,
        )


class JoinDuelRoomView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        room_code = request.data.get("room_code")
        if not room_code:
            return response.Response(
                {"detail": "room_code is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            room = DuelRoom.objects.get(room_code=room_code, is_finished=False)
        except DuelRoom.DoesNotExist:
            return response.Response(
                {"detail": "Room not found or already finished."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if room.player1 == request.user:
            return response.Response(
                {"detail": "You are already in this room."}, status=status.HTTP_200_OK
            )

        if room.player2 and room.player2 != request.user:
            return response.Response(
                {"detail": "Room is full."}, status=status.HTTP_400_BAD_REQUEST
            )

        room.player2 = request.user
        room.save()

        return response.Response(
            {"room_code": room.room_code, "media_type": room.media_type}
        )


class MatchmakingView(views.APIView):
    """Trouve une salle disponible ou en crée une."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        media_type = request.data.get("media_type", "anime")

        # Chercher une salle avec un seul joueur
        room = (
            DuelRoom.objects.filter(
                media_type=media_type, player2__isnull=True, is_finished=False
            )
            .exclude(player1=request.user)
            .first()
        )

        if room:
            room.player2 = request.user
            room.save()
            return response.Response(
                {"room_code": room.room_code, "media_type": room.media_type}
            )

        # Sinon, créer une nouvelle salle
        return CreateDuelRoomView().post(request)
