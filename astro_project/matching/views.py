from django.shortcuts import render
from matching.service.matching_logic import get_matching_candidates
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from accounts.models import UserProfile
from matching.models import MatchAction
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from chat.models import ChatRoom 

@require_POST
@login_required
def send_match_action(request):
    from_user_profile = request.user.profile
    to_user_id = int(request.POST.get('to_user_id'))
    action = request.POST.get('action')

    if not to_user_id or action not in ['like', 'dislike']:
        return JsonResponse({'status': 'error', 'message': '資料不完整'}, status=400)

    try:
        to_user_profile = UserProfile.objects.get(id=to_user_id)
    except UserProfile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '找不到使用者'}, status=404)

    # 避免重複
    obj, created = MatchAction.objects.get_or_create(
        from_user=from_user_profile,
        to_user=to_user_profile,
        defaults={'action': action},
    )

    if not created:
        return JsonResponse({'status': 'error', 'message': '已經操作過'}, status=400)

    # 配對判斷
    is_match = False
    if action == 'like':
        reverse_action = MatchAction.objects.filter(
            from_user=to_user_profile,
            to_user=from_user_profile,
            action='like'
        ).first()

        if reverse_action:
            is_match = True
            obj.is_match = True
            reverse_action.is_match = True
            obj.save()
            reverse_action.save()

            user1 = from_user_profile.user
            user2 = to_user_profile.user

            chat_exists = ChatRoom.objects.filter(
                user1=user1, user2=user2
            ).exists() or ChatRoom.objects.filter(
                user1=user2, user2=user1
            ).exists()

            if not chat_exists:
                ChatRoom.objects.create(user1=user1, user2=user2)

    return JsonResponse({'status': 'ok', 'match': is_match})


@login_required
def show_match_candidates(request):
    candidates = get_matching_candidates(request.user)
    return render(request, 'matching/candidate_list.html', {'candidates': candidates})
