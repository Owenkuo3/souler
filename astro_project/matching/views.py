from django.shortcuts import render
from matching.service.matching_logic import get_matching_candidates
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from accounts.models import UserProfile
from matching.models import Match
from django.contrib.auth.models import User

@login_required
def send_match_action(request, to_user_id, liked):
    from_user = request.user
    to_user = get_object_or_404(User, id=to_user_id)

    if from_user == to_user:
        messages.error(request, "你不能對自己按讚！")
        return redirect('candidate_list')  # 替換為你的配對頁面 URL 名稱

    # 建立或更新配對紀錄
    match, created = Match.objects.update_or_create(
        from_user=from_user,
        to_user=to_user,
        defaults={'liked': liked}
    )

    try:
        reverse_match = Match.objects.get(from_user=to_user, to_user=from_user)
        if reverse_match.liked and liked:
            # 雙方都喜歡，配對成功！
            match.matched = True
            match.save()
            reverse_match.matched = True
            reverse_match.save()
            messages.success(request, "配對成功！你們現在可以聊天了！")
    except Match.DoesNotExist:
        pass

    return redirect('candidate_list')

@login_required
def show_match_candidates(request):
    candidates = get_matching_candidates(request.user)
    return render(request, 'matching/candidate_list.html', {'candidates': candidates})
