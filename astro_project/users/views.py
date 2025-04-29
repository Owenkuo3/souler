from django.shortcuts import render, redirect
from .forms import UserBirthInfoForm
from .models import UserBirthInfo
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from accounts.models import UserProfile


@login_required
def enter_birth_info(request):
    user_profile = request.user.profile  # 假設你有用 OneToOne 連接 UserProfile

    try:
        birth_info = user_profile.birth_info
        form = UserBirthInfoForm(instance=birth_info)
    except UserBirthInfo.DoesNotExist:
        form = UserBirthInfoForm()

    if request.method == 'POST':
        form = UserBirthInfoForm(request.POST, instance=getattr(user_profile, 'birth_info', None))
        if form.is_valid():
            birth_info = form.save(commit=False)
            birth_info.user_profile = user_profile
            birth_info.save()
            return redirect('profile') 

    return render(request, 'users/enter_birth_info.html', {'form': form})

def test_birth_info(request):
    user_profile = UserProfile.objects.get(id=5)

    # 刪掉舊資料（開發測試方便用，正式環境別這樣）
    UserBirthInfo.objects.filter(user_profile=user_profile).delete()

    info = UserBirthInfo(
        user_profile=user_profile,
        birth_year=1990, birth_month=1, birth_day=1,
        birth_hour=12, birth_minute=0,
        birth_location='台北'
    )
    info.save()

    return HttpResponse(f"{info.zodiac_sign} / {info.moon_sign}")