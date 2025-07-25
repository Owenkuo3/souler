from django.contrib import admin
from .models import ChatRoom,Message

# Register your models here.
admin.site.register(ChatRoom)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'sender', 'content', 'timestamp')  # 👈 把 timestamp 加進來
    list_filter = ('timestamp', 'sender')
    search_fields = ('content',)
