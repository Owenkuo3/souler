from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '註冊成功！請登入。')
            return redirect('login')  # 這邊預設有一個 login 頁面
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})
