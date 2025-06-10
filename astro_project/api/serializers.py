from django.contrib.auth.models import User
from rest_framework import serializers
from .models import EmailVerificationCode
from django.utils import timezone
from datetime import timedelta


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def validate_email(self, email):
        now = timezone.now()
        try:
            code_record = EmailVerificationCode.objects.get(
                email=email,
                is_verified=True,
                created_at__gte=now - timedelta(minutes=30)  # 驗證成功有效 30 分鐘內
            )
        except EmailVerificationCode.DoesNotExist:
            raise serializers.ValidationError("請先完成 Email 驗證")

        return email


    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user
    

class VerifyEmailCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data['email']
        code = data['code']
        now = timezone.now()

        try:
            record = EmailVerificationCode.objects.get(
                email=email,
                code=code,
                is_verified=False,
            )
        except EmailVerificationCode.DoesNotExist:
            raise serializers.ValidationError("驗證碼錯誤")
        
        if record.is_expired():
            raise serializers.ValidationError("驗證碼已過期")
        
        data['record'] = record
        return data
