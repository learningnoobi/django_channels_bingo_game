from django.shortcuts import render
from .models import BingoRoom,TrackPlayers
# Create your views here.

def CreateRoomView(request):
    return render(request,'bingo/create_room.html')

def bingoView(request,room_name):
    return render(request,'bingo/bingo.html')
