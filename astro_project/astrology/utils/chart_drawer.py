# astrology/utils/chart_drawer.py

import matplotlib.pyplot as plt
import io
import base64

def draw_chart(planet_positions):
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'projection': 'polar'})
    ax.set_theta_direction(-1)  # 逆時針
    ax.set_theta_zero_location('E')  # 東方為0度

    # 畫出12宮線
    for i in range(12):
        angle = i * 30 * (3.14159 / 180)
        ax.plot([angle, angle], [0, 1], color='gray', linewidth=0.8)

    # 畫星體落點
    for planet in planet_positions:
        angle = planet.degree * (3.14159 / 180)
        ax.plot(angle, 0.9, 'o', label=planet.planet_name)

    ax.set_yticklabels([])
    ax.set_xticks([])

    # 存成 base64 image 字串
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig)
    return image_base64
