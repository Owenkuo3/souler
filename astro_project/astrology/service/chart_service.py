# astrology/service/chart_service.py

from astrology.models import PlanetPosition
from users.utils import calculate_full_chart

def generate_chart_and_save(user_profile, birth_info):
    if birth_info.birth_latitude is None or birth_info.birth_longitude is None:
        raise ValueError("缺少經緯度資料，無法產生星盤")
    birth_info.save()

    year = birth_info.birth_year
    month = birth_info.birth_month
    day = birth_info.birth_day
    hour = birth_info.birth_hour
    minute = birth_info.birth_minute
    latitude = float(birth_info.birth_latitude)
    longitude = float(birth_info.birth_longitude)
    
    # 呼叫 calculate_full_chart 並傳入拆開的資料
    chart_data = calculate_full_chart(
        year, month, day, hour, minute, latitude, longitude
    )
    
    # 刪除舊的 PlanetPosition 資料
    PlanetPosition.objects.filter(user_profile=user_profile).delete()
    
    # 創建新的 PlanetPosition 資料
    for planet, data in chart_data.items():
        degree = data['度數']
        correct_degree = degree % 30

        house = data.get('宮位', None)  # 如果不存在則返回 None
        PlanetPosition.objects.create(
            user_profile=user_profile,
            planet_name=planet,
            zodiac_sign=data['星座'],
            degree=degree,  # 原始度數
            correct_degree=correct_degree,  # 修正後的度數
            house=house,  # 如果 '宮位' 為 None，則存入 None
        )