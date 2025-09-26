from django.urls import path
from .views import RegisterView, ObtainTokenPairView, RefreshTokenView, UserDetailView, LogoutView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth_register"),
    path("login/", ObtainTokenPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token_refresh"),
    path("me/", UserDetailView.as_view(), name="user_detail"),
    path("logout/", LogoutView.as_view(), name="auth_logout"),  # ✅ logout endpoint
]
