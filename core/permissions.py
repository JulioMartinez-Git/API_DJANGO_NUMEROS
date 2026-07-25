from rest_framework.permissions import BasePermission


class IsActiveSeller(BasePermission):
    message = {
        "code": "USER_BLOCKED",
        "message": "Usuario bloqueado. Contacte al administrador.",
    }

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            return False

        profile = getattr(user, "seller_profile", None)
        if not profile or not profile.is_seller or not profile.is_active or profile.is_blocked:
            return False

        return True
