from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer, UserSerializer


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        # Support login by email
        if "@" in username:
            try:
                user_obj = User.objects.get(email__iexact=username)
                username = user_obj.username
            except User.DoesNotExist:
                pass

        user = authenticate(
            request,
            username=username,
            password=password,
        )
        if user is None:
            return Response(
                {"success": False, "message": "Credenciales invalidas."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return Response(
                {"code": "USER_INACTIVE", "message": "Usuario inactivo. Contacte al administrador."},
                status=status.HTTP_403_FORBIDDEN,
            )

        client = request.data.get("client", "mobile")

        if client == "web":
            if not user.is_staff and not user.is_superuser:
                return Response(
                    {"code": "ACCESS_DENIED", "message": "Acceso denegado. Este usuario no tiene permisos web."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:  # client == "mobile"
            seller_profile = getattr(user, "seller_profile", None)
            if not seller_profile or not seller_profile.is_seller:
                return Response(
                    {"code": "ACCESS_DENIED", "message": "Acceso denegado. Este usuario no tiene permisos moviles."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if seller_profile.is_blocked:
                return Response(
                    {"code": "USER_BLOCKED", "message": "Usuario bloqueado. Contacte al administrador."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "success": True,
                "data": {
                    "accessToken": str(refresh.access_token),
                    "refreshToken": str(refresh),
                    "user": UserSerializer(user).data,
                },
            }
        )


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, "seller_profile", None)
        if profile and profile.is_blocked:
            return Response(
                {"code": "USER_BLOCKED", "message": "Usuario bloqueado. Contacte al administrador."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response({"success": True, "data": UserSerializer(request.user).data})
