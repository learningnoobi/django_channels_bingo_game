from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .models import BingoRoom
from .validators import is_valid_room_name


def CreateRoomView(request):
    return render(request, "bingo/create_room.html")


def bingoView(request, room_name):
    if not is_valid_room_name(room_name):
        return render(request, "bingo/error.html", status=400)
    return render(request, "bingo/bingo.html")


@require_GET
def roomExist(request, room_name):
    return JsonResponse({"room_exist": BingoRoom.objects.filter(room_name=room_name).exists()})
