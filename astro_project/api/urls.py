from django.urls import path
from .views import RegisterAPIView, VerifyEmailCodeAPIView, RequestEmailVerificationCodeView, UserProfileView, UserBirthInfoView, NatalChartView, MatchCandidatesView, MatchActionView
from rest_framework_simplejwt.views import TokenRefreshView
from .views import ChatRoomListView, ChatRoomMessageView, MyTokenObtainPairView

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('request-verification-code/', RequestEmailVerificationCodeView.as_view(), name='request-code'),
    path('verify-code/', VerifyEmailCodeAPIView.as_view(), name='verify-code'),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'), 
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    path('user/profile/', UserProfileView.as_view(), name='update_user_profile'),
    path('birth-info/', UserBirthInfoView.as_view(), name='birth-info'),
    path('natal-chart/', NatalChartView.as_view(), name='natal-chart'),
    path('candidates/', MatchCandidatesView.as_view(), name='match-candidates'),
    path('match/action/', MatchActionView.as_view(), name='match-action'),
    path("chatrooms/", ChatRoomListView.as_view(), name="chatroom-list"),
    path("chatrooms/<int:room_id>/messages/", ChatRoomMessageView.as_view(), name="chatroom-messages"),

]
