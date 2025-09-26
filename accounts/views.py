# accounts/views.py
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import RegisterSerializer, UserSerializer
from .models import Role

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    Register a new user, assign default role (id=2), and return tokens.
    """
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Register new user",
        operation_description="Creates a user, assigns role id=2, and returns JWT tokens with user info.",
        responses={201: "Tokens + user info"},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Assign default role (id=2)
        try:
            default_role = Role.objects.get(id=2)
            user.profile.add_role(default_role)
        except Role.DoesNotExist:
            pass  # Skip if missing

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "username": user.username,
            "email": user.email,
            "roles": [r.slug for r in user.profile.get_active_roles()],
        }
        return Response(data, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom login serializer to allow login with email or username.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["email"] = user.email
        token["roles"] = [r.slug for r in user.profile.get_active_roles()]
        return token

    def validate(self, attrs):
        credentials = {
            "username": attrs.get("username"),
            "password": attrs.get("password"),
        }

        # If "username" is email → resolve to real username
        if credentials["username"] and "@" in credentials["username"]:
            try:
                user = User.objects.get(email=credentials["username"])
                credentials["username"] = user.username
            except User.DoesNotExist:
                pass

        return super().validate(credentials)


class ObtainTokenPairView(TokenObtainPairView):
    """
    Login with username or email.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class RefreshTokenView(TokenRefreshView):
    """
    Refresh access token.
    """
    permission_classes = [permissions.AllowAny]


class UserDetailView(APIView):
    """
    Return logged-in user info with profile & roles.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get current user",
        operation_description="Returns the logged-in user's profile and roles.",
        responses={200: UserSerializer()},
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class LogoutView(APIView):
    """
    Logout: Blacklist the given refresh token.
    Body: {"refresh": "<refresh_token>"}
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Logout user",
        operation_description="Blacklists the refresh token so it can’t be reused.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "refresh": openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token"),
            },
            required=["refresh"],
        ),
        responses={
            205: openapi.Response("Successfully logged out"),
            400: openapi.Response("Invalid or expired token"),
        },
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "Refresh token required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"detail": "Successfully logged out."},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except Exception:
            return Response(
                {"detail": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
