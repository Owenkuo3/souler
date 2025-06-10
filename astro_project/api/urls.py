from django.urls import path
from .views import RegisterAPIView, current_user_info, request_verification_code, VerifyEmailCodeAPIView

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('me/', current_user_info, name='current_user_info'),
    path('request-verification-code/', request_verification_code),
    path('verify-code/', VerifyEmailCodeAPIView.as_view(), name='verify-code'),

]
