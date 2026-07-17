import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from api.models import PushSubscription, VapidKeyPair

User = get_user_model()


def _make_user(email, nickname):
    user = User.objects.create_user(email=email, password="test123456")
    profile = user.profile
    profile.nickname = nickname
    profile.save()
    return user


def _auth(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_push_key_autogenerates_and_persists():
    user = _make_user("push1@test.com", "推播一號")
    resp = _auth(user).get("/api/v1/push/key/")
    assert resp.status_code == 200
    key1 = resp.data["public_key"]
    assert len(key1) > 40
    assert VapidKeyPair.objects.count() == 1

    # 第二次拿到同一把（不重複生成）
    resp2 = _auth(user).get("/api/v1/push/key/")
    assert resp2.data["public_key"] == key1
    assert VapidKeyPair.objects.count() == 1


@pytest.mark.django_db
def test_subscribe_and_resubscribe():
    user = _make_user("push2@test.com", "推播二號")
    client = _auth(user)
    sub = {
        "endpoint": "https://push.example.com/abc",
        "keys": {"p256dh": "pkey", "auth": "akey"},
    }
    resp = client.post("/api/v1/push/subscribe/", sub, format="json")
    assert resp.status_code == 201
    assert PushSubscription.objects.filter(user=user).count() == 1

    # 同一個 endpoint 換帳號登入時，歸屬轉移而不是報錯
    user2 = _make_user("push3@test.com", "推播三號")
    resp2 = _auth(user2).post("/api/v1/push/subscribe/", sub, format="json")
    assert resp2.status_code == 201
    assert PushSubscription.objects.get(endpoint=sub["endpoint"]).user == user2


@pytest.mark.django_db
def test_send_push_removes_dead_subscription(monkeypatch):
    from api import push_utils
    from pywebpush import WebPushException

    user = _make_user("push4@test.com", "推播四號")
    PushSubscription.objects.create(
        user=user, endpoint="https://push.example.com/dead", p256dh="k", auth="a"
    )

    class FakeResp:
        status_code = 410

    def fake_webpush(**kwargs):
        raise WebPushException("gone", response=FakeResp())

    monkeypatch.setattr("pywebpush.webpush", fake_webpush)
    push_utils._send_to_user_sync(user.id, {"title": "t", "body": "b", "url": "/"})
    assert PushSubscription.objects.filter(user=user).count() == 0
