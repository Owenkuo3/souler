from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .forms import RegistrationForm, LoginForm, UserProfileForm
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from users import templates
from users.forms import UserBirthInfoForm  
from users.models import UserBirthInfo
from astrology import templates

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, nickname=user.username)
            
            login(request, user)
            return redirect('profile')
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
    user = request.user
    user_profile = user.profile

    try:
        birth_info = user_profile.birth_info
    except UserBirthInfo.DoesNotExist:
        birth_info = None

    # 表單資料傳入
    if request.method == 'POST':
        birth_form = UserBirthInfoForm(request.POST, instance=birth_info)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)

        if birth_form.is_valid() and profile_form.is_valid():
            # 儲存個人資料
            profile_form.save()

            # 儲存星盤資料（補上 user_profile）
            birth = birth_form.save(commit=False)
            birth.user_profile = user_profile
            birth.save()

            return redirect('user_chart')
    else:
        birth_form = UserBirthInfoForm(instance=birth_info)
        profile_form = UserProfileForm(instance=user_profile)

    return render(request, 'accounts/profile.html', {
        'birth_form': birth_form,
        'profile_form': profile_form,
        'birth_info': birth_info,
    })



def home(request):
    return render(request, 'home.html')