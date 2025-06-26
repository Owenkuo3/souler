from django.urls import path
from .views import RegisterAPIView, VerifyEmailCodeAPIView, RequestEmailVerificationCodeView, UserProfileView, UserBirthInfoView, NatalChartView, MatchCandidatesView, MatchActionView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('request-verification-code/', RequestEmailVerificationCodeView.as_view(), name='request-code'),
    path('verify-code/', VerifyEmailCodeAPIView.as_view(), name='verify-code'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'), 
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    path('user/profile/', UserProfileView.as_view(), name='update_user_profile'),
    path('birth-info/', UserBirthInfoView.as_view(), name='birth-info'),
    path('natal-chart/', NatalChartView.as_view(), name='natal-chart'),
    path('candidates/', MatchCandidatesView.as_view(), name='match-candidates'),
    path('match/action/', MatchActionView.as_view(), name='match-action'),

]
