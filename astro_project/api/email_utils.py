# api/email_utils.py
"""驗證信寄送。

Render 免費層封鎖對外 SMTP 埠（25/465/587），所以正式環境走 Brevo 的 HTTP API
（443 埠不受限）。沒設 BREVO_API_KEY 時退回 Django 的 email backend
（本機開發 = console backend，印在終端機）。
"""
import os

import httpx
from django.conf import settings
from django.core.mail import send_mail


def send_verification_email(email, code):
    """寄驗證碼。失敗時拋出例外，由呼叫端決定怎麼回應。"""
    subject = 'Souler 註冊驗證碼'
    body = f'你的驗證碼是：{code}（15 分鐘內有效）'

    api_key = os.environ.get('BREVO_API_KEY')
    if api_key:
        resp = httpx.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={'api-key': api_key},
            json={
                'sender': {'name': 'Souler', 'email': settings.DEFAULT_FROM_EMAIL},
                'to': [{'email': email}],
                'subject': subject,
                'textContent': body,
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        return

    send_mail(
        subject=subject,
        message=body,
        from_email=None,  # 使用 settings.DEFAULT_FROM_EMAIL
        recipient_list=[email],
        fail_silently=False,
    )
