from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ChatRoom

@login_required
def chat_room_list(request):
    rooms = ChatRoom.objects.filter(user1=request.user) | ChatRoom.objects.filter(user2=request.user)

    # 加上對方的 username
    room_infos = []
    for room in rooms:
        other_user = room.user2 if room.user1 == request.user else room.user1
        room_infos.append({
            'id': room.id,
            'other_username': other_user.username,
        })

    return render(request, 'chat/room_list.html', {'rooms': room_infos})
