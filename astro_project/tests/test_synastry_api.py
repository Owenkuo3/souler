import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from accounts.models import UserProfile
from astrology.models import PlanetPosition
from chat.models import ChatRoom
from matching.models import MatchScore

User = get_user_model()


def _make_user(email, nickname, degrees):
    """建一個帶星盤的使用者；degrees 是 {行星名: 黃道度數}。"""
    user = User.objects.create_user(email=email, password="test123456")
    # signal 會自動建 profile，拿回來改暱稱即可
    profile = user.profile
    profile.nickname = nickname
    profile.gender = 'M'
    profile.save()
    for name, deg in degrees.items():
        PlanetPosition.objects.create(
            user_profile=profile,
            planet_name=name,
            zodiac_sign='牡羊',
            degree=deg,
            correct_degree=deg % 30,
            house=1,
        )
    return user


@pytest.fixture
def matched_pair(db):
    # 太陽合相（0°/2°）→ 一定有相位可談
    user_a = _make_user("syn_a@test.com", "小合", {"太陽": 0.0, "月亮": 90.0, "金星": 10.0})
    user_b = _make_user("syn_b@test.com", "小盤", {"太陽": 2.0, "月亮": 150.0, "金星": 190.0})
    u1, u2 = sorted([user_a, user_b], key=lambda u: u.id)
    room = ChatRoom.objects.create(user1=u1, user2=u2)
    return user_a, user_b, room


def _auth(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_synastry_get_before_generation_returns_404(matched_pair):
    user_a, _, room = matched_pair
    resp = _auth(user_a).get(f"/api/v1/chatrooms/{room.id}/synastry/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_synastry_forbidden_for_outsider(matched_pair):
    _, _, room = matched_pair
    outsider = _make_user("syn_c@test.com", "路人", {"太陽": 30.0})
    resp = _auth(outsider).post(f"/api/v1/chatrooms/{room.id}/synastry/")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_synastry_generate_records_unlock_and_caches(matched_pair, monkeypatch):
    user_a, user_b, room = matched_pair
    calls = []

    def fake_generate(pa, pb, aspects, score):
        calls.append((pa.nickname, pb.nickname))
        assert aspects, "應該先補算 matched_aspects 再生成"
        return "這是合盤解說內容", "claude-test"

    monkeypatch.setattr(
        "astrology.service.interpretation_service.generate_synastry_interpretation",
        fake_generate,
    )

    resp = _auth(user_a).post(f"/api/v1/chatrooms/{room.id}/synastry/")
    assert resp.status_code == 201
    assert resp.data["content"] == "這是合盤解說內容"

    ms = MatchScore.objects.get(user_a=room.user1, user_b=room.user2)
    assert ms.is_ai_unlocked and ms.ai_unlocked_at is not None
    assert ms.ai_generated_at is not None
    assert ms.ai_model_used == "claude-test"
    assert ms.matched_aspects  # 空列被補算

    # 另一方 POST 直接吃快取，不再生成
    resp2 = _auth(user_b).post(f"/api/v1/chatrooms/{room.id}/synastry/")
    assert resp2.status_code == 200
    assert resp2.data["content"] == "這是合盤解說內容"
    assert len(calls) == 1

    # GET 也拿得到
    resp3 = _auth(user_b).get(f"/api/v1/chatrooms/{room.id}/synastry/")
    assert resp3.status_code == 200


@pytest.mark.django_db
def test_synastry_daily_cap(matched_pair, monkeypatch):
    user_a, _, room = matched_pair
    monkeypatch.setenv("DAILY_INTERPRETATION_CAP", "0")
    resp = _auth(user_a).post(f"/api/v1/chatrooms/{room.id}/synastry/")
    assert resp.status_code == 429


@pytest.mark.django_db
def test_synastry_generation_failure_still_records_click(matched_pair, monkeypatch):
    user_a, _, room = matched_pair

    def boom(*args, **kwargs):
        raise RuntimeError("api down")

    monkeypatch.setattr(
        "astrology.service.interpretation_service.generate_synastry_interpretation",
        boom,
    )
    resp = _auth(user_a).post(f"/api/v1/chatrooms/{room.id}/synastry/")
    assert resp.status_code == 503

    ms = MatchScore.objects.get(user_a=room.user1, user_b=room.user2)
    assert ms.is_ai_unlocked  # 點擊數據要留下
    assert ms.ai_interpretation is None  # 可以再重試
