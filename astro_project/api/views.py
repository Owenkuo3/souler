import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, VerifyEmailCodeSerializer, UserBirthInfoCreateUpdateSerializer, UserProfileSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from .models import EmailVerificationCode
from django.utils import timezone
from datetime import timedelta
from accounts.models import UserProfile
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser



class RegisterAPIView(APIView):
    def post(self, request):
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "註冊成功"}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RequestEmailVerificationCodeView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': '請提供 email'}, status=400)

        if EmailVerificationCode.objects.filter(email=email, is_verified=True).exists():
            return Response({'message': '此 Email 已完成驗證，無需再次驗證'}, status=200)

        EmailVerificationCode.objects.filter(email=email, is_verified=False).delete()

        code = f"{random.randint(100000, 999999)}"
        EmailVerificationCode.objects.create(email=email, code=code)

        print(f"寄送驗證碼到 {email}：{code}")
        return Response({'message': '驗證碼已發送'}, status=200)

class VerifyEmailCodeAPIView(APIView):
    def post(self, request):
        serializer = VerifyEmailCodeSerializer(data=request.data)
        if serializer.is_valid():
            record = serializer.validated_data['record']
            record.is_verified = True
            record.save()
            return Response({"message": "驗證成功"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CurrentUserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return Response({"error": "使用者尚未建立個人資料"}, status=404)

        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    
class UpdateUserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def patch(self, request):
        user = request.user
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return Response({"error": "找不到使用者的個人資料"}, status=404)

        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserBirthInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            birth_info = request.user.profile.birth_info
            serializer = UserBirthInfoCreateUpdateSerializer(birth_info)
            return Response(serializer.data)
        except UserBirthInfo.DoesNotExist:
            return Response({"detail": "尚未填寫出生資料"}, status=404)

    def post(self, request):
        serializer = UserBirthInfoCreateUpdateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def patch(self, request):
        try:
            birth_info = request.user.profile.birth_info
        except UserBirthInfo.DoesNotExist:
            return Response({"detail": "尚未填寫出生資料"}, status=404)

        serializer = UserBirthInfoCreateUpdateSerializer(birth_info, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)