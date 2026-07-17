import pytest
from io import BytesIO
from PIL import Image
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import ProfilePhoto

User = get_user_model()


def _make_user(email, nickname):
    user = User.objects.create_user(email=email, password="test123456")
    profile = user.profile
    profile.nickname = nickname
    profile.save()
    return user


def _fake_image(name="p.png", size=(200, 200)):
    buf = BytesIO()
    Image.new("RGB", size, (120, 80, 200)).save(buf, format="PNG")
    buf.seek(0)
    buf.name = name
    return buf


def _auth(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_upload_and_list_photos():
    user = _make_user("photo1@test.com", "照片一號")
    client = _auth(user)

    resp = client.post("/api/v1/user/photos/", {"photo": _fake_image()}, format="multipart")
    assert resp.status_code == 201
    assert resp.data["url"]

    resp2 = client.get("/api/v1/user/photos/")
    assert resp2.status_code == 200
    assert len(resp2.data) == 1

    # 個人資料的 photo（頭像）= 第一張
    profile_resp = client.get("/api/v1/user/profile/")
    assert profile_resp.data["photo"] == resp.data["url"]
    assert len(profile_resp.data["photos"]) == 1


@pytest.mark.django_db
def test_photo_limit_five():
    user = _make_user("photo2@test.com", "照片二號")
    client = _auth(user)
    for i in range(5):
        r = client.post("/api/v1/user/photos/", {"photo": _fake_image(f"p{i}.png")}, format="multipart")
        assert r.status_code == 201
    r6 = client.post("/api/v1/user/photos/", {"photo": _fake_image("p6.png")}, format="multipart")
    assert r6.status_code == 400


@pytest.mark.django_db
def test_delete_photo_only_own():
    owner = _make_user("photo3@test.com", "照片三號")
    other = _make_user("photo4@test.com", "照片四號")
    client = _auth(owner)
    resp = client.post("/api/v1/user/photos/", {"photo": _fake_image()}, format="multipart")
    photo_id = resp.data["id"]

    # 別人不能刪
    resp_other = _auth(other).delete(f"/api/v1/user/photos/{photo_id}/")
    assert resp_other.status_code == 404

    resp_del = client.delete(f"/api/v1/user/photos/{photo_id}/")
    assert resp_del.status_code == 204
    assert not ProfilePhoto.objects.filter(id=photo_id).exists()
