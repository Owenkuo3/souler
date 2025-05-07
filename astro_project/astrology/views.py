from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import PlanetPosition
from .utils.chart_drawer import draw_chart 

@login_required
def chart_result(request):
    user_profile = request.user.profile
    planet_positions = PlanetPosition.objects.filter(user_profile=user_profile)

    chart_img = draw_chart(planet_positions)  # 把圖畫出來轉 base64

    return render(request, 'astrology/chart_result.html', {
        'planet_positions': planet_positions,
        'chart_img': chart_img
    })