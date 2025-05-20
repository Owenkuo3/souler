from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

class LoginForm(AuthenticationForm):
    pass

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['nickname', 'gender', 'match_gender', 'photo', 'bio']

    match_gender = forms.ChoiceField(
        choices=[
            ('M', '只配對男生'),
            ('F', '只配對女生'),
            ('O', '只配對其他性別'),
            ('A', '不限性別')
        ],
        label='配對對象性別',
        widget=forms.Select()
    )