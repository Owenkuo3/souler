from rest_framework import serializers
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'id',
            'nickname',
            'gender',
            'avatar',
            'bio',
            'birth_date',
            'birth_time',
            'birth_place',
        ]