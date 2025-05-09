from astrology.models import PlanetPosition
from users.utils import calculate_full_chart

def generate_chart_and_save(user_profile, birth_info):
    birth_info.save()
    chart_data = calculate_full_chart(birth_info)
    PlanetPosition.objects.filter(user_profile=user_profile).delete()
    for planet, data in chart_data.items():
        PlanetPosition.objects.create(
            user_profile=user_profile,
            planet_name=planet,
            zodiac_sign=data['星座'],
            degree=data['度數'],
            house=data['宮位']
        )
