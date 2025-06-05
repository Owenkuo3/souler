from accounts.models import UserProfile
from django.utils import timezone
from datetime import timedelta
from matching.service.aspect_matching import calculate_match_score

def get_matching_candidates(user, top_n=10):
    my_profile = user.profile
    preferred_gender = my_profile.match_gender
    
    # 初步過濾
    candidates = UserProfile.objects.exclude(user=user)
    if preferred_gender != 'A':
        candidates = candidates.filter(gender=preferred_gender)

    one_week_ago = timezone.now() - timedelta(days=7)
    candidates = candidates.filter(user__last_login__gte=one_week_ago)

    # 計算配對分數
    scored_candidates = []
    for candidate in candidates:
        score, _ = calculate_match_score(my_profile, candidate)
        scored_candidates.append({
            'userprofile': candidate,
            'score': score
        })

    # 排序取前 N 名
    scored_candidates.sort(key=lambda x: x['score'], reverse=True)
    return scored_candidates[:top_n]

