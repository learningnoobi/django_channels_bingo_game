from django.http import JsonResponse
from django.shortcuts import render
from .models import BingoRoom
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import re
# Create your views here.

def CreateRoomView(request):
    return render(request,'bingo/create_room.html')

def bingoView(request,room_name):
    if not re.match(r'^[\w-]*$', room_name):
        return render(request,'bingo/error.html')
    return render(request,'bingo/bingo.html')

@csrf_exempt
def roomExist(request,room_name):
    print(room_name)
    
    return JsonResponse({
        "room_exist":BingoRoom.objects.filter(room_name=room_name).exists()
    })