import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, VerifyEmailCodeSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from .models import EmailVerificationCode
from django.utils import timezone
from datetime import timedelta

class RegisterAPIView(APIView):
    def post(self, request):
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "註冊成功"}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_info(request):
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
    })

@api_view(['POST'])
def request_verification_code(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': '請提供 email'}, status=status.HTTP_400_BAD_REQUEST)

    code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

    EmailVerificationCode.objects.create(email=email, code=code)

    print(f"[開發用] 寄送驗證碼給 {email}：{code}")

    return Response({'message': '驗證碼已發送'}, status=status.HTTP_200_OK)

class VerifyEmailCodeAPIView(APIView):
    def post(self, request):
        serializer = VerifyEmailCodeSerializer(data=request.data)
        if serializer.is_valid():
            record = serializer.validated_data['record']
            record.is_verified = True
            record.save()
            return Response({"message": "驗證成功"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)