from django.shortcuts import render
from .models import PlanetPosition
from .utils.chart_drawer import draw_chart

def user_chart_view(request):
    user = request.user
    planets = PlanetPosition.objects.filter(user_profile=user.profile)

    chart_img = draw_chart(planets)

    return render(request, 'astrology/user_chart.html', {
        'chart_img': chart_img
    })
