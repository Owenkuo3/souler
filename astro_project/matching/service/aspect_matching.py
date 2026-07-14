# matching/services/aspect_matching.py

from users.models import UserProfile
from astrology.models import PlanetPosition
from math import fabs

# 相位定義（含容許度與分數）
ASPECTS = [
    {"name": "Conjunction", "angle": 0, "orb": 6, "score": 5},       # 中性，視行星
    {"name": "Sextile", "angle": 60, "orb": 6, "score": 4},          # 正面
    {"name": "Square", "angle": 90, "orb": 6, "score": -3},          # 負面
    {"name": "Trine", "angle": 120, "orb": 6, "score": 5},           # 正面
    {"name": "Opposition", "angle": 180, "orb": 6, "score": -2},     # 負面（吸引力）
    {"name": "Semi-Sextile", "angle": 30, "orb": 3, "score": 1},     # 弱正面
    {"name": "Semi-Square", "angle": 45, "orb": 3, "score": -1},     # 弱負面
    {"name": "Quincunx", "angle": 150, "orb": 3, "score": -2},       # 不理解
]

# 行星權重（主星 → 外行星）
# 鍵必須與 PlanetPosition.planet_name 存的中文名一致（見 users/utils.py 的 planet_names）
PLANET_WEIGHTS = {
    "太陽": 1.5, "月亮": 1.5,
    "水星": 1.0, "金星": 1.2, "火星": 1.2,
    "木星": 0.8, "土星": 0.8,
    "天王星": 0.5, "海王星": 0.5, "冥王星": 0.5,
    "上升": 1.5, "下降": 1.5, "天頂": 1.0, "天底": 1.0,
}

def get_user_planets(user_profile):
    return PlanetPosition.objects.filter(user_profile=user_profile)

def calculate_aspect(deg1, deg2):
    diff = fabs(deg1 - deg2)
    if diff > 180:
        diff = 360 - diff
    for aspect in ASPECTS:
        if fabs(diff - aspect["angle"]) <= aspect["orb"]:
            return aspect
    return None

def get_planet_weight(planet_name):
    return PLANET_WEIGHTS.get(planet_name, 1.0)  # 預設為 1.0

def calculate_match_score(user_a_profile, user_b_profile):
    planets_a = get_user_planets(user_a_profile)
    planets_b = get_user_planets(user_b_profile)

    total_score = 0
    matched_aspects = []

    for pa in planets_a:
        for pb in planets_b:
            # 相位要用完整黃道度數 (0-360) 計算；correct_degree 是星座內度數 (0-30)，只能用於顯示
            aspect = calculate_aspect(pa.degree, pb.degree)
            if aspect:
                base_score = aspect["score"]
                weight = (get_planet_weight(pa.planet_name) + get_planet_weight(pb.planet_name)) / 2
                weighted_score = base_score * weight

                total_score += weighted_score

                matched_aspects.append({
                    "planet_a": pa.planet_name,
                    "planet_b": pb.planet_name,
                    "aspect": aspect["name"],
                    "base_score": base_score,
                    "weight": round(weight, 2),
                    "score": round(weighted_score, 2),
                })

    return round(total_score, 2), matched_aspects
