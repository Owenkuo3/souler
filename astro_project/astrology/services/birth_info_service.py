
from astrology.services.city_info_service import get_city_coordinates
from users.utils import calculate_full_chart

def enrich_birth_info_with_coordinates_and_signs(birth_info):
    city_name = birth_info.birth_location
    latitude, longitude = get_city_coordinates(city_name)
    
    if latitude and longitude:
        birth_info.birth_latitude = latitude
        birth_info.birth_longitude = longitude
    else:
        # 如果找不到城市的座標，可以記錄一個警告，或進行其他處理
        birth_info.birth_latitude = None
        birth_info.birth_longitude = None

    # 確保所有必要的出生資訊都已經填寫
    if all([
        birth_info.birth_year,
        birth_info.birth_month,
        birth_info.birth_day,
        birth_info.birth_hour,
        birth_info.birth_minute,
        birth_info.birth_latitude,
        birth_info.birth_longitude,
    ]):
        # 計算星盤資料
        chart = calculate_full_chart(
            birth_info.birth_year,
            birth_info.birth_month,
            birth_info.birth_day,
            birth_info.birth_hour,
            birth_info.birth_minute,
            float(birth_info.birth_latitude),
            float(birth_info.birth_longitude),
        )

        # 檢查 chart 是否包含所有必要的資料
        if chart:
            birth_info.sun_sign = chart.get("太陽", {}).get("星座", "")
            birth_info.moon_sign = chart.get("月亮", {}).get("星座", "")
            birth_info.mercury_sign = chart.get("水星", {}).get("星座", "")
            birth_info.venus_sign = chart.get("金星", {}).get("星座", "")
            birth_info.mars_sign = chart.get("火星", {}).get("星座", "")
            birth_info.jupiter_sign = chart.get("木星", {}).get("星座", "")
            birth_info.saturn_sign = chart.get("土星", {}).get("星座", "")
            birth_info.uranus_sign = chart.get("天王星", {}).get("星座", "")
            birth_info.neptune_sign = chart.get("海王星", {}).get("星座", "")
            birth_info.pluto_sign = chart.get("冥王星", {}).get("星座", "")
            birth_info.ascendant_sign = chart.get("上升", {}).get("星座", "")
            birth_info.descendant_sign = chart.get("下降", {}).get("星座", "")
            birth_info.mc_sign = chart.get("天頂", {}).get("星座", "")
            birth_info.ic_sign = chart.get("天底", {}).get("星座", "")

            # 儲存更新後的出生資訊
            birth_info.save()

    return birth_info
