from users.utils import calculate_full_chart, city_name_mapping, get_lat_lng_by_city

def enrich_birth_info_with_coordinates_and_signs(birth_info):
    """
    根據使用者輸入的出生地點與時間，自動補上經緯度與星座資料
    """
    if birth_info.birth_location:
        english_city = city_name_mapping.get(birth_info.birth_location, birth_info.birth_location)
        lat, lng = get_lat_lng_by_city(english_city)

        if lat is not None and lng is not None:
            birth_info.birth_latitude = lat
            birth_info.birth_longitude = lng
        else:
            birth_info.birth_latitude = None
            birth_info.birth_longitude = None

    if all([
        birth_info.birth_year,
        birth_info.birth_month,
        birth_info.birth_day,
        birth_info.birth_hour,
        birth_info.birth_minute,
        birth_info.birth_latitude,
        birth_info.birth_longitude,
    ]):
        chart = calculate_full_chart(
            birth_info.birth_year,
            birth_info.birth_month,
            birth_info.birth_day,
            birth_info.birth_hour,
            birth_info.birth_minute,
            float(birth_info.birth_latitude),
            float(birth_info.birth_longitude),
        )

        birth_info.sun_sign = chart["太陽"]["星座"]
        birth_info.moon_sign = chart["月亮"]["星座"]
        birth_info.mercury_sign = chart["水星"]["星座"]
        birth_info.venus_sign = chart["金星"]["星座"]
        birth_info.mars_sign = chart["火星"]["星座"]
        birth_info.jupiter_sign = chart["木星"]["星座"]
        birth_info.saturn_sign = chart["土星"]["星座"]
        birth_info.uranus_sign = chart["天王星"]["星座"]
        birth_info.neptune_sign = chart["海王星"]["星座"]
        birth_info.pluto_sign = chart["冥王星"]["星座"]
        birth_info.ascendant_sign = chart.get("上升")["星座"]
        birth_info.descendant_sign = chart.get("下降")["星座"]
        birth_info.mc_sign = chart.get("天頂")["星座"]
        birth_info.ic_sign = chart.get("天底")["星座"]

    return birth_info
