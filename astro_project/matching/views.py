from django.shortcuts import render
from matching.service.matching_logic import get_matching_candidates
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from accounts.models import UserProfile
from matching.models import MatchAction
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from chat.models import ChatRoom 



@require_POST
@login_required
def send_match_action(request):
    from_user = request.user.profile
    to_user_id = request.POST.get('to_user_id')
    action = request.POST.get('action')  # like 或 dislike

    # 確保欄位都有填
    if not to_user_id or action not in ['like', 'dislike']:
        return JsonResponse({'status': 'error', 'message': '資料不完整'}, status=400)

    try:
        to_user = UserProfile.objects.get(id=to_user_id)
    except UserProfile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '找不到使用者'}, status=404)

    # 如果已經存在一筆記錄就不要重複新增
    obj, created = MatchAction.objects.get_or_create(
        from_user=from_user,
        to_user=to_user,
        defaults={'action': action},
    )

    if not created:
        return JsonResponse({'status': 'error', 'message': '已經操作過'}, status=400)

    # 如果使用者按的是 "like"，而對方也已經按過 like，那就配對成功
    is_match = False
    if action == 'like':
        reverse_action = MatchAction.objects.filter(
            from_user=to_user,
            to_user=from_user,
            action='like'
        ).first()

        if reverse_action:
            is_match = True

            # 更新雙方 match 資訊（你可以視情況加上 is_match 欄位）
            obj.is_match = True
            reverse_action.is_match = True
            obj.save()
            reverse_action.save()

            # ✅ 建立聊天室（避免重複）
            existing_chat = ChatRoom.objects.filter(
                user1=from_user, user2=to_user
            ).exists() or ChatRoom.objects.filter(
                user1=to_user, user2=from_user
            ).exists()

            if not existing_chat:
                ChatRoom.objects.create(user1=from_user, user2=to_user)

    return JsonResponse({'status': 'ok', 'match': is_match})

@login_required
def show_match_candidates(request):
    candidates = get_matching_candidates(request.user)
    return render(request, 'matching/candidate_list.html', {'candidates': candidates})
