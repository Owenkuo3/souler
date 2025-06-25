from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .forms import RegistrationForm, LoginForm, UserProfileForm
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from users.forms import UserBirthInfoForm  
from users.models import UserBirthInfo
from astrology.models import PlanetPosition
from users.utils import calculate_full_chart
from astrology.service.chart_service import generate_chart_and_save


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
    user_profile = request.user.profile
    birth_info = getattr(user_profile, 'birth_info', None)

    if request.method == 'POST':
        birth_form = UserBirthInfoForm(request.POST, instance=birth_info)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)

        if birth_form.is_valid() and profile_form.is_valid():
            profile_form.save()
            birth = birth_form.save(commit=False)
            birth.user_profile = user_profile
            birth.save()  # 此時會觸發 birth_info model 裡的 save()，寫入經緯度
        
            generate_chart_and_save(user_profile, birth)


            return redirect('astrology:chart_result')
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