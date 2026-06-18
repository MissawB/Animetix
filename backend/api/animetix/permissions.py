from rest_framework import permissions
from django.conf import settings


class IsIAPApprovedAdmin(permissions.BasePermission):
    """
    Permission stricte qui vérifie si l'utilisateur a son email dans IAP_APPROVED_ADMIN_EMAILS.
    Protège contre les élévations de privilèges accidentelles via d'autres backends d'auth.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Si on est en développement local, on se contente du is_staff classique
        if not getattr(settings, "IS_PRODUCTION", False):
            return request.user.is_staff

        approved_admins = getattr(settings, "IAP_APPROVED_ADMIN_EMAILS", [])
        return request.user.is_staff and request.user.email in approved_admins


class IsExpertUser(permissions.BasePermission):
    """
    Permission check for Expert tier users.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if staff/admin (admins are experts by default)
        if request.user.is_staff:
            return True

        # Check user tier in profile
        try:
            return getattr(request.user.profile, "tier", "free") == "expert"
        except Exception:
            return False


class IsAdminOrReadOnlyExpert(permissions.BasePermission):
    """
    Allows full access to admins, and read-only access to Expert users.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_staff:
            return True

        if request.method in permissions.SAFE_METHODS:
            try:
                return getattr(request.user.profile, "tier", "free") == "expert"
            except Exception:
                return False

        return False
