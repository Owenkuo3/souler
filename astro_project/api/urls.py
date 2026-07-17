from django.urls import path
from .views import RegisterAPIView, VerifyEmailCodeAPIView, RequestEmailVerificationCodeView, UserProfileView, UserBirthInfoView, NatalChartView, ChartInterpretationView, MatchCandidatesView, MatchActionView, CityListView
from rest_framework_simplejwt.views import TokenRefreshView
from .views import ChatRoomListView, ChatRoomMessageView, ChatRoomReadView, MyTokenObtainPairView, SynastryInterpretationView, UserPhotoView, UserPhotoDetailView

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('request-verification-code/', RequestEmailVerificationCodeView.as_view(), name='request-code'),
    path('verify-code/', VerifyEmailCodeAPIView.as_view(), name='verify-code'),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'), 
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    path('user/profile/', UserProfileView.as_view(), name='update_user_profile'),
    path('user/photos/', UserPhotoView.as_view(), name='user-photos'),
    path('user/photos/<int:photo_id>/', UserPhotoDetailView.as_view(), name='user-photo-detail'),
    path('birth-info/', UserBirthInfoView.as_view(), name='birth-info'),
    path('cities/', CityListView.as_view(), name='city-list'),
    path('natal-chart/', NatalChartView.as_view(), name='natal-chart'),
    path('natal-chart/interpretation/', ChartInterpretationView.as_view(), name='natal-chart-interpretation'),
    path('candidates/', MatchCandidatesView.as_view(), name='match-candidates'),
    path('match/action/', MatchActionView.as_view(), name='match-action'),
    path("chatrooms/", ChatRoomListView.as_view(), name="chatroom-list"),
    path("chatrooms/<int:room_id>/messages/", ChatRoomMessageView.as_view(), name="chatroom-messages"),
    path("chatrooms/<int:room_id>/read/", ChatRoomReadView.as_view(), name="chatroom-read"),
    path("chatrooms/<int:room_id>/synastry/", SynastryInterpretationView.as_view(), name="chatroom-synastry"),

]
