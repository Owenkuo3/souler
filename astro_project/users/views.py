from django.shortcuts import render, redirect
from .forms import UserBirthInfoForm
from .models import UserBirthInfo
from django.contrib.auth.decorators import login_required

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
