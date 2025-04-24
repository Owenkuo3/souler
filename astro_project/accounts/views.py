from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .forms import RegistrationForm, LoginForm, UserProfileForm
from django.contrib.auth.decorators import login_required
from .models import UserProfile



def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('registration_success')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def registration_success(request):
    return render(request, 'accounts/registration_success.html')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('profile') # 之後定義這個 URL
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home') # 之後定義這個 URL

@login_required
def profile(request):
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile') # 重新導向到個人資料頁面
    else:
        form = UserProfileForm(instance=user_profile)

    return render(request, 'accounts/profile.html', {'form': form})