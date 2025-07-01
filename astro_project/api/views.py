import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, VerifyEmailCodeSerializer, UserBirthInfoCreateUpdateSerializer, UserProfileSerializer, PlanetPositionSerializer, SimpleUserProfileSerializer, MessageSerializer
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
from matching.models import MatchScore, MatchAction
from chat.models import ChatRoom
from django.db.models import Q
from chat.models import Message

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
        birth_info = getattr(request.user.profile, 'birth_info', None)
        if not birth_info:
            return Response({"detail": "尚未填寫出生資料"}, status=404)

        serializer = UserBirthInfoCreateUpdateSerializer(birth_info)
        return Response(serializer.data)

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

            changed_fields = set(request.data.keys())
            if changed_fields & {'birth_year', 'birth_month', 'birth_day', 'birth_hour', 'birth_minute', 'birth_location'}:
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
        serializer = PlanetPositionSerializer(
            chart, many=True)
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
    
class MatchActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from_user = request.user.profile
        to_user_id = request.data.get("to_user_id")
        action = request.data.get("action")
        
        if action not in ['like', 'dislike']:
            return Response({"detail": "無效的行為"}, status=400)

        try:
            to_user = UserProfile.objects.get(user__id=to_user_id)
        except UserProfile.DoesNotExist:
            return Response({"detail": "目標用戶不存在"}, status=404)

        if str(from_user.user.id) == str(to_user_id):
            return Response({"detail": "不能對自己進行 like/dislike。"}, status=400)
        
        match_action, created = MatchAction.objects.get_or_create(
            from_user=from_user,
            to_user=to_user,
            defaults={"action": action}
        )

        if not created:
            return Response({"detail": "你已對此用戶操作過"}, status=400)

        is_matched = MatchAction.objects.filter(
            from_user=to_user,
            to_user=from_user,
            action='like'
        ).exists()

        if is_matched:
            # 決定 user1 與 user2 的順序（用 id 決定，避免建立兩次聊天室）
            user1 = min(from_user, to_user, key=lambda u: u.user.id)
            user2 = max(from_user, to_user, key=lambda u: u.user.id)

            ChatRoom.objects.get_or_create(
                user1=user1.user,
                user2=user2.user
            )

        return Response({
            "detail": "操作成功",
            "matched": is_matched 
        }, status=201)

class ChatRoomListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        rooms = ChatRoom.objects.filter(
            Q(user1=user) | Q(user2=user)
        ).prefetch_related('messages', 'user1__profile', 'user2__profile')
        data = []

        for room in rooms:
            other_user = room.user2 if room.user1 == user else room.user1
            data.append({
                "room_id": room.id,
                "matched_user": SimpleUserProfileSerializer(other_user).data,
                "last_message_time": room.messages.last().timestamp if room.messages.exists() else None
            })

        return Response(data)
    
class ChatRoomMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_id):
        user = request.user
        try:
            room = ChatRoom.objects.get(id=room_id)
        except ChatRoom.DoesNotExist:
            return Response({"detail": "聊天室不存在"}, status=404)

        # 確保這個人是這個聊天室成員
        if user != room.user1 and user != room.user2:
            return Response({"detail": "你無權查看這個聊天室"}, status=403)

        messages = room.messages.order_by('timestamp')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request, room_id):
        user = request.user
        content = request.data.get("content")
        if not content:
            return Response({"detail": "訊息不得為空"}, status=400)

        try:
            room = ChatRoom.objects.get(id=room_id)
        except ChatRoom.DoesNotExist:
            return Response({"detail": "聊天室不存在"}, status=404)

        if user != room.user1 and user != room.user2:
            return Response({"detail": "你無權傳送訊息"}, status=403)

        message = Message.objects.create(
            room=room,
            sender=user,
            content=content
        )
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)