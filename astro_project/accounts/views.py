from django.shortcuts import render
from .forms import RegistrationForm

def register(request):
    if request.method == 'POST':
        if form.is_valid():
            #
            cleaned_data = form.cleaned_data
            return render(request, 'accounts/result.html', {'data': cleaned_data})
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})