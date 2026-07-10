"""Session-auth endpoints (login/logout/register/me) and game-session state."""

from animetix_project.logging_config import get_logger
from django.contrib.auth import authenticate, login, logout  # noqa: E402
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django_ratelimit.decorators import ratelimit  # noqa: E402
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from animetix.api.dependencies import get_session_service  # noqa: E402

from ...serializers import ProfileSerializer

logger = get_logger("animetix.api")


class GameSessionView(APIView):
    """Endpoint pour gérer l'état du jeu via API."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        # Récupère l'état actuel de la session via le service de session
        session = get_session_service(request)
        return Response(
            {
                "media_type": session.get("media_type"),
                "is_ranked": session.get("is_ranked"),
                "is_daily": session.get("is_daily"),
                "game_over": session.get("game_over"),
                "guess_count": len(session.get("guesses", [])),
            }
        )


@method_decorator(ensure_csrf_cookie, name="dispatch")
@method_decorator(
    ratelimit(key="ip", rate="5/m", method="POST", block=True), name="dispatch"
)
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({"success": True})
        return Response(
            {"success": False, "error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"success": True})


@method_decorator(ensure_csrf_cookie, name="dispatch")
@method_decorator(
    ratelimit(key="ip", rate="5/m", method="POST", block=True), name="dispatch"
)
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if not username or not password or not email:
            return Response(
                {"success": False, "error": "Missing fields"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"success": False, "error": "Username already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.create_user(
                username=username, email=email, password=password
            )
            login(request, user)
            return Response({"success": True})
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CurrentUserView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            serializer = ProfileSerializer(request.user.profile)
            return Response(serializer.data)
        return Response(
            {"detail": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
        )
