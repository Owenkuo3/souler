import pytest
from rest_framework.test import APIClient
from api.models import EmailVerificationCode
from django.utils import timezone

#註冊成功
@pytest.mark.django_db
def test_register_success():
    EmailVerificationCode.objects.create(
        email="test123@example.com",
        code="123456",
        is_verified=True,
        created_at=timezone.now()
    )

    client = APIClient()
    url = "/api/v1/register/"
    data = {
        "email": "test123@example.com",
        "password": "StrongPass123!",
        "password2": "StrongPass123!",
        "nickname": "小星星"
    }

    response = client.post(url, data)
    print("回應訊息：", response.data)
    assert response.status_code == 201


#未驗證email    
@pytest.mark.django_db
def test_register_with_unverified_email_should_fail():
    EmailVerificationCode.objects.create(
        email="unverified@example.com",
        code="999999",
        is_verified=False,
        created_at=timezone.now()
    )

    client = APIClient()
    url = "/api/v1/register/"
    data = {
        "email": "unverified@example.com",
        "password": "StrongPass123!",
        "password2": "StrongPass123!",
        "nickname": "未驗證星人"
    }

    response = client.post(url, data)
    print("請先完成 Email 驗證", response.data)

    assert response.status_code == 400

    assert "email" in response.data

@pytest.mark.django_db
def test_request_email_code_success():
    client = APIClient()
    url = "/api/v1/request-email-code/"
    data = {"email": "test@example.com"}

    response = client.post(url, data)
    print("正常請求驗證碼回應:", response.data)

    assert response.status_code == 200
    assert "message" in response.data

@pytest.mark.django_db
def test_request_email_code_too_soon():
    client = APIClient()
    url = "/api/v1/request-email-code/"
    email = "test@example.com"

    # 先創建一筆剛發送的驗證碼（60秒內）
    EmailVerificationCode.objects.create(
        email=email,
        code="123456",
        created_at=timezone.now()
    )

    data = {"email": email}
    response = client.post(url, data)
    print("重複請求驗證碼回應:", response.data)

    assert response.status_code == 429
    assert "error" in response.data

@pytest.mark.django_db
def test_request_email_code_no_email():
    client = APIClient()
    url = "/api/v1/request-email-code/"
    data = {}  # 沒有 email

    response = client.post(url, data)
    print("沒帶 email 請求驗證碼回應:", response.data)

    assert response.status_code == 400
    assert "error" in response.data