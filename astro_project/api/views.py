import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, VerifyEmailCodeSerializer, UserBirthInfoCreateUpdateSerializer, UserProfileSerializer, PlanetPositionSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from .models import EmailVerificationCode
from django.utils import timezone
from datetime import timedelta
from accounts.models import UserProfile
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from users.models import UserBirthInfo
from users.utils import get_lat_lng_by_city
from astrology.service.chart_service import generate_chart_and_save
from astrology.models import PlanetPosition
from matching.service.matching_logic import get_matching_candidates
from matching.models import MatchScore


#註冊
class RegisterAPIView(APIView):
    def post(self, request):
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "註冊成功"}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#email請求
class RequestEmailVerificationCodeView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': '請提供 email'}, status=400)
        
        recent_code = EmailVerificationCode.objects.filter(
            email=email,
            created_at__gte=timezone.now() - timedelta(seconds=60)).first()

        if recent_code:
            seconds_passed = (timezone.now() - recent_code.created_at).seconds
            seconds_left = 60 - seconds_passed
            return Response(
                {'error': f'請勿重複請求，請於 {seconds_left} 秒後再試'}, 
                status=429
            )

        if EmailVerificationCode.objects.filter(email=email, is_verified=True).exists():
            return Response({'message': '此 Email 已完成驗證，無需再次驗證'}, status=200)
        
        EmailVerificationCode.objects.filter(email=email, is_verified=False).delete()

        code = f"{random.randint(100000, 999999)}"
        EmailVerificationCode.objects.create(email=email, code=code)

        print(f"寄送驗證碼到 {email}：{code}")
        return Response({'message': '驗證碼已發送'}, status=200)

#email驗證
class VerifyEmailCodeAPIView(APIView):
    def post(self, request):
        serializer = VerifyEmailCodeSerializer(data=request.data)
        if serializer.is_valid():
            record = serializer.validated_data['record']
            record.is_verified = True
            record.save()
            return Response({"message": "驗證成功"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        user = request.user
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return Response({"error": "尚未建立個人資料"}, status=404)

        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return Response({"error": "尚未建立個人資料"}, status=404)

        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
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
            birth_info = serializer.save()

            if not birth_info.birth_latitude or not birth_info.birth_longitude:
                lat, lng = get_lat_lng_by_city(birth_info.birth_location)
                if lat is None or lng is None:
                    return Response({"error": "無法辨識出生地，請重新選擇"}, status=400)
                birth_info.birth_latitude = lat
                birth_info.birth_longitude = lng

            try:
                generate_chart_and_save(request.user.profile, birth_info)
            except Exception as e:
                return Response({"error": f"產生星盤失敗：{str(e)}"}, status=500)

            return Response(serializer.data, status=201)
        
        return Response(serializer.errors, status=400)

    def patch(self, request):
        try:
            birth_info = request.user.profile.birth_info
        except UserBirthInfo.DoesNotExist:
            return Response({"detail": "尚未填寫出生資料"}, status=404)

        serializer = UserBirthInfoCreateUpdateSerializer(
            birth_info, data=request.data, partial=True, context={'request': request}
        )
        
        if serializer.is_valid():
            updated_birth_info = serializer.save()

            # 判斷是否有改動關鍵欄位（可選，也可以每次都重算）
            changed_fields = set(request.data.keys())
            if changed_fields & {'birth_year', 'birth_month', 'birth_day', 'birth_hour', 'birth_minute', 'birth_location'}:
                # 🔁 重新取得經緯度
                lat, lng = get_lat_lng_by_city(updated_birth_info.birth_location)
                if lat and lng:
                    updated_birth_info.birth_latitude = lat
                    updated_birth_info.birth_longitude = lng
                    updated_birth_info.save()

                try:
                    generate_chart_and_save(request.user.profile, updated_birth_info)
                except Exception as e:
                    return Response({"error": f"星盤更新失敗：{str(e)}"}, status=500)

            return Response(serializer.data)
        
        return Response(serializer.errors, status=400)
    
class NatalChartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_profile = request.user.profile
        chart = PlanetPosition.objects.filter(user_profile=user_profile).order_by('planet_name')
        serializer = PlanetPositionSerializer(chart, many=True)
        return Response(serializer.data)
    
class MatchCandidatesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        candidates = get_matching_candidates(user, top_n=10)

        data = []
        for item in candidates:
            profile_data = UserProfileSerializer(item['userprofile']).data
            profile_data['match_score'] = item['score']
            data.append(profile_data)

        return Response(data)
    
