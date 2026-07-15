# astrology/service/interpretation_service.py
"""AI 星盤解說生成：把使用者的星盤資料整理成 prompt，呼叫 Claude 生成繁體中文解說。"""
import os

import anthropic

from astrology.models import PlanetPosition

# 模型可用環境變數切換（預設用最高品質的 Opus——解說品質是這個功能的賣點）
AI_MODEL = os.environ.get('AI_MODEL', 'claude-opus-4-8')

SYSTEM_PROMPT = """你是一位溫暖、專業的占星師，在一個以星盤配對為核心的交友 app「Souler」中為使用者解讀本命星盤。

寫作要求：
- 使用繁體中文（台灣用語），語氣親切自然，像面對面聊天，不要條列式的冷冰冰報告
- 避免堆砌專業術語；提到相位或宮位時用一句話解釋它的意思
- 內容要「有命中感」：具體描述性格特質與行為傾向，避免放諸四海皆準的空話
- 因為是交友 app，「愛情與親密關係」的段落要寫得最深入
- 不要提及健康、壽命、災禍等敏感預測
- 總長度約 900～1200 字

輸出結構（用這些標題，每段之間空一行）：
【整體印象】用三四句話勾勒這個人的核心氣質
【太陽・月亮・上升】解讀人格三大支柱：外在表現、內在情感需求、給人的第一印象
【愛情與親密關係】根據金星、火星與相關宮位，深入描寫愛情觀、心動的類型、相處模式與需要注意的盲點
【天賦與人生方向】根據其他行星與宮位配置，點出天賦與適合的發展方向
【給你的一句話】一句溫暖有力的總結"""


def _format_chart(user_profile):
    """把 PlanetPosition 資料整理成給模型看的文字。"""
    positions = PlanetPosition.objects.filter(user_profile=user_profile)
    if not positions.exists():
        return None

    lines = []
    for p in positions:
        deg = int(p.correct_degree)
        minute = int(round((p.correct_degree - deg) * 60))
        retro = '（逆行）' if p.is_retrograde else ''
        house = f'，第{p.house}宮' if p.house else ''
        lines.append(f'{p.planet_name}：{p.zodiac_sign}座 {deg}°{minute:02d}′{house}{retro}')
    return '\n'.join(lines)


SYNASTRY_SYSTEM_PROMPT = """你是一位溫暖、專業的占星師，在一個以星盤配對為核心的交友 app「Souler」中，為一對剛配對成功的使用者解讀他們的合盤（synastry）。

寫作要求：
- 使用繁體中文（台灣用語），語氣親切自然，像在跟這兩個人一起聊天；用「你們」稱呼這對組合
- 兩人都會看到同一份解說，所以描述要平衡，不要偏袒某一方；提到個人時用暱稱
- 避免堆砌專業術語；提到相位時用一句話解釋它在關係裡的意思
- 內容要「有命中感」：根據實際相位具體描述兩人互動的化學反應，避免空泛的場面話
- 摩擦點要誠實指出，但用建設性的方式收尾——這是幫他們開啟話題，不是勸退
- 不要提及健康、壽命、災禍等敏感預測；不要給出「你們一定會在一起/分開」的斷言
- 總長度約 800～1100 字

輸出結構（用這些標題，每段之間空一行）：
【你們的化學反應】用三四句話勾勒這對組合的整體氛圍與吸引力來源
【心動的訊號】根據金星、火星、月亮相關相位，描寫兩人之間的吸引力如何運作
【相處與溝通】根據水星、太陽、上升等相位，描寫日常互動、聊天的頻率與默契
【可能的小摩擦】誠實點出挑戰相位代表的磨合點，並給一個具體的相處建議
【給你們的開場白】建議一個根據合盤特質設計的聊天話題，讓他們現在就能用"""

# 相位英文名 → 中文（matched_aspects 存的是英文名）
_ASPECT_ZH = {
    'Conjunction': '合相', 'Sextile': '六分相', 'Square': '四分相',
    'Trine': '三分相', 'Opposition': '對分相',
    'Semi-Sextile': '半六分相', 'Semi-Square': '半四分相', 'Quincunx': '十二分之五相',
}


def generate_synastry_interpretation(profile_a, profile_b, matched_aspects, score):
    """呼叫 Claude 生成兩人合盤解說。回傳 (content, model_used)。"""
    chart_a = _format_chart(profile_a)
    chart_b = _format_chart(profile_b)
    if chart_a is None or chart_b is None:
        raise ValueError('雙方星盤資料不完整')

    # 相位依影響力排序，取前 20 條給模型（全列會太長且稀釋重點）
    aspects = sorted(matched_aspects or [], key=lambda x: abs(x.get('score', 0)), reverse=True)[:20]
    aspect_lines = [
        f"{profile_a.nickname}的{a['planet_a']} — {profile_b.nickname}的{a['planet_b']}："
        f"{_ASPECT_ZH.get(a['aspect'], a['aspect'])}（{'和諧' if a.get('base_score', 0) > 0 else '挑戰'}）"
        for a in aspects
    ]

    client = anthropic.Anthropic(timeout=90.0)
    response = client.messages.create(
        model=AI_MODEL,
        max_tokens=4096,
        thinking={'type': 'disabled'},
        system=SYNASTRY_SYSTEM_PROMPT,
        messages=[{
            'role': 'user',
            'content': (
                f'請解讀這對配對的合盤。\n\n'
                f'== {profile_a.nickname} 的本命盤 ==\n{chart_a}\n\n'
                f'== {profile_b.nickname} 的本命盤 ==\n{chart_b}\n\n'
                f'== 兩人之間的主要相位（依影響力排序）==\n' + '\n'.join(aspect_lines) + '\n\n'
                '直接輸出解說內容，不要有開場白或結尾的免責聲明。'
            ),
        }],
    )

    content = next((b.text for b in response.content if b.type == 'text'), '')
    if not content.strip():
        raise RuntimeError(f'模型未回傳內容（stop_reason={response.stop_reason}）')
    return content, AI_MODEL


def generate_interpretation(user_profile):
    """呼叫 Claude 生成星盤解說。回傳 (content, model_used)。

    呼叫端負責存檔與錯誤處理；沒有 ANTHROPIC_API_KEY 時 anthropic 會拋出認證錯誤。
    """
    chart_text = _format_chart(user_profile)
    if chart_text is None:
        raise ValueError('尚無星盤資料')

    client = anthropic.Anthropic(timeout=90.0)
    response = client.messages.create(
        model=AI_MODEL,
        max_tokens=4096,
        # 明確關閉思考模式：sonnet-5 預設開啟 adaptive thinking，會吃掉輸出預算；
        # 這是創意寫作不是推理任務，關閉後更快也更省
        thinking={'type': 'disabled'},
        system=SYSTEM_PROMPT,
        messages=[{
            'role': 'user',
            'content': (
                f'請解讀這張本命星盤（暱稱：{user_profile.nickname}）：\n\n{chart_text}\n\n'
                '直接輸出解說內容，不要有開場白或結尾的免責聲明。'
            ),
        }],
    )

    content = next((b.text for b in response.content if b.type == 'text'), '')
    if not content.strip():
        raise RuntimeError(f'模型未回傳內容（stop_reason={response.stop_reason}）')
    return content, AI_MODEL
