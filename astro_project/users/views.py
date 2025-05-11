from django.shortcuts import render, redirect
from .forms import UserBirthInfoForm
from .models import UserBirthInfo
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile
from astrology.models import PlanetPosition
from astrology.service.chart_service import generate_chart_and_save

@login_required
def enter_birth_info(request):
    user_profile = request.user.profile

    if hasattr(user_profile, 'birth_info'):
        birth_info.save()
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = UserBirthInfoForm(request.POST)
        if form.is_valid():
            birth_info = form.save(commit=False)
            birth_info.user_profile = user_profile
            birth_info.save()

            generate_chart_and_save(user_profile, birth_info)

            return redirect('astrology:chart_result')
    else:
        form = UserBirthInfoForm()

    return render(request, 'users/enter_birth_info.html', {'form': form})
