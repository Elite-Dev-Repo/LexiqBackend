from django.contrib import admin
from .models import Room, RoomMember
# Register your models here.


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('code', 'host', 'status', 'question_deck', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('code', 'host__username')
    ordering = ('-created_at',)

@admin.register(RoomMember)
class RoomMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'score', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'room__code')
    ordering = ('-created_at',)
