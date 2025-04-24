from django import forms

class RegistrationForm(forms.Form):
    birth_yaear = forms.IntergerField(label="出生年", min_value=1900, max_value=2100)
    birth_month = forms.IntegerField(label="出生月", min_value=1, max_value=12)
    birth_day = forms.IntegerField(label="出生日", min_value=1, max_value=31)
    birth_hour = forms.IntegerField(label="出生時", min_value=0, max_value=23)
    birth_minute = forms.IntegerField(label="出生分", min_value=0, max_value=59)
    birth_place = forms.CharField(label="出生地（城市名稱或經緯度）", max_length=100)