from django.urls import path
from .views import RegisterAPIView, VerifyEmailCodeAPIView, RequestEmailVerificationCodeView, CurrentUserProfileView, UpdateUserProfileView, UserBirthInfoView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('me/profile/', CurrentUserProfileView.as_view(), name='current_user_profile'),
    path('request-verification-code/', RequestEmailVerificationCodeView.as_view(), name='request-code'),
    path('verify-code/', VerifyEmailCodeAPIView.as_view(), name='verify-code'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'), 
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    path('me/profile/update/', UpdateUserProfileView.as_view(), name='update_user_profile'),
    path('birth-info/', UserBirthInfoView.as_view(), name='birth-info'),

]
