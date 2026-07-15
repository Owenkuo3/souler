import swisseph as swe
from datetime import datetime, timedelta

def calculate_full_chart(year, month, day, hour, minute, latitude, longitude):
    swe.set_ephe_path('.')

    local_dt = datetime(year, month, day, hour, minute)
    utc_dt = local_dt - timedelta(hours=8)

    utc_hour_float = utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_hour_float)

    planet_names = {
        swe.SUN: "太陽",
        swe.MOON: "月亮",
        swe.MERCURY: "水星",
        swe.VENUS: "金星",
        swe.MARS: "火星",
        swe.JUPITER: "木星",
        swe.SATURN: "土星",
        swe.URANUS: "天王星",
        swe.NEPTUNE: "海王星",
        swe.PLUTO: "冥王星",
    }

    signs = ["牡羊", "金牛", "雙子", "巨蟹", "獅子", "處女",
             "天秤", "天蠍", "射手", "魔羯", "水瓶", "雙魚"]

    cusps, ascmc = swe.houses(jd, latitude, longitude, b'P')

    result = {}
    for planet_id, name in planet_names.items():
        planet_pos, _ = swe.calc_ut(jd, planet_id)
        degree = planet_pos[0]
        zodiac_sign = int(degree / 30)

        house = get_house_from_degree(degree, cusps)

        result[name] = {
            "度數": round(degree, 4),
            "星座": signs[zodiac_sign],
            "宮位": house,
            "逆行": planet_pos[3] < 0,  # 黃經速度為負即逆行
        }

    # 加入上升、下降、天頂、天底
    asc = ascmc[0]
    mc = ascmc[1]
    dsc = (asc + 180) % 360
    ic = (mc + 180) % 360

    result["上升"] = {
        "度數": round(asc, 4),
        "星座": signs[int(asc / 30)]
    }
    result["下降"] = {
        "度數": round(dsc, 4),
        "星座": signs[int(dsc / 30)]
    }
    result["天頂"] = {
        "度數": round(mc, 4),
        "星座": signs[int(mc / 30)]
    }
    result["天底"] = {
        "度數": round(ic, 4),
        "星座": signs[int(ic / 30)]
    }

    return result


# 🧠 輔助函式：根據度數與 cusps 判斷落在哪一宮
def get_house_from_degree(degree, cusps):
    for i in range(12):
        start = cusps[i]
        end = cusps[(i + 1) % 12]
        if end < start:
            end += 360
        deg = degree
        if deg < start:
            deg += 360
        if start <= deg < end:
            return i + 1
    return 12  # fallback



def get_house_cusps(year, month, day, hour, minute, latitude, longitude):
    """回傳 12 個宮頭黃道度數（Placidus），供前端畫宮位分隔線。"""
    local_dt = datetime(year, month, day, hour, minute)
    utc_dt = local_dt - timedelta(hours=8)
    utc_hour_float = utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_hour_float)
    cusps, _ = swe.houses(jd, latitude, longitude, b'P')
    return [round(c, 4) for c in cusps[:12]]


def get_lat_lng_by_city(city_name):
    eng_name = city_name_mapping.get(city_name)
    if not eng_name:
        return (None, None)
    return city_coordinates.get(eng_name, (None, None))



city_name_mapping = {
    "台北": "Taipei",
    "高雄": "Kaohsiung",
    "台中": "Taichung",
    "澎湖": "Penghu",
    "金門": "Kinmen",
    "馬祖": "Matsu",
    "香港": "Hong Kong",
    "澳門": "Macau",
    "上海": "Shanghai",
    "北京": "Beijing",
    "紐約": "New York",
    "洛杉磯": "Los Angeles",
    "倫敦": "London",
    "巴黎": "Paris",
    "東京": "Tokyo",
    "悉尼": "Sydney",
    "首爾": "Seoul",
    "曼谷": "Bangkok",
    "新加坡": "Singapore",
    "吉隆坡": "Kuala Lumpur",
    "墨爾本": "Melbourne",
    "羅馬": "Rome",
    "柏林": "Berlin",
    "聖保羅": "Sao Paulo",
    "馬尼拉": "Manila",
    "開羅": "Cairo",
    "孟買": "Mumbai",
}

# 城市的經緯度 (簡單的例子)
city_coordinates = {
    "Taipei": (25.0330, 121.5654),  # 台北
    "Kaohsiung": (22.6273, 120.3014),  # 高雄
    "Taichung": (24.1477, 120.6736),  # 台中
    "Penghu": (23.5666, 119.5745),  # 澎湖
    "Kinmen": (24.4360, 118.3172),  # 金門
    "Matsu": (26.1540, 119.9505),  # 馬祖
    "Hong Kong": (22.3193, 114.1694),  # 香港
    "Macau": (22.1987, 113.5439),  # 澳門
    "Shanghai": (31.2304, 121.4737),  # 上海
    "Beijing": (39.9042, 116.4074),  # 北京
    "New York": (40.7128, -74.0060),  # 紐約
    "Los Angeles": (34.0522, -118.2437),  # 洛杉磯
    "London": (51.5074, -0.1278),  # 倫敦
    "Paris": (48.8566, 2.3522),  # 巴黎
    "Tokyo": (35.6762, 139.6503),  # 東京
    "Sydney": (-33.8688, 151.2093),  # 悉尼
    "Seoul": (37.5665, 126.9780),  # 首爾
    "Bangkok": (13.7563, 100.5018),  # 曼谷
    "Singapore": (1.3521, 103.8198),  # 新加坡
    "Kuala Lumpur": (3.1390, 101.6869),  # 吉隆坡
    "Melbourne": (-37.8136, 144.9631),  # 墨爾本
    "Rome": (41.9028, 12.4964),  # 羅馬
    "Berlin": (52.5200, 13.4050),  # 柏林
    "Sao Paulo": (-23.5505, -46.6333),  # 聖保羅
    "Manila": (14.5995, 120.9842),  # 馬尼拉
    "Cairo": (30.0444, 31.2357),  # 開羅
    "Mumbai": (19.0760, 72.8777),  # 孟買
}