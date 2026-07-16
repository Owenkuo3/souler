import random
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, VerifyEmailCodeSerializer, UserBirthInfoCreateUpdateSerializer, UserProfileSerializer, PlanetPositionSerializer, SimpleUserProfileSerializer, MessageSerializer, MyTokenObtainPairSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from .models import EmailVerificationCode
from django.utils import timezone
from datetime import timedelta
from accounts.models import UserProfile
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from users.models import UserBirthInfo
from users.utils import get_lat_lng_by_city, city_name_mapping
from astrology.service.chart_service import generate_chart_and_save
from astrology.models import PlanetPosition
from matching.service.matching_logic import get_matching_candidates
from matching.models import MatchScore, MatchAction
from chat.models import ChatRoom
from django.db.models import Q
from chat.models import Message
from rest_framework_simplejwt.views import TokenObtainPairView

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

        try:
            from api.email_utils import send_verification_email
            send_verification_email(email, code)
        except Exception as e:
            # 錯誤類型放進回應，SMTP 出問題時才有線索（DEBUG 關閉時 log 看不到 traceback）
            return Response(
                {'error': f'驗證信寄送失敗，請稍後再試（{type(e).__name__}: {str(e)[:120]}）'},
                status=503,
            )
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

#更新userprofile資料
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
    
#更新user出生地/日期
class UserBirthInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        birth_info = getattr(request.user.profile, 'birth_info', None)
        if not birth_info:
            return Response({"detail": "尚未填寫出生資料"}, status=404)

        serializer = UserBirthInfoCreateUpdateSerializer(birth_info)
        return Response(serializer.data)

    def post(self, request):
        if getattr(request.user.profile, 'birth_info', None):
            return Response({"detail": "出生資料已存在，請改用 PATCH 更新"}, status=400)

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
        from datetime import timedelta
        from django.utils import timezone

        try:
            birth_info = request.user.profile.birth_info
        except UserBirthInfo.DoesNotExist:
            return Response({"detail": "尚未填寫出生資料"}, status=404)

        CHART_FIELDS = {'birth_year', 'birth_month', 'birth_day', 'birth_hour', 'birth_minute', 'birth_location'}
        changes_chart = bool(set(request.data.keys()) & CHART_FIELDS)

        # 修改限制：前 3 次免費，之後每 30 天限改一次
        if changes_chart and birth_info.chart_edit_count >= 3:
            if birth_info.last_chart_edit_at:
                elapsed = timezone.now() - birth_info.last_chart_edit_at
                if elapsed < timedelta(days=30):
                    days_left = 30 - elapsed.days
                    return Response(
                        {"detail": f"出生資料修改已達免費上限，還要等 {days_left} 天才能再次修改"},
                        status=403,
                    )

        serializer = UserBirthInfoCreateUpdateSerializer(
            birth_info, data=request.data, partial=True, context={'request': request}
        )

        if serializer.is_valid():
            updated_birth_info = serializer.save()

            changed_fields = set(request.data.keys())
            if changed_fields & CHART_FIELDS:
                lat, lng = get_lat_lng_by_city(updated_birth_info.birth_location)
                if lat is not None and lng is not None:
                    updated_birth_info.birth_latitude = lat
                    updated_birth_info.birth_longitude = lng
                    updated_birth_info.save()

                try:
                    generate_chart_and_save(request.user.profile, updated_birth_info)
                except Exception as e:
                    return Response({"error": f"星盤更新失敗：{str(e)}"}, status=500)

                updated_birth_info.chart_edit_count += 1
                updated_birth_info.last_chart_edit_at = timezone.now()
                updated_birth_info.save(update_fields=['chart_edit_count', 'last_chart_edit_at'])

            return Response(serializer.data)
        
        return Response(serializer.errors, status=400)

#支援的出生地城市清單（前端下拉選單用）
class CityListView(APIView):
    def get(self, request):
        return Response({"cities": list(city_name_mapping.keys())})

#星盤展示
class NatalChartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from users.utils import get_house_cusps

        user_profile = request.user.profile
        chart = PlanetPosition.objects.filter(user_profile=user_profile).order_by('planet_name')
        serializer = PlanetPositionSerializer(chart, many=True)

        # 宮頭度數即時計算（前端畫宮位分隔線用）
        cusps = []
        birth = getattr(user_profile, 'birth_info', None)
        if birth and birth.birth_latitude is not None and birth.birth_longitude is not None:
            cusps = get_house_cusps(
                birth.birth_year, birth.birth_month, birth.birth_day,
                birth.birth_hour, birth.birth_minute,
                float(birth.birth_latitude), float(birth.birth_longitude),
            )

        return Response({'planets': serializer.data, 'house_cusps': cusps})
    
