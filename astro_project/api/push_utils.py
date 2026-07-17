# api/push_utils.py
"""Web Push 推播（免第三方服務）。

- VAPID 金鑰第一次用到時自動生成並存 DB（跨部署持久）
- send_push_async 用背景執行緒寄送，不拖慢 API 回應
- 失效的訂閱（使用者移除 PWA / 撤銷權限，服務回 404/410）自動清掉
"""
import base64
import json
import logging
import threading

logger = logging.getLogger(__name__)


def get_vapid_keypair():
    """取得（或第一次自動生成）VAPID 金鑰。回傳 (private_pem, public_key_b64)。"""
    from api.models import VapidKeyPair

    row = VapidKeyPair.objects.first()
    if row:
        return row.private_pem, row.public_key_b64

    from cryptography.hazmat.primitives import serialization
    from py_vapid import Vapid

    v = Vapid()
    v.generate_keys()
    private_pem = v.private_pem().decode()
    raw_public = v.public_key.public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    public_b64 = base64.urlsafe_b64encode(raw_public).decode().rstrip('=')

    row = VapidKeyPair.objects.create(private_pem=private_pem, public_key_b64=public_b64)
    return row.private_pem, row.public_key_b64


def _send_to_user_sync(user_id, payload):
    from pywebpush import webpush, WebPushException
    from api.models import PushSubscription

    private_pem, _ = get_vapid_keypair()
    subs = PushSubscription.objects.filter(user_id=user_id)
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh, 'auth': sub.auth},
                },
                data=json.dumps(payload),
                vapid_private_key=private_pem,
                vapid_claims={'sub': 'mailto:a74109876@gmail.com'},
                timeout=10,
            )
        except WebPushException as e:
            status = getattr(getattr(e, 'response', None), 'status_code', None)
            if status in (404, 410):
                sub.delete()  # 訂閱已失效，清掉
            else:
                logger.warning('push failed (user=%s): %s', user_id, e)
        except Exception as e:
            logger.warning('push error (user=%s): %s', user_id, e)


def send_push_async(user, title, body, url='/'):
    """背景寄推播給某使用者的所有裝置。呼叫端不用等待、失敗不影響主流程。"""
    payload = {'title': title, 'body': body, 'url': url}
    threading.Thread(
        target=_send_to_user_sync, args=(user.id, payload), daemon=True
    ).start()
