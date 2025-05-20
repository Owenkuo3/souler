from django.shortcuts import render
from matching.service.matching_logic import get_matching_candidates
from django.contrib.auth.decorators import login_required



@login_required
def show_match_candidates(request):
    candidates = get_matching_candidates(request.user)
    return render(request, 'matching/candidate_list.html', {'candidates': candidates})
