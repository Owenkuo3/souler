from django.conf import settings
from rest_framework import serializers
from .models import EmailVerificationCode
from django.utils import timezone
from datetime import timedelta
from accounts.models import CustomUser, UserProfile
from users.models import UserBirthInfo
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile



class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6)

    def validate(self, data):
        email = data['email']
        password = data['password']
        password2 = data['password2']

        if password != password2:
            raise serializers.ValidationError("兩次輸入的密碼不一致")

        if not EmailVerificationCode.objects.filter(email=email, is_verified=True).exists():
            raise serializers.ValidationError("請先完成 Email 驗證")

        if CustomUser.objects.filter(username=email).exists():
            raise serializers.ValidationError("此 Email 已經註冊過")

        return data

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        user = CustomUser.objects.create_user(username=email, email=email, password=password)
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

class UserBirthInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBirthInfo
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
    birth_info = UserBirthInfoSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['nickname', 'bio', 'gender', 'match_gender', 'preferred_age_min', 'preferred_age_max', 'photo', 'birth_info']

        def validate_photo(self, image):
            img = Image.open(image)

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            max_size = (1024, 1024)
            img.thumbnail(max_size)

            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=70)

            new_image = ContentFile(buffer.getvalue())
            new_image.name = f"{image.name.split('.')[0]}.jpg"

            return new_image
        
class UserBirthInfoCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBirthInfo
        exclude = ['id']
        extra_kwargs = {
            'user_profile': {'read_only': True}
        }

    def create(self, validated_data):
        user = self.context['request'].user
        user_profile = user.profile
        return UserBirthInfo.objects.create(user_profile=user_profile, **validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance