from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('register/success/', views.registration_success, name='registration_success'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),

]