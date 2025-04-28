import swisseph as swe
import datetime

def calculate_sun_sign(year, month, day, hour, minute, second, latitude, longitude):
    swe.set_ephe_path('.')  # 可以指向 Swiss Ephemeris 資料庫的位置
    utc_time = datetime.datetime(year, month, day, hour, minute, second)
    jd = swe.julday(utc_time.year, utc_time.month, utc_time.day, 
                    utc_time.hour + utc_time.minute / 60 + utc_time.second / 3600)
    planet_pos = swe.calc_ut(jd, swe.SUN)[0]  # 取得太陽位置（黃道度數）

    # 根據度數判斷星座
    signs = ["牡羊", "金牛", "雙子", "巨蟹", "獅子", "處女",
             "天秤", "天蠍", "射手", "魔羯", "水瓶", "雙魚"]
    sign_index = int(planet_pos / 30)
    return signs[sign_index]


def get_lat_lng_by_city(city_name):

    return city_coordinates.get(city_name, (None, None))

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