#AI 星盤解說（免費）：GET 取得既有解說，POST 生成
def _daily_ai_cap_reached():
    """個人解說＋合盤解說共用同一個每日生成上限（DAILY_INTERPRETATION_CAP）。"""
    import os as _os
    from django.utils import timezone as _tz
    from astrology.models import ChartInterpretation

    daily_cap = int(_os.environ.get('DAILY_INTERPRETATION_CAP', '100'))
    today = _tz.now().date()
    today_count = (
        ChartInterpretation.objects.filter(created_at__date=today).count()
        + MatchScore.objects.filter(ai_generated_at__date=today).count()
    )
    return today_count >= daily_cap


class ChartInterpretationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from astrology.models import ChartInterpretation

        interp = getattr(request.user.profile, 'chart_interpretation', None)
        if not interp:
            return Response({"detail": "尚未生成解說"}, status=404)
        return Response({
            "content": interp.content,
            "created_at": interp.created_at,
        })

    def post(self, request):
        from astrology.models import ChartInterpretation
        from astrology.service.interpretation_service import generate_interpretation

        profile = request.user.profile

        # 已有快取直接回傳（星盤沒變就不重新生成）
        existing = getattr(profile, 'chart_interpretation', None)
        if existing:
            return Response({
                "content": existing.content,
                "created_at": existing.created_at,
            })

        if not PlanetPosition.objects.filter(user_profile=profile).exists():
            return Response({"detail": "請先填寫出生資料產生星盤"}, status=400)

        # 全域斷路器：每日生成上限，防止被批量假帳號惡意消耗 AI 額度
        if _daily_ai_cap_reached():
            return Response({"detail": "今日 AI 解說名額已滿，請明天再來"}, status=429)

        try:
            content, model_used = generate_interpretation(profile)
        except Exception as e:
            return Response({"detail": f"解說生成失敗，請稍後再試（{type(e).__name__}）"}, status=503)

        interp = ChartInterpretation.objects.create(
            user_profile=profile, content=content, model_used=model_used,
        )
        return Response({
            "content": interp.content,
            "created_at": interp.created_at,
        }, status=201)


class SynastryInterpretationView(APIView):
    """合盤 AI 解說：綁在配對成功的聊天室上，一對配對只生成一次，雙方共用快取。

    POST = 假門的「解鎖」點擊（限時免費階段點擊即生成）；
    is_ai_unlocked / ai_unlocked_at 記錄點擊，之後分析付費意願用。
    """
    permission_classes = [IsAuthenticated]

    def _get_room_and_score(self, request, room_id):
        try:
            room = ChatRoom.objects.get(id=room_id)
        except ChatRoom.DoesNotExist:
            return None, None, Response({"detail": "聊天室不存在"}, status=404)
        if request.user != room.user1 and request.user != room.user2:
            return None, None, Response({"detail": "你無權查看這個聊天室"}, status=403)

        # 標準列：跟 ChatRoom 一樣用 user1(小 id)/user2(大 id) 的順序，避免雙向兩列各存一份
        match_score, _ = MatchScore.objects.get_or_create(
            user_a=room.user1, user_b=room.user2, defaults={'score': 0},
        )
        return room, match_score, None

    def get(self, request, room_id):
        room, ms, err = self._get_room_and_score(request, room_id)
        if err:
            return err
        if not ms.ai_interpretation:
            return Response({"detail": "尚未生成合盤解說"}, status=404)
        return Response({
            "content": ms.ai_interpretation,
            "created_at": ms.ai_generated_at,
        })

    def post(self, request, room_id):
        from django.utils import timezone as _tz
        from astrology.service.interpretation_service import generate_synastry_interpretation
        from matching.service.aspect_matching import calculate_match_score

        room, ms, err = self._get_room_and_score(request, room_id)
        if err:
            return err

        # 已有快取直接回傳（另一方點過就直接看）
        if ms.ai_interpretation:
            return Response({
                "content": ms.ai_interpretation,
                "created_at": ms.ai_generated_at,
            })

        # 記錄假門點擊（就算後面生成失敗，點擊本身就是付費意願數據）
        if not ms.is_ai_unlocked:
            ms.is_ai_unlocked = True
            ms.ai_unlocked_at = _tz.now()
            ms.save(update_fields=['is_ai_unlocked', 'ai_unlocked_at'])

        profile_a = room.user1.profile
        profile_b = room.user2.profile
        if not PlanetPosition.objects.filter(user_profile=profile_a).exists() \
                or not PlanetPosition.objects.filter(user_profile=profile_b).exists():
            return Response({"detail": "雙方星盤資料不完整，無法生成合盤"}, status=400)

        # 標準列可能是反向補的空列（score=0 無相位），現算補上
        if not ms.matched_aspects:
            score, aspects = calculate_match_score(profile_a, profile_b)
            ms.score = score
            ms.matched_aspects = aspects
            ms.save(update_fields=['score', 'matched_aspects'])

        if _daily_ai_cap_reached():
            return Response({"detail": "今日 AI 解說名額已滿，請明天再來"}, status=429)

        try:
            content, model_used = generate_synastry_interpretation(
                profile_a, profile_b, ms.matched_aspects, ms.score,
            )
        except Exception as e:
            return Response({"detail": f"合盤生成失敗，請稍後再試（{type(e).__name__}）"}, status=503)

        ms.ai_interpretation = content
        ms.ai_model_used = model_used
        ms.ai_generated_at = _tz.now()
        ms.save(update_fields=['ai_interpretation', 'ai_model_used', 'ai_generated_at'])
        return Response({
            "content": ms.ai_interpretation,
            "created_at": ms.ai_generated_at,
        }, status=201)


