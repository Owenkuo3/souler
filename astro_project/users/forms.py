from django import forms
from .models import UserBirthInfo

class UserBirthInfoForm(forms.ModelForm):
    class Meta:
        model = UserBirthInfo
        fields = [
            'birth_year', 'birth_month', 'birth_day',
            'birth_hour', 'birth_minute',
            'birth_location'
        ]
        widgets = {
            'birth_year': forms.NumberInput(attrs={'min': 1900, 'max': 2100}),
            'birth_month': forms.NumberInput(attrs={'min': 1, 'max': 12}),
            'birth_day': forms.NumberInput(attrs={'min': 1, 'max': 31}),
            'birth_hour': forms.NumberInput(attrs={'min': 0, 'max': 23}),
            'birth_minute': forms.NumberInput(attrs={'min': 0, 'max': 59}),
            'birth_location': forms.TextInput(attrs={'placeholder': '例如：台北市'}),
        }

