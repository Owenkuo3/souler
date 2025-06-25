from accounts.models import UserProfile
from django.utils import timezone
from datetime import timedelta
from matching.service.aspect_matching import calculate_match_score
from matching.models import MatchScore


def get_matching_candidates(user, top_n=10):
    my_profile = user.profile
    preferred_gender = my_profile.match_gender

    candidates = UserProfile.objects.exclude(user=user)
    if preferred_gender != 'A':
        candidates = candidates.filter(gender=preferred_gender)

    one_week_ago = timezone.now() - timedelta(days=7)
    candidates = candidates.filter(user__last_login__gte=one_week_ago)

    scored_candidates = []
    for candidate in candidates:
        match_score, created = MatchScore.objects.get_or_create(
            user_a=user,
            user_b=candidate.user,
            defaults={'score': 0} 
        )
        
        if created or match_score.score == 0:
            score, matched_aspects = calculate_match_score(my_profile, candidate)
            match_score.score = score
            match_score.matched_aspects = matched_aspects
            match_score.save()
        else:
            score = match_score.score

        MatchScore.objects.get_or_create(
            user_a=candidate.user,
            user_b=user,
            defaults={'score': 0}
        )

        scored_candidates.append({
            'userprofile': candidate,
            'score': score,
        })

    scored_candidates.sort(key=lambda x: x['score'], reverse=True)
    return scored_candidates[:top_n]