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
