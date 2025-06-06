from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import ChatRoom, Message

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

@login_required
def chat_room_detail(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)

    if request.user not in [room.user1, room.user2]:
        return render(request, 'chat/not_allowed.html')

    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            Message.objects.create(
                room=room,
                sender=request.user,
                content=text
            )
            return redirect('chat_room_detail', room_id=room.id)

    return render(request, 'chat/room_detail.html', {
        'room': room,
        'other_user': room.user2 if room.user1 == request.user else room.user1
    })
