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
