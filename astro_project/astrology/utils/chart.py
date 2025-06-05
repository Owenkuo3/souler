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

    # 計算宮位
    cusps, ascmc = swe.houses(jd, latitude, longitude, b'P')

    result = {}
    for planet_id, name in planet_names.items():
        planet_pos, _ = swe.calc_ut(jd, planet_id)
        degree = planet_pos[0]
        zodiac_sign = int(degree / 30)

        # 宮位計算邏輯
        house = get_house_from_degree(degree, cusps)

        result[name] = {
            "度數": round(degree, 4),
            "星座": signs[zodiac_sign],
            "宮位": f"第 {house} 宮",
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