#配對邏輯API
class MatchCandidatesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from datetime import date

        user = request.user
        candidates = get_matching_candidates(user, top_n=10)

        today = date.today()
        data = []
        for item in candidates:
            profile = item['userprofile']

            birth = getattr(profile, 'birth_info', None)
            age = None
            if birth:
                age = today.year - birth.birth_year - (
                    (today.month, today.day) < (birth.birth_month, birth.birth_day)
                )

            sun = PlanetPosition.objects.filter(
                user_profile=profile, planet_name='太陽'
            ).first()

            data.append({
                'user_id': profile.user.id,
                'nickname': profile.nickname,
                'bio': profile.bio,
                'photo': profile.photo.url if profile.photo else None,
                'age': age,
                'sun_sign': sun.zodiac_sign if sun else None,
                'match_score': item['score'],
            })

        return Response(data)

#配對動作
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

        room = None
        if is_matched:
            # 決定 user1 與 user2 的順序（用 id 決定，避免建立兩次聊天室）
            user1 = min(from_user, to_user, key=lambda u: u.user.id)
            user2 = max(from_user, to_user, key=lambda u: u.user.id)

            room, _ = ChatRoom.objects.get_or_create(
                user1=user1.user,
                user2=user2.user
            )

        return Response({
            "detail": "操作成功",
            "matched": is_matched,
            "room_id": room.id if room else None,
            "matched_nickname": to_user.nickname if is_matched else None,
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
            last_message = room.messages.last()
            unread = room.messages.filter(is_read=False).exclude(sender=user).count()
            data.append({
                "room_id": room.id,
                "matched_user": SimpleUserProfileSerializer(other_user.profile).data,
                "last_message": last_message.content if last_message else None,
                "last_message_time": last_message.timestamp if last_message else None,
                "unread_count": unread,
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

        # 廣播給聊天室雙方的 WebSocket（發送走 REST 保證不掉，接收走 WS 即時）
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{room.id}',
            {
                'type': 'chat_message',
                'id': message.id,
                'sender': user.id,
                'sender_nickname': user.profile.nickname,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
            },
        )

        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class ChatRoomReadView(APIView):
    """把聊天室內「對方傳來」的訊息全部標為已讀，並廣播已讀事件給對方。"""
    permission_classes = [IsAuthenticated]

    def post(self, request, room_id):
        user = request.user
        try:
            room = ChatRoom.objects.get(id=room_id)
        except ChatRoom.DoesNotExist:
            return Response({"detail": "聊天室不存在"}, status=404)

        if user != room.user1 and user != room.user2:
            return Response({"detail": "你無權操作這個聊天室"}, status=403)

        updated = (
            room.messages.filter(is_read=False)
            .exclude(sender=user)
            .update(is_read=True)
        )

        if updated:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{room.id}',
                {'type': 'read_event', 'reader': user.id},
            )

        return Response({"marked_read": updated})


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer