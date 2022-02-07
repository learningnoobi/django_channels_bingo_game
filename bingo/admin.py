from django.contrib import admin
from.models import BingoRoom,TrackPlayers




class TrackPlayersAdmin(admin.TabularInline):
    model = TrackPlayers

class RoomAdmin(admin.ModelAdmin):
   inlines = [TrackPlayersAdmin,]

admin.site.register(BingoRoom,RoomAdmin)