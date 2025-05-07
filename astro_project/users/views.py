from django.shortcuts import render, redirect
from .forms import UserBirthInfoForm
from .models import UserBirthInfo
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile
from astrology.models import PlanetPosition
from .utils import calculate_full_chart
from astrology.services.birth_info_service import enrich_birth_info_with_coordinates_and_signs

@login_required
def enter_birth_info(request):
    user_profile = request.user.profile

    # 檢查是否已有出生資料，如果有就直接導向 profile 頁（防止重複進入）
    if hasattr(user_profile, 'birth_info'):
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = UserBirthInfoForm(request.POST)
        if form.is_valid():
            birth_info = form.save(commit=False)
            birth_info.user_profile = user_profile

            enrich_birth_info_with_coordinates_and_signs(birth_info)
            birth_info.save()

            # 計算星盤並寫入 PlanetPosition
            PlanetPosition.objects.filter(user_profile=user_profile).delete()
            chart_data = calculate_full_chart(birth_info)

            for planet, data in chart_data.items():
                PlanetPosition.objects.create(
                    user_profile=user_profile,
                    planet_name=planet,
                    zodiac_sign=data['星座'],
                    degree=data['度數'],
                    house=data['宮位']
                )

            return redirect('astrology:chart_result')
    else:
        form = UserBirthInfoForm()

    return render(request, 'users/enter_birth_info.html', {'form': form})
