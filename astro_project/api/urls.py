from django.urls import path
from .views import RegisterAPIView, VerifyEmailCodeAPIView, VerifyEmailCodeAPIView, CurrentUserProfileView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('me/profile/', CurrentUserProfileView.as_view(), name='current_user_profile'),
    path('request-verification-code/', VerifyEmailCodeAPIView.as_view(), name='request-code'),
    path('verify-code/', VerifyEmailCodeAPIView.as_view(), name='verify-code'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # 登入
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # 刷新 access token

]
