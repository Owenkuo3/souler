from django.shortcuts import render, redirect
from .forms import UserBirthInfoForm
from .models import UserBirthInfo
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from accounts.models import UserProfile


@login_required
def enter_birth_info(request):
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        return HttpResponse("尚未建立個人檔案，請聯絡管理員")
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